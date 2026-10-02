# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Schmid Software Solutions (https://schmid-software.de)
"""The add-on's link to Durty Cloth Tool: connection, pairing, sign-in, texture streaming and model pushes.

``LinkController.poll`` runs on Blender's main thread from a ``bpy.app.timers`` timer and drives the dct_link
session; session callbacks run inside that call. Network calls to gta.clothing (sign-in, renewing it, sign-in
assertions, sign-out) run as dct_link tasks on worker threads that never touch Blender; the timer only checks
whether they finished.

Nothing in this module imports Blender. The Blender side passes in where to keep files, how to read an image
and how to export a model, so the flows can be tested against a fake Durty Cloth Tool without Blender.
"""

from __future__ import annotations

import pathlib
import shutil
import tempfile
import time
import traceback
from typing import Any, Callable, Dict, List, NamedTuple, Optional, Protocol

from . import bundle, settings
from .dct_link import auth, tokens
from .dct_link.session import (
    AUTHENTICATING,
    HELLO,
    IDLE,
    PAIRING,
    READY,
    SIGNING_IN,
    STOPPED,
    WAITING,
    LinkError,
    LinkSession,
    LiveSurface,
    PairingRequired,
    PluginInfo,
    Request,
    SignInPrompt,
)
from .pixels import Conversion, StreamBuffers, limit_rects


class Notice(NamedTuple):
    """A message for the panels. ``level`` is ``INFO``, ``WARNING`` or ``ERROR``."""

    level: str
    text: str


# --------------------------------------------------------------------------------------------------
# Sign-in shared by the session and the Sign In buttons
# --------------------------------------------------------------------------------------------------


class _Finished:
    """A task that is already done (the dct_link task shape: ``poll``, ``result``, ``cancel``)."""

    def __init__(self, value: Any = None, error: Optional[BaseException] = None) -> None:
        self._value, self._error = value, error

    def poll(self) -> bool:
        return True

    def result(self) -> Any:
        if self._error is not None:
            raise self._error
        return self._value

    def cancel(self) -> None:
        pass


class _RememberFlow:
    """Wraps a device sign-in task so the flow it returns becomes the shared one."""

    def __init__(self, task: Any, source: "TokenSource") -> None:
        self._task, self._source = task, source

    def poll(self) -> bool:
        done = self._task.poll()
        if done and self._source.flow is None:
            try:
                self._source.flow = self._task.result()
            except Exception:  # noqa: BLE001 - the error reaches whoever calls result()
                pass
        return done

    def result(self) -> Any:
        return self._task.result()

    def cancel(self) -> None:
        self._task.cancel()


class TokenSource:
    """The session's token source: :class:`dct_link.auth.LinkAuth` plus one shared device sign-in and Blender's
    "Allow Online Access" switch.

    For every connection the session asks for a sign-in assertion bound to DCT's challenge; access and refresh
    tokens never go to DCT. Without a sign-in the session starts a device sign-in (and asks DCT to approve it),
    and the Sign In button starts one too. Sharing the flow means there is only one code: the one the browser
    shows is the one DCT is asked to approve. The ``begin_*`` forms return tasks that run on dct_link's worker
    threads, so the Blender timer never waits for the network. With online access off nothing is sent.
    """

    def __init__(self, link_auth: auth.LinkAuth, online: Callable[[], bool],
                 device_name: Callable[[], Optional[str]] = lambda: None) -> None:
        self.auth = link_auth
        self.online = online
        self.device_name = device_name
        self.flow: Optional[auth.DeviceFlow] = None

    @property
    def signed_out_by_user(self) -> bool:
        return self.auth.signed_out_by_user

    def allow_sign_in(self) -> None:
        self.auth.allow_sign_in()

    def invalidate_access_token(self) -> None:
        self.auth.invalidate_access_token()

    def active_flow(self) -> Optional[auth.DeviceFlow]:
        flow = self.flow
        if flow is None or flow.cancelled or flow.access_token is not None:
            return None
        if flow.expires_at <= self.auth._clock():
            return None
        return flow

    def _offline(self) -> auth.AuthError:
        return auth.AuthError("offline", "online access is off")

    def begin_mint_assertion(self, nonce: str) -> Any:
        if not self.online():
            return _Finished(error=self._offline()) if self.auth.signed_in else _Finished(None)
        return self.auth.begin_mint_assertion(nonce)

    def mint_assertion(self, nonce: str) -> Optional[str]:  # the blocking form; the session prefers begin_*
        if not self.online():
            if self.auth.signed_in:
                raise self._offline()
            return None
        return self.auth.mint_assertion(nonce)

    def begin_device_sign_in(self) -> Any:
        if not self.online():
            return _Finished(error=self._offline())
        flow = self.active_flow()
        if flow is not None:
            return _Finished(flow)
        self.flow = None
        # The computer name is shown on the approval page; the preference may have changed since start-up.
        self.auth.info = self.auth.info._replace(device_name=self.device_name() or None)
        return _RememberFlow(self.auth.begin_device_sign_in(), self)

    def start_device_sign_in(self) -> auth.DeviceFlow:  # the blocking form; the session prefers begin_*
        if not self.online():
            raise self._offline()
        flow = self.active_flow()
        if flow is None:
            self.auth.info = self.auth.info._replace(device_name=self.device_name() or None)
            flow = self.flow = self.auth.start_device_sign_in()
        return flow

    def cancel(self) -> None:
        if self.flow is not None:
            self.flow.cancel()
        self.flow = None


# --------------------------------------------------------------------------------------------------
# Texture streaming
# --------------------------------------------------------------------------------------------------


class ImageSource(Protocol):
    """What the stream needs from the Blender image (see ``host.BlenderImageSource``)."""

    def problem(self) -> Optional[str]: ...  # why the image can no longer be streamed

    def is_dirty(self) -> bool: ...  # whether the image may differ from what was read before

    def stroke_active(self) -> bool: ...  # whether a paint stroke is in progress right now

    def strokes_known(self) -> bool: ...  # whether stroke_active can tell at all (False: wait for quiet moments)

    def read_into(self, buffer: Any) -> None: ...  # fills a float32 buffer in Blender's layout


class _PixelSource:
    """The pixel source handed to the session. It lets go of the buffers when the stream ends, so they are freed
    even while the session still holds the surface (until DCT confirms the close)."""

    def __init__(self, buffers: StreamBuffers) -> None:
        self.buffers: Optional[StreamBuffers] = buffers

    def __call__(self, x: int, y: int, w: int, h: int) -> bytes:
        buffers = self.buffers
        if buffers is None:
            raise ValueError("the live texture was stopped")
        return buffers.pixels(x, y, w, h)

    def release(self) -> None:
        buffers, self.buffers = self.buffers, None
        if buffers is not None:
            buffers.release()


class TextureStream:
    """Streams one Blender image into a live texture in DCT's preview.

    Captures never run during a paint stroke; the image is captured once the stroke ends. A capture reads the
    image in one step and then works through it a few tiles at a time, a few milliseconds per timer step.
    Without strokes the image is checked now and then (only while Blender marks it changed), less and less often
    while nothing changes.
    """

    STEP_BUDGET = 0.006
    AFTER_CHANGE = 0.5
    AFTER_CHANGE_UNSEEN = 1.5  # when strokes cannot be seen, captures keep further apart while the image changes
    IDLE_FIRST = 1.0
    IDLE_MAX = 30.0
    READ_SHARE = 20.0  # an idle check reads the image for at most one twentieth of the time
    #: Changed areas marked per timer step; more are merged so a busy image does not flood DCT with frames.
    RECTS_PER_STEP = 4

    def __init__(self, controller: "LinkController") -> None:
        self.controller = controller
        self.source: Optional[ImageSource] = None
        self.buffers: Optional[StreamBuffers] = None
        self._pixel_source: Optional[_PixelSource] = None
        self.surface: Optional[LiveSurface] = None
        self.opening: Optional[Request] = None
        self.target: Optional[str] = None
        self.document: Optional[str] = None
        self.warning: Optional[str] = None
        self.live_state: Optional[str] = None
        self.status: Optional[Notice] = None
        self.saving = False
        self.next_check = 0.0
        self.quiet_checks = 0
        self._first_capture = False
        self._stroke_seen = False
        self._changes = 0
        self._force = False

    @property
    def active(self) -> bool:
        return self.buffers is not None

    @property
    def is_open(self) -> bool:
        return self.surface is not None and not self.surface.closed

    def start(self, source: ImageSource, target: str, width: int, height: int,
              conversion: Conversion = Conversion(), *, document: Optional[str] = None,
              warning: Optional[str] = None) -> None:
        """Opens a live texture for ``target`` on the item focused in DCT. Raises ``ValueError`` with a message
        for the user when that is not possible now."""
        session = self.controller.ready_session()
        problem = settings.check_stream_size(width, height) or self.controller.feature_problem(settings.FEATURE_LIVE_TEXTURE)
        if problem:
            raise ValueError(problem)
        if target not in {t for t, _, _ in settings.TARGETS}:
            raise ValueError("Choose diffuse, normal or specular.")
        self.stop()
        buffers = StreamBuffers(width, height, source.read_into, conversion)
        pixel_source = _PixelSource(buffers)
        try:
            buffers.begin(full=True)  # converted over the next timer steps; the first frame waits for it
            request = session.open_live(target, width, height, document=document, pixel_source=pixel_source)
        except BaseException:
            pixel_source.release()
            raise
        self.source, self.buffers, self.target, self.document = source, buffers, target, document
        self._pixel_source = pixel_source
        self.warning = warning
        self.live_state = None
        self._first_capture = True
        self._stroke_seen = self._force = False
        self.quiet_checks = 0
        self.status = Notice("INFO", "Opening the live texture in Durty Cloth Tool")
        self.opening = request
        request.add_done_callback(self._on_opened)

    def _on_opened(self, request: Request) -> None:
        if request is not self.opening:
            if request.error is None:
                _close_quietly(request.result())  # a newer start or a stop replaced this one
            return
        self.opening = None
        if request.error is not None:
            self.status = Notice("ERROR", settings.describe_error(request.error.code, request.error.message))
            self._release()
            self.controller.touch()
            return
        surface = request.result()
        if surface.closed:  # DCT ended it, or the connection dropped, before this answer was handled
            self._release()
            self.status = Notice("WARNING", settings.describe_close_reason(surface.close_reason or "closed"))
            self.controller.touch()
            return
        self.surface = surface
        if not self._first_capture:
            try:
                surface.mark_dirty(None)
            except LinkError:
                pass  # closing already; on_live_closed reports it
        self._set_streaming_status()
        self.controller.touch()

    def _set_streaming_status(self) -> None:
        text = "Streaming" if not self._first_capture else "Reading the image"
        if self.warning:
            self.status = Notice("WARNING", f"{text}. {self.warning}")
        else:
            self.status = Notice("INFO", text)

    def tick(self, now: float) -> None:
        if self.buffers is None or self.source is None or self.saving:
            return
        if self.opening is None and not self.is_open:
            return
        problem = self.source.problem()
        if problem:
            self.stop()
            self.status = Notice("WARNING", problem)
            self.controller.touch()
            return
        if self.source.stroke_active():
            self._stroke_seen = True  # capture once the stroke ends, never during it
            return
        buffers = self.buffers
        if buffers.busy:
            rects = buffers.step(self.STEP_BUDGET)
            if self._first_capture:
                if not buffers.busy:
                    self._first_capture = False
                    if self.is_open and self.surface is not None:
                        self._mark_all()
                        self._set_streaming_status()
                        self.controller.touch()
                    self.next_check = now + self.AFTER_CHANGE
                return
            self._mark(rects)
            if not buffers.busy:
                self._capture_finished(now)
            return
        if not self.is_open:
            return
        due = self._force or self._stroke_seen or (now >= self.next_check and self.source.is_dirty())
        if not due:
            if now >= self.next_check:
                self.next_check = now + self.IDLE_FIRST  # unchanged since loading or saving
            return
        self._force = self._stroke_seen = False
        self._changes = 0
        buffers.begin()

    def _mark(self, rects: List[Any]) -> None:
        if self.surface is None or self.surface.closed or not rects:
            return
        try:
            for rect in limit_rects(rects, self.RECTS_PER_STEP):
                self.surface.mark_dirty(rect)
        except LinkError:
            return  # closing already; on_live_closed reports it
        self._changes += len(rects)

    def _mark_all(self) -> None:
        if self.surface is None or self.surface.closed:
            return
        try:
            self.surface.mark_dirty(None)
        except LinkError:
            pass  # closing already; on_live_closed reports it

    def _capture_finished(self, now: float) -> None:
        assert self.buffers is not None
        if self._changes:
            self.quiet_checks = 0
            known = getattr(self.source, "strokes_known", None)
            interval = self.AFTER_CHANGE if known is None or known() else self.AFTER_CHANGE_UNSEEN
        else:
            self.quiet_checks += 1
            interval = min(self.IDLE_MAX, self.IDLE_FIRST * 2 ** (self.quiet_checks - 1))
        self.next_check = now + max(interval, self.buffers.last_read_cost * self.READ_SHARE)

    def send_now(self) -> None:
        """Captures the image at the next timer step even when nothing looks changed."""
        self._force = True

    def _capture_now(self) -> None:
        """Finishes any capture and captures once more, all at once (before a save)."""
        assert self.buffers is not None
        rects = self.buffers.finish()
        if self._first_capture:
            self._first_capture = False
            self._mark_all()
        else:
            self._mark(rects)
        self._mark(self.buffers.check())

    def save(self, mode: str) -> Request:
        if not self.is_open or self.surface is None:
            raise ValueError("Start streaming first.")
        problem = self.controller.feature_problem(settings.FEATURE_SAVE)
        if problem:
            raise ValueError(problem)
        if mode == "newVariation" and self.target != "diffuse":
            raise ValueError("Only diffuse textures can be saved as a new variation.")
        if self.source is not None and self.source.problem() is None:
            self._capture_now()  # the save covers the newest pixels
        self.saving = True
        request = self.surface.save(mode)
        self.status = Notice("INFO", "Saving")
        request.add_done_callback(lambda r: self._on_saved(r, mode))
        return request

    def _on_saved(self, request: Request, mode: str) -> None:
        self.saving = False
        if request.error is not None:
            self.status = Notice("ERROR", settings.describe_error(request.error.code, request.error.message))
        else:
            result = request.result()
            if result.get("ok"):
                text = "Saved as a new texture variation" if mode == "newVariation" else "Saved to the cloth"
                self.status = Notice("INFO", text)
            else:
                self.status = Notice("ERROR", settings.describe_error(result.get("code")))
        self.controller.touch()

    def discard(self) -> None:
        """Drops the unsaved changes in DCT's preview (which ends the live texture)."""
        surface = self.surface
        if surface is not None and not surface.closed:
            try:
                surface.discard()
            except LinkError:
                pass  # the connection is gone; DCT drops unsaved previews by itself
        self.opening = None
        self._release()
        self.status = Notice("INFO", "Discarded the changes in Durty Cloth Tool")

    def stop(self) -> None:
        """Closes the live texture. One still opening is closed when DCT answers (see ``_on_opened``)."""
        was_active = self.active
        surface = self.surface
        self.opening = None
        if surface is not None:
            _close_quietly(surface)
        self._release()
        if was_active:
            self.status = Notice("INFO", "Stopped")

    def fail(self, text: str) -> None:
        self.stop()
        self.status = Notice("ERROR", text)

    def _release(self) -> None:
        if self._pixel_source is not None:
            self._pixel_source.release()  # frees the pixels now, not when DCT confirms the close
        self._pixel_source = None
        self.surface = None
        self.buffers = None
        self.source = None
        self.saving = False
        self.live_state = None
        self._force = self._stroke_seen = self._first_capture = False
        self.quiet_checks = 0

    def on_live_status(self, surface: LiveSurface, message: Dict[str, Any]) -> None:
        if surface is self.surface:
            self.live_state = message.get("state")
            self.controller.touch()

    def on_live_closed(self, surface: LiveSurface, reason: str) -> None:
        if surface is self.surface:
            self._release()
            saved = self.status is not None and self.status.text.startswith("Saved")
            if not (reason == "closed" and saved):  # keep "Saved ..." when DCT ends the live texture after a save
                self.status = Notice("INFO" if reason == "closed" else "WARNING", settings.describe_close_reason(reason))
            self.controller.touch()

    def on_live_error(self, surface: LiveSurface, error: LinkError) -> None:
        if surface is self.surface:
            self.status = Notice("ERROR", settings.describe_error(error.code, error.message))
            self.controller.touch()

    def on_disconnected(self) -> None:
        if self.active:
            self._release()
            self.opening = None
            self.status = Notice("WARNING", settings.describe_close_reason("disconnected"))


def _close_quietly(surface: LiveSurface) -> None:
    if surface.closed:
        return
    try:
        surface.close()
    except LinkError:
        pass  # disconnected or closing already: DCT ends the live texture by itself


# --------------------------------------------------------------------------------------------------
# Model pushes
# --------------------------------------------------------------------------------------------------


class ModelPush:
    """Pushes models exported by Sollumz to DCT's preview, then saves or discards them there."""

    def __init__(self, controller: "LinkController") -> None:
        self.controller = controller
        self.lease: Optional[str] = None
        self.revision: Optional[int] = None
        self.findings: List[Dict[str, Any]] = []
        self.root_name: Optional[str] = None
        self.pending: Optional[Request] = None
        self.busy: Optional[str] = None  # "saving" or "discarding"
        self.status: Optional[Notice] = None
        self.auto_push = False
        #: Whether Push Automatically is on right now; Blender reads the current scene's setting.
        self.auto_enabled: Callable[[], bool] = lambda: self.auto_push
        #: Automatic pushes stop after an export with warnings until the user pushes again.
        self.paused = False
        self.delay = settings.AUTO_PUSH_DELAY_DEFAULT
        self.due_at: Optional[float] = None
        self.on_auto_push: Optional[Callable[[], None]] = None
        #: Why an automatic push waits right now (Edit Mode, a running tool), for the panel.
        self.waiting: Optional[str] = None
        self._saved = False
        self._note: Optional[str] = None
        self._save_tries = 0
        self._save_retry_at: Optional[float] = None

    SAVE_RETRIES = 5
    SAVE_RETRY_DELAY = 1.0

    @property
    def pushing(self) -> bool:
        return self.pending is not None and not self.pending.done

    @property
    def save_blocker(self) -> Optional[str]:
        """Why Save cannot run now, or ``None``. Saving while a newer push is on its way would store the model
        DCT showed before it."""
        if self.lease is None:
            return "Push a model first."
        if self.busy == "saving":
            return "Saving already."
        if self.busy is not None:
            return "Wait until Durty Cloth Tool answered."
        if self.pushing:
            return "Wait until the newest push is shown in Durty Cloth Tool, then save."
        if self.due_at is not None:
            return "Your newest changes are about to be pushed; save once they are shown in Durty Cloth Tool."
        return None

    def push(self, export: Callable[[str], Any], root_name: Optional[str] = None, *, automatic: bool = False) -> Request:
        """Exports with ``export(folder)`` into a temporary folder, collects the files and pushes them. ``export``
        may return an object whose ``warnings`` says the exporter logged warnings.

        Raises ``ValueError`` (or :class:`bundle.BundleError`) with a message for the user.
        """
        session = self.controller.ready_session()
        problem = self.controller.feature_problem(settings.FEATURE_MODEL)
        if problem:
            raise ValueError(problem)
        folder = tempfile.mkdtemp(prefix="dct_link_")
        try:
            result = export(folder)
            model_bundle, collected = bundle.build_bundle(folder)
        finally:
            shutil.rmtree(folder, ignore_errors=True)
        self.root_name = root_name
        self._saved = False
        self._note = None
        self.waiting = None
        if getattr(result, "warnings", False):
            if automatic:
                self.paused = True
                self.due_at = None
                self._note = ("Sollumz reported warnings, so automatic pushing is paused. Check Sollumz's Info log, "
                              "then push again to resume.")
            else:
                self._note = "Sollumz reported warnings; its Info log has the details."
        if not automatic:
            self.paused = False
        request = session.push_model(model_bundle)
        self.pending = request
        self.status = Notice("INFO", f"Sending {collected.model.name} with {len(collected.textures)} textures")
        request.add_done_callback(self._on_pushed)
        self.controller.touch()
        return request

    def _on_pushed(self, request: Request) -> None:
        if request is self.pending:
            self.pending = None
        if request.error is not None:
            if request.error.code != "superseded":
                self.status = Notice("ERROR", settings.describe_error(request.error.code, request.error.message))
                self.controller.touch()
            return
        self._applied(request.result())

    def _applied(self, message: Dict[str, Any]) -> None:
        self.lease = message.get("lease")
        self.revision = message.get("revision")
        self.findings = list(message.get("findings") or [])
        text = "Previewing in Durty Cloth Tool. Save or discard it there or here."
        if self.findings:
            text += f" Durty Cloth Tool reported {len(self.findings)} findings."
        if self._note:
            text += " " + self._note
        self.status = Notice("WARNING" if self._note else "INFO", text)
        self.controller.touch()

    def on_applied(self, message: Dict[str, Any]) -> None:
        """``model.applied`` as an event (also after the request finished, which changes nothing)."""
        self._applied(message)

    def save(self) -> Request:
        session = self.controller.ready_session()
        blocker = self.save_blocker
        if blocker is not None:
            raise ValueError(blocker)
        self._save_tries = 0
        self.busy = "saving"
        self.status = Notice("INFO", "Saving the model in Durty Cloth Tool")
        return self._send_save(session)

    def _send_save(self, session: LinkSession) -> Request:
        request = session.save_model()
        request.add_done_callback(self._on_saved)
        return request

    def _retry_save(self) -> None:
        self._save_retry_at = None
        if self.busy != "saving":
            return
        try:
            self._send_save(self.controller.ready_session())
        except (LinkError, ValueError) as exc:
            self.busy = None
            code = exc.code if isinstance(exc, LinkError) else None
            self.status = Notice("ERROR", settings.describe_error(code, str(exc)) if code else str(exc))
        self.controller.touch()

    def _on_saved(self, request: Request) -> None:
        if self.busy != "saving":
            return  # disconnected or discarded meanwhile
        if (request.error is not None and request.error.code == "busy" and self.lease is not None
                and self._save_tries < self.SAVE_RETRIES):
            # DCT is still loading this model (or handling other requests); ask again shortly.
            self._save_tries += 1
            self._save_retry_at = time.monotonic() + self.SAVE_RETRY_DELAY
            self.status = Notice("INFO", "Durty Cloth Tool is still loading the model. Saving in a moment.")
            self.controller.touch()
            return
        self.busy = None
        if request.error is not None and request.error.code == "busy":
            self.status = Notice("WARNING", "Durty Cloth Tool is still busy with the model. Save again in a moment.")
        elif request.error is not None:
            self.status = Notice("ERROR", settings.describe_error(request.error.code, request.error.message))
        elif request.result().get("ok"):
            self._saved = True
            self.status = Notice("INFO", "Saved the model to the project")
        else:
            self.status = Notice("ERROR", settings.describe_error(request.result().get("code")))
        self.controller.touch()

    def discard(self) -> Request:
        session = self.controller.ready_session()
        if self.lease is None:
            raise ValueError("Push a model first.")
        self.busy = "discarding"
        self.due_at = None
        self._save_retry_at = None
        self._saved = False
        request = session.discard_model()
        request.add_done_callback(self._on_discarded)
        return request

    def _on_discarded(self, request: Request) -> None:
        self.busy = None
        if request.error is not None:
            self.status = Notice("ERROR", settings.describe_error(request.error.code, request.error.message))
        else:
            self._closed(request.result().get("reason"))
        self.controller.touch()

    def on_closed(self, message: Dict[str, Any]) -> None:
        if message.get("lease") == self.lease:
            self._closed(message.get("reason"))
            self.controller.touch()

    def _closed(self, reason: Optional[str]) -> None:
        self.lease = None
        self.revision = None
        self.findings = []
        self.due_at = None
        self.waiting = None
        self._save_retry_at = None
        if self.busy == "saving":
            self.busy = None
        if reason == "closed" and self._saved:
            return  # DCT ended the preview after the save; keep "Saved ..."
        text = "Discarded the model in Durty Cloth Tool" if reason == "closed" else settings.describe_close_reason(reason)
        self.status = Notice("INFO" if reason == "closed" else "WARNING", text)

    def on_disconnected(self) -> None:
        if self.lease is not None or self.pending is not None:
            self.status = Notice("WARNING", settings.describe_close_reason("disconnected"))
        self.lease = None
        self.revision = None
        self.pending = None
        self.busy = None
        self.due_at = None
        self.waiting = None
        self._save_retry_at = None

    # ---- automatic pushes ----------------------------------------------------------------------------

    def schedule(self, now: float) -> None:
        """Something in the pushed model changed: push again once it stays unchanged for ``delay`` seconds."""
        if self.paused or self.lease is None or self.busy is not None or not self.auto_enabled():
            return
        self.due_at = now + settings.clamp_auto_push_delay(self.delay)

    def postpone(self, now: float, reason: Optional[str] = None) -> None:
        """The push is due but cannot run yet; ``reason`` is shown in the panel until it runs."""
        if self.due_at is None:
            self.due_at = now + settings.clamp_auto_push_delay(self.delay)
        else:
            self.due_at = max(self.due_at, now + 0.5)
        if reason != self.waiting:
            self.waiting = reason
            self.controller.touch()

    def tick(self, now: float) -> None:
        if self._save_retry_at is not None and now >= self._save_retry_at:
            self._retry_save()
        if self.due_at is None or now < self.due_at:
            return
        if self.pushing or self.busy is not None:
            self.due_at = now + 0.25
            return
        self.due_at = None
        if self.waiting is not None:
            self.waiting = None
            self.controller.touch()
        if not self.paused and self.lease is not None and self.on_auto_push is not None and self.auto_enabled():
            self.on_auto_push()


# --------------------------------------------------------------------------------------------------
# The controller
# --------------------------------------------------------------------------------------------------

LOGOUT_PATH = "/link/api/auth/logout"


class _ObservedHttp:
    """gta.clothing's HTTP client, noting whether the sign-out request reached it. dct_link's sign-out forgets the
    session here either way and does not report whether the server was told."""

    def __init__(self, inner: Any) -> None:
        self._inner = inner
        self.logout_reached: Optional[bool] = None  # written on a worker thread, read once the task is done

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)

    def request(self, method: str, path: str, body: Any = None, **kwargs: Any) -> Any:
        if path != LOGOUT_PATH:
            return self._inner.request(method, path, body, **kwargs)
        try:
            response = self._inner.request(method, path, body, **kwargs)
        except auth.AuthError:
            self.logout_reached = False
            raise
        self.logout_reached = response[0] < 500
        return response


class LinkController:
    """Owns the dct_link session, the sign-in and the pairing for one Blender process."""

    def __init__(
        self,
        data_dir: Callable[[], pathlib.Path],
        host_version: str,
        *,
        online: Callable[[], bool] = lambda: True,
        device_name: Callable[[], Optional[str]] = lambda: None,
        display_name: Optional[str] = None,
        secret_store: Callable[[str, pathlib.Path, str], Any] = tokens.default_secret_store,
        open_url: Callable[[str], None] = lambda url: None,
    ) -> None:
        self._data_dir_fn = data_dir
        self._secret_store = secret_store
        self.host_version = host_version
        self.channel = settings.CHANNEL
        self.online = online
        self.device_name = device_name
        self.display_name = display_name
        self.open_url = open_url
        # Test seams: a fixed port keeps tests off the real link ports; the sign-in may use a loopback fake.
        self.port_override: Optional[int] = None
        self.auth_base_url: str = auth.BASE_URL

        self.session: Optional[LinkSession] = None
        self.link_auth: Optional[auth.LinkAuth] = None
        self.token_source: Optional[TokenSource] = None
        self.pairing_store: Optional[tokens.PairingStore] = None
        self.data_dir: Optional[pathlib.Path] = None

        self.want_connected = False
        self.state = IDLE
        self.dct_seen = False
        self.pairing_prompt = None
        self.pairing_not_started = False
        self.pairing_required: Optional[PairingRequired] = None
        self.signed_out = False
        self.sign_in_prompt: Optional[SignInPrompt] = None
        self.notice: Optional[Notice] = None
        self.incompatible: Optional[Dict[str, Any]] = None
        self.project: Optional[Dict[str, Any]] = None
        self.focused: Optional[Dict[str, Any]] = None
        self.user_name: Optional[str] = None
        self.paired: Optional[bool] = None
        self.changed = True
        self._sign_in_task: Any = None
        self._open_when_ready = False
        self._logout_task: Any = None
        self._http: Optional[_ObservedHttp] = None

        self.stream = TextureStream(self)
        self.model = ModelPush(self)

    # ---- set-up --------------------------------------------------------------------------------------

    def touch(self) -> None:
        """Marks the panels for a redraw."""
        self.changed = True

    def _ensure_setup(self) -> None:
        if self.link_auth is not None:
            return
        folder = self._data_dir_fn()
        folder.mkdir(parents=True, exist_ok=True)
        install_id = tokens.load_install_id(folder)
        token_store = tokens.TokenStore(self._secret_store("tokens", folder, install_id))
        self.pairing_store = tokens.PairingStore(self._secret_store("pairing", folder, install_id))
        client = auth.ClientInfo(settings.PLUGIN_KIND, settings.VERSION, self.host_version, self.channel, install_id,
                                 self.device_name() or None)
        self.link_auth = auth.LinkAuth(client, token_store, folder / "auth.lock", base_url=self.auth_base_url)
        self._http = _ObservedHttp(self.link_auth.http)
        self.link_auth.http = self._http
        self.token_source = TokenSource(self.link_auth, self.online, self.device_name)
        self.data_dir = folder
        self.refresh_account()

    def prepare(self) -> None:
        """Creates the add-on's folder and reads the stored sign-in and pairing (for the panels)."""
        self._ensure_setup()
        self.refresh_account()

    def refresh_account(self) -> None:
        """Re-reads who is signed in and whether this Blender is paired (both kept in the secret store)."""
        if self.link_auth is None or self.pairing_store is None:
            return
        user = self.link_auth.user
        self.user_name = user.get("name") if user else None
        if self.user_name is None and self.link_auth.signed_in:
            self.user_name = "your account"
        self.signed_out = self.link_auth.signed_out_by_user
        self.paired = self.pairing_store.load() is not None
        self.touch()

    def _session(self) -> LinkSession:
        if self.session is None:
            self._ensure_setup()
            assert self.pairing_store is not None and self.token_source is not None
            plugin = PluginInfo(settings.PLUGIN_KIND, settings.VERSION, self.channel, settings.HOST_NAME,
                                self.host_version, self.display_name)
            session = LinkSession(
                plugin,
                pairing_store=self.pairing_store,
                token_source=self.token_source,
                port=self.port_override,
                use_discovery_file=self.port_override is None,
            )
            for event, handler in (
                ("state", self._on_state),
                ("ready", self._on_ready),
                ("pairing", self._on_pairing),
                ("pairing-required", self._on_pairing_required),
                ("sign-in", self._on_sign_in),
                ("signed-out", self._on_signed_out),
                ("selection", self._on_selection),
                ("project", self._on_project),
                ("entitlement", lambda message: self.touch()),
                ("live-status", self.stream.on_live_status),
                ("live-closed", self.stream.on_live_closed),
                ("live-error", self.stream.on_live_error),
                ("model-applied", self.model.on_applied),
                ("model-closed", self.model.on_closed),
                ("incompatible", self._on_incompatible),
                ("error", self._on_error),
                ("disconnected", self._on_disconnected),
            ):
                session.on(event, handler)
            self.session = session
        return self.session

    # ---- connection ----------------------------------------------------------------------------------

    def connect(self) -> None:
        session = self._session()
        self.want_connected = True
        self.incompatible = None
        self.notice = None
        session.start()
        self.touch()

    def disconnect(self) -> None:
        self.want_connected = False
        self.stream.stop()
        if self.session is not None:
            self.session.stop()
        self.touch()

    def shutdown(self) -> None:
        """Stops everything (the add-on is being disabled): no socket is left open, no timer will poll again."""
        self.want_connected = False
        self.stream.stop()
        if self.session is not None:
            self.session.shutdown()
        if self.token_source is not None:
            self.token_source.cancel()
        for task in (self._sign_in_task, self._logout_task):
            if task is not None:
                task.cancel()
        self._sign_in_task = self._logout_task = None
        self.session = None
        self.state = IDLE

    @property
    def ready(self) -> bool:
        return self.session is not None and self.session.state == READY

    def ready_session(self) -> LinkSession:
        if not self.ready or self.session is None:
            raise ValueError("Connect to Durty Cloth Tool first.")
        return self.session

    def feature_problem(self, feature: str) -> Optional[str]:
        if self.session is None:
            return None
        return settings.describe_feature(self.session.features.get(feature))

    @property
    def account_name(self) -> Optional[str]:
        return self.session.account_name if self.ready and self.session is not None else None

    # ---- pairing -------------------------------------------------------------------------------------

    def request_pairing(self) -> None:
        """Asks DCT for a pairing code (connecting first, or pairing again after the user agreed)."""
        session = self._session()
        self.want_connected = True
        self.pairing_not_started = False
        if self.pairing_required is not None:
            self.pairing_required = None
            session.confirm_repair()
        else:
            session.retry_pairing()
            if session.state == IDLE:
                session.start()
        self.touch()

    def submit_pairing_code(self, text: str) -> None:
        code = settings.normalize_pairing_code(text)
        if code is None:
            raise ValueError("The pairing code has six digits.")
        if self.session is None or self.session.state != PAIRING or self.pairing_prompt is None:
            raise ValueError("Durty Cloth Tool is not waiting for a pairing code. Click Request Code first.")
        self.session.submit_pairing_code(code)
        self.touch()

    def remove_pairing(self) -> None:
        self._ensure_setup()
        self.disconnect()
        assert self.pairing_store is not None
        self.pairing_store.clear()
        self.paired = False
        self.pairing_required = None
        self.notice = Notice("INFO", "Removed the pairing. Also remove Blender from the paired apps in Durty Cloth "
                                     "Tool (Options > Creator Link).")
        self.touch()

    # ---- sign-in -------------------------------------------------------------------------------------

    def active_sign_in(self):
        """The sign-in waiting for approval: ``(display code, link)`` or ``None``."""
        if self.token_source is None:
            return None
        flow = self.token_source.active_flow()
        if flow is None:
            return None
        return settings.display_user_code(flow.user_code), flow.verification_uri_complete or flow.verification_uri

    @property
    def starting_sign_in(self) -> bool:
        return self._sign_in_task is not None

    def start_sign_in(self) -> None:
        """Starts (or reuses) the device sign-in; the browser opens once gta.clothing answered (see ``poll``)."""
        self._ensure_setup()
        assert self.token_source is not None
        if not self.online():
            raise auth.AuthError("offline", "online access is off")
        self.token_source.allow_sign_in()
        self.signed_out = False
        active = self.active_sign_in()
        if active is not None:
            self.open_url(active[1])
            return
        if self._sign_in_task is None:
            self._sign_in_task = self.token_source.begin_device_sign_in()
        self._open_when_ready = True
        self.notice = Notice("INFO", "Starting the sign-in")
        self.touch()

    def sign_in_with_dct(self) -> None:
        """Connects (pairing first when needed); the session then asks DCT to approve the sign-in."""
        session = self._session()
        self.want_connected = True
        self.signed_out = False
        self.notice = None
        session.sign_in()
        self.touch()

    def cancel_sign_in(self) -> None:
        if self.token_source is not None:
            self.token_source.cancel()
        if self._sign_in_task is not None:
            self._sign_in_task.cancel()
            self._sign_in_task = None
        self._open_when_ready = False
        self.touch()

    def sign_out(self) -> None:
        """Ends the gta.clothing session (when online) and forgets it here; DCT disconnects as well. The sign-out
        is remembered: no sign-in starts until the user asks for one."""
        self._ensure_setup()
        assert self.link_auth is not None
        self.disconnect()
        self.cancel_sign_in()
        online = self.online()
        if online:
            if self._http is not None:
                self._http.logout_reached = None
            self._logout_task = self.link_auth.begin_logout()
            self.notice = Notice("INFO", "Signing out")
        else:
            self.link_auth.store.save({"signedOut": True})
            self.notice = Notice("WARNING", "Signed out on this computer. Allow online access in Blender's "
                                            "preferences to also end the session on gta.clothing.")
        self.user_name = None
        self.signed_out = True
        self.touch()

    # ---- polling -------------------------------------------------------------------------------------

    def poll(self) -> float:
        """One timer step. Returns the seconds until the next step."""
        now = time.monotonic()
        if self.session is not None:
            self.session.poll()
        self._poll_tasks()
        try:
            self.stream.tick(now)
        except Exception as exc:  # noqa: BLE001 - stop the stream, show why, keep the link running
            traceback.print_exc()
            self.stream.fail(f"Streaming stopped after an unexpected problem: {type(exc).__name__}: {exc}")
            self.touch()
        try:
            self.model.tick(now)
        except Exception as exc:  # noqa: BLE001 - show why, keep the link running
            traceback.print_exc()
            self.model.status = Notice("ERROR", f"The automatic push failed: {type(exc).__name__}: {exc}")
            self.touch()
        working = self.stream.active or self.model.pushing
        waiting = self._sign_in_task is not None or self._logout_task is not None or self.active_sign_in() is not None
        state = self.session.state if self.session is not None else IDLE
        if state == READY and working:
            return 0.02
        if state in (HELLO, PAIRING, SIGNING_IN, AUTHENTICATING):
            return 0.05
        if state == READY or waiting:
            return 0.1
        return 0.25

    def _poll_tasks(self) -> None:
        task = self._sign_in_task
        if task is not None and task.poll():
            self._sign_in_task = None
            try:
                flow = task.result()
            except auth.AuthError as exc:
                self._open_when_ready = False
                self.notice = Notice("ERROR", settings.describe_error(exc.code, str(exc)))
            else:
                self.notice = Notice("INFO", "Approve the sign-in in your browser. The code there must be "
                                             f"{settings.display_user_code(flow.user_code)}.")
                if self._open_when_ready:
                    self._open_when_ready = False
                    self.open_url(flow.verification_uri_complete or flow.verification_uri)
            self.touch()
        task = self._logout_task
        if task is not None and task.poll():
            self._logout_task = None
            reached = True
            try:
                task.result()
            except Exception:  # noqa: BLE001 - the server session could not be ended; forget it here anyway
                if self.link_auth is not None:
                    self.link_auth.store.save({"signedOut": True})
                reached = False
            if self._http is not None and self._http.logout_reached is False:
                reached = False
            if reached:
                self.notice = Notice("INFO", "Signed out.")
            else:
                self.notice = Notice("WARNING", "Signed out on this computer; gta.clothing could not be reached. The "
                                                "session there ends by itself, or end it on your account page.")
            self.touch()
        source = self.token_source
        # The flow itself, not active_flow(): the worker that receives the approval sets its access token before
        # this poll sees the request finish.
        flow = source.flow if source is not None else None
        if flow is None or flow.cancelled or (self.session is not None and self.session.state == SIGNING_IN):
            return  # nothing waiting, or the session polls the same sign-in itself
        try:
            token = flow.poll()  # never blocks: the request runs on a worker thread
        except auth.AuthError as exc:
            assert source is not None
            source.flow = None
            self.notice = Notice("ERROR", settings.describe_error(exc.code, str(exc)))
            self.touch()
            return
        if token:
            assert source is not None
            source.flow = None
            self.refresh_account()
            self.notice = Notice("INFO", f"Signed in as {self.user_name}.")
            if self.want_connected and self.session is not None and self.session.state in (IDLE, STOPPED, WAITING):
                self.session.sign_in()
            self.touch()

    # ---- session events ------------------------------------------------------------------------------

    def _on_state(self, state: str) -> None:
        previous, self.state = self.state, state
        if state == HELLO:
            self.dct_seen = True
        if state != PAIRING:
            self.pairing_prompt = None
        if state != SIGNING_IN:
            self.sign_in_prompt = None
        if previous == PAIRING and state in (SIGNING_IN, AUTHENTICATING):
            self.paired = True
            self.pairing_not_started = False
            self.notice = Notice("INFO", "Paired with Durty Cloth Tool.")
        self.touch()

    def _on_ready(self, welcome: Dict[str, Any]) -> None:
        self.paired = True
        self.pairing_not_started = False
        self.pairing_required = None
        self.signed_out = False
        self.notice = None
        if self.token_source is not None and self.token_source.active_flow() is None:
            self.token_source.flow = None
        self.refresh_account()
        assert self.session is not None
        self.session.context().add_done_callback(self._on_context)
        self.touch()

    def _on_context(self, request: Request) -> None:
        if request.error is None:
            message = request.result()
            self.project = message.get("project")
            self.focused = message.get("focused")
            self.touch()

    def _on_pairing(self, prompt) -> None:
        self.pairing_prompt = prompt
        self.pairing_not_started = False
        if prompt.error:
            left = prompt.attempts_left
            self.notice = Notice("WARNING", f"{settings.describe_error(prompt.error)} {left} "
                                            f"{'try' if left == 1 else 'tries'} left.")
        else:
            self.notice = None  # the pairing box says what to do
        self.touch()

    def _on_pairing_required(self, required: PairingRequired) -> None:
        self.pairing_required = required
        self.notice = Notice("WARNING", settings.describe_pairing_required(required.reason, required.endpoint_trusted))
        self.touch()

    def _on_sign_in(self, prompt: SignInPrompt) -> None:
        self.sign_in_prompt = prompt
        if prompt.assisted_by_dct is True:
            self.notice = Notice("INFO", "Durty Cloth Tool approved the sign-in. Finishing.")
        elif prompt.assisted_by_dct is False:
            self.notice = Notice("WARNING", "Durty Cloth Tool did not approve the sign-in. You can approve it in the "
                                            "browser instead.")
        else:
            self.notice = Notice("INFO", "Approve the sign-in in Durty Cloth Tool, or in your browser.")
        self.touch()

    def _on_signed_out(self) -> None:
        self.signed_out = True
        self.user_name = None
        self.notice = Notice("INFO", "You signed out. Sign in to connect to Durty Cloth Tool.")
        self.touch()

    def _on_selection(self, message: Dict[str, Any]) -> None:
        self.focused = message.get("focused")
        self.touch()

    def _on_project(self, message: Dict[str, Any]) -> None:
        self.project = message.get("project")
        if self.project is None:
            self.focused = None
        self.touch()

    def _on_incompatible(self, message: Dict[str, Any]) -> None:
        self.incompatible = message
        self.touch()

    def _on_error(self, error: LinkError) -> None:
        code = error.code
        if code == "pairing-not-started":
            self.pairing_not_started = True
        if code in settings.SIGNED_OUT_CODES:
            self.user_name = None
        if code in ("token-invalid", "signed-out"):
            return  # the session refreshes and retries by itself; signed-out has its own event
        level = "WARNING" if code in ("pairing-not-started", "disconnected", "busy", "rate-limited") else "ERROR"
        self.notice = Notice(level, settings.describe_error(code, error.message))
        self.touch()

    def _on_disconnected(self, code: Optional[int], reason: str) -> None:
        self.project = None
        self.focused = None
        self.stream.on_disconnected()
        self.model.on_disconnected()
        self.touch()

    def status_text(self) -> str:
        if self.ready:
            return f"Connected as {self.account_name}"
        if self.state == WAITING and self.dct_seen:
            return "Reconnecting to Durty Cloth Tool"
        if self.state in (IDLE, STOPPED) and self.signed_out:
            return "Signed out"
        return settings.describe_state(self.state)


def describe_focus(focused: Optional[Dict[str, Any]]) -> List[str]:
    """Lines describing the item focused in DCT."""
    if not focused:
        return ["No cloth selected in Durty Cloth Tool"]
    lines = [f"Cloth: {focused.get('name')}"]
    selected = focused.get("selectedTextureId")
    for texture in focused.get("textures") or []:
        if texture.get("textureId") == selected:
            size = ""
            if texture.get("width") and texture.get("height"):
                size = f" ({texture['width']} x {texture['height']})"
            lines.append(f"Texture: {texture.get('name')}{size}")
            break
    return lines


__all__ = [
    "LinkController",
    "ModelPush",
    "Notice",
    "TokenSource",
    "TextureStream",
    "describe_focus",
]
