# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Schmid Software Solutions (https://schmid-software.de)
"""The add-on's link to Durty Cloth Tool: connection, sign-in, live preview, texture checks, model pushes, the
textures and models Durty Cloth Tool sends ("Edit in connected app") and the linked cloth's picture.

``LinkController.poll`` runs on Blender's main thread from a ``bpy.app.timers`` timer and drives the dct_link
session; session callbacks run inside that call. Network calls to gta.clothing (sign-in, renewing it, sign-in
assertions, sign-out) run as dct_link tasks on worker threads that never touch Blender; the timer only checks
whether they finished.

Texts for the user are :class:`strings.Msg` values (a key and its fields); the panels render them in Blender's
language. Nothing in this module imports Blender. The Blender side passes in where to keep files, how to read
an image, how to export a model and how to open what Durty Cloth Tool sends (:class:`DocumentHost`), so the flows
can be tested against a fake Durty Cloth Tool without Blender.
"""

from __future__ import annotations

import collections
import pathlib
import shutil
import tempfile
import time
import traceback
from typing import Any, Callable, Deque, Dict, List, NamedTuple, Optional, Protocol, Set

from . import bundle, settings
from .dct_link import auth, protocol, tokens
from .dct_link.session import (
    AUTHENTICATING,
    HELLO,
    IDLE,
    READY,
    SIGNING_IN,
    STOPPED,
    WAITING,
    HostOpenModel,
    HostOpenTexture,
    LinkError,
    LinkSession,
    LiveSurface,
    PluginInfo,
    Request,
    SignInPrompt,
    Thumbnail,
)
from .pixels import Conversion, StreamBuffers, limit_rects
from .strings import Msg, UserError, english, msg


class Notice(NamedTuple):
    """A message for the panels. ``level`` is ``INFO``, ``WARNING`` or ``ERROR``."""

    level: str
    message: Msg

    @property
    def text(self) -> str:
        """The English text (logs and tests); the panels render :attr:`message` in Blender's language."""
        return english(self.message)


def _error_notice(code: Optional[str]) -> Notice:
    return Notice("ERROR", settings.describe_error(code))


def _detail(exc: BaseException) -> Any:
    """What went wrong, for a message field: the user's message, or the error itself (logged to the console)."""
    if isinstance(exc, UserError):
        return exc.message
    if isinstance(exc, OSError):
        return str(exc.strerror or exc)
    traceback.print_exception(type(exc), exc, exc.__traceback__)
    return f"{type(exc).__name__}: {exc}"


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


class _Waiter:
    """One caller's view of the device sign-in that is being started. The session and the Sign In button can wait
    for the same start, so there is only ever one code; cancelling one view leaves the start running for the other
    (Cancel in the panel ends it through :meth:`TokenSource.cancel`)."""

    def __init__(self, task: _RememberFlow) -> None:
        self._task = task

    def poll(self) -> bool:
        return self._task.poll()

    def result(self) -> Any:
        return self._task.result()

    def cancel(self) -> None:
        pass


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
        self._starting: Optional[_RememberFlow] = None

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
        starting = self._starting
        if starting is not None and starting.poll():  # finished: a flow it brought is the shared one now
            self._starting = starting = None
            flow = self.active_flow()
            if flow is not None:
                return _Finished(flow)
        if starting is None:  # nothing on its way: start one
            self.flow = None
            # The computer name is shown on the approval page; the preference may have changed since start-up.
            self.auth.info = self.auth.info._replace(device_name=self.device_name() or None)
            starting = self._starting = _RememberFlow(self.auth.begin_device_sign_in(), self)
        return _Waiter(starting)

    def start_device_sign_in(self) -> auth.DeviceFlow:  # the blocking form; the session prefers begin_*
        if not self.online():
            raise self._offline()
        flow = self.active_flow()
        if flow is None:
            self.auth.info = self.auth.info._replace(device_name=self.device_name() or None)
            flow = self.flow = self.auth.start_device_sign_in()
        return flow

    def cancel(self) -> None:
        if self._starting is not None:
            self._starting.cancel()
            self._starting = None
        if self.flow is not None:
            self.flow.cancel()
        self.flow = None


# --------------------------------------------------------------------------------------------------
# Texture streaming
# --------------------------------------------------------------------------------------------------


class ImageSource(Protocol):
    """What the stream needs from the Blender image (see ``host.BlenderImageSource``)."""

    def problem(self) -> Optional[Msg]: ...  # why the image can no longer be streamed

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
    """The live preview: streams one Blender image into a live texture on the cloth focused in DCT.

    Captures never run during a paint stroke; the image is captured once the stroke ends. A capture reads the
    image in one step and then works through it a few tiles at a time, a few milliseconds per timer step.
    Without strokes the image is checked now and then (only while Blender marks it changed), less and less often
    while nothing changes. While paused nothing is captured; resuming captures everything changed meanwhile.
    """

    STEP_BUDGET = 0.006
    AFTER_CHANGE = 0.5
    AFTER_CHANGE_UNSEEN = 1.5  # when strokes cannot be seen, captures keep further apart while the image changes
    IDLE_FIRST = 1.0
    IDLE_MAX = 30.0
    READ_SHARE = 20.0  # an idle check reads the image for at most one twentieth of the time
    #: Changed areas marked per timer step; more are merged so a busy image does not flood DCT with frames.
    RECTS_PER_STEP = 4
    #: How long a result such as "Live preview stopped." stays in the panel (warnings and errors stay).
    INFO_SECONDS = 30.0

    def __init__(self, controller: "LinkController") -> None:
        self.controller = controller
        self.source: Optional[ImageSource] = None
        self.buffers: Optional[StreamBuffers] = None
        self._pixel_source: Optional[_PixelSource] = None
        self.surface: Optional[LiveSurface] = None
        self.opening: Optional[Request] = None
        self.target: Optional[str] = None
        self.document: Optional[str] = None
        #: The cloth and variation the image is bound to (an image opened from Durty Cloth Tool), sent with every
        #: live.open so the image stays linked to its cloth; ``None`` follows the selection in Durty Cloth Tool.
        self.binding: Optional[Dict[str, str]] = None
        self.width = 0
        self.height = 0
        #: Why the image's colours may arrive changed (its colour space), shown while the preview runs.
        self.warning: Optional[Msg] = None
        self.live_state: Optional[str] = None
        self._status: Optional[Notice] = None
        self.status_at = 0.0
        self.saving = False
        self.paused = False
        #: Changes are on the ped that the project does not have yet.
        self.unsaved = False
        #: Durty Cloth Tool's texture checks for the running preview (``None``: not checked yet).
        self.findings: Optional[List[Dict[str, Any]]] = None
        self.checking = False
        self.checks_problem: Optional[Msg] = None
        self.next_check = 0.0
        self.quiet_checks = 0
        self._first_capture = False
        self._stroke_seen = False
        self._changes = 0
        self._force = False
        self._check_request: Optional[Request] = None

    @property
    def active(self) -> bool:
        return self.buffers is not None

    @property
    def is_open(self) -> bool:
        return self.surface is not None and not self.surface.closed

    @property
    def reading(self) -> bool:
        """The first capture is still being worked through (nothing has reached the ped yet)."""
        return self.active and self._first_capture

    @property
    def progress(self) -> Optional[float]:
        """How far the first capture got (0 to 1) while it runs, otherwise ``None``."""
        if self.buffers is None or not self._first_capture:
            return None
        return self.buffers.progress

    def start(self, source: ImageSource, target: str, width: int, height: int,
              conversion: Conversion = Conversion(), *, document: Optional[str] = None,
              warning: Optional[Msg] = None, binding: Optional[Dict[str, str]] = None) -> None:
        """Opens a live texture for ``target`` on the cloth ``binding`` names, or on the item focused in DCT without
        one. Raises :class:`strings.UserError` when that is not possible now."""
        session = self.controller.ready_session()
        problem = settings.check_stream_size(width, height) or self.controller.feature_problem(settings.FEATURE_LIVE_TEXTURE)
        if problem:
            raise UserError(problem)
        if target not in protocol.LIVE_TARGETS:
            raise ValueError(f"unknown map {target!r}")
        self.stop()
        buffers = StreamBuffers(width, height, source.read_into, conversion)
        pixel_source = _PixelSource(buffers)
        try:
            buffers.begin(full=True)  # converted over the next timer steps; the first frame waits for it
            request = session.open_live(target, width, height, binding=binding, document=document,
                                        pixel_source=pixel_source)
        except BaseException:
            pixel_source.release()
            raise
        self.source, self.buffers, self.target, self.document = source, buffers, target, document
        self.binding = dict(binding) if binding else None
        self.width, self.height = width, height
        self._pixel_source = pixel_source
        self.warning = warning
        self.live_state = None
        self.paused = False
        self.unsaved = False
        self.findings = None
        self.checks_problem = None
        self._first_capture = True
        self._stroke_seen = self._force = False
        self.quiet_checks = 0
        self.status = None
        self.opening = request
        request.add_done_callback(self._on_opened)

    def _on_opened(self, request: Request) -> None:
        if request is not self.opening:
            if request.error is None:
                _close_quietly(request.result())  # a newer start or a stop replaced this one
            return
        self.opening = None
        if request.error is not None:
            self.status = _error_notice(request.error.code)
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
            self._mark_all()
        self.check_texture()
        self.controller.touch()

    @property
    def status(self) -> Optional[Notice]:
        """The latest result or problem of the live preview, for the panel."""
        return self._status

    @status.setter
    def status(self, notice: Optional[Notice]) -> None:
        self._status = notice
        self.status_at = time.monotonic()

    def tick(self, now: float) -> None:
        notice = self._status
        if notice is not None and notice.level == "INFO" and now - self.status_at > self.INFO_SECONDS:
            self._status = None  # a result fades; the panel shows the current state instead
            self.controller.touch()
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
        if self.paused and not self._first_capture:
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
                    self.next_check = now + self.AFTER_CHANGE
                self.controller.touch()  # the progress bar moves
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
        if not self.unsaved:
            self.unsaved = True
            self.controller.touch()

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

    def pause(self) -> None:
        """Stops sending changes for now; the ped keeps the last update."""
        if self.active:
            self.paused = True
            self.controller.touch()

    def resume(self) -> None:
        """Sends changes again, starting with whatever changed while paused."""
        if self.paused:
            self.paused = False
            self._force = True
            self.controller.touch()

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
            raise UserError(msg("notice.start-live-first"))
        problem = self.controller.feature_problem(settings.FEATURE_SAVE)
        if problem:
            raise UserError(problem)
        if mode == "newVariation" and self.target != "diffuse":
            raise UserError(msg("notice.diffuse-only"))
        if self.source is not None and self.source.problem() is None:
            self._capture_now()  # the save covers the newest pixels, also those changed while paused
        self.saving = True
        name = self.controller.cloth_label(self.surface.binding)
        request = self.surface.save(mode)
        self.status = None
        request.add_done_callback(lambda r: self._on_saved(r, mode, name))
        return request

    def _on_saved(self, request: Request, mode: str, name: Optional[str]) -> None:
        self.saving = False
        if request.error is not None:
            self.status = _error_notice(request.error.code)
        else:
            result = request.result()
            if result.get("ok"):
                self.unsaved = False
                if mode == "newVariation":
                    message = msg("live.saved-variation", name=name) if name else msg("live.saved-variation-unnamed")
                else:
                    message = msg("live.saved", name=name) if name else msg("live.saved-unnamed")
                self.status = Notice("INFO", message)
            else:
                self.status = _error_notice(result.get("code"))
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
        self.status = Notice("INFO", msg("live.discarded"))

    def stop(self) -> None:
        """Closes the live texture. One still opening is closed when DCT answers (see ``_on_opened``)."""
        was_active, was_unsaved = self.active, self.unsaved
        surface = self.surface
        self.opening = None
        if surface is not None:
            _close_quietly(surface)
        self._release()
        if was_active:
            # Stopping drops the changes from Durty Cloth Tool's preview; the Blender image keeps them.
            self.status = Notice("INFO", msg("live.stopped-unsaved" if was_unsaved else "live.stopped"))

    def fail(self, message: Msg) -> None:
        self.stop()
        self.status = Notice("ERROR", message)

    def _release(self) -> None:
        if self._pixel_source is not None:
            self._pixel_source.release()  # frees the pixels now, not when DCT confirms the close
        self._pixel_source = None
        self.surface = None
        self.buffers = None
        self.source = None
        self.binding = None
        self.saving = False
        self.paused = False
        self.unsaved = False
        self.live_state = None
        self.warning = None
        self.findings = None
        self.checking = False
        self.checks_problem = None
        self._check_request = None
        self._force = self._stroke_seen = self._first_capture = False
        self.quiet_checks = 0

    # ---- texture checks ------------------------------------------------------------------------------

    def check_texture(self) -> None:
        """Asks DCT to check the image against the cloth (``texture.validate``); the result fills ``findings``."""
        session = self.controller.session
        if not self.is_open or session is None or self.target is None:
            return
        problem = self.controller.feature_problem(settings.FEATURE_SERVICES)
        if problem:
            self.checks_problem = msg("checks.unavailable")
            return
        self.checking = True
        self.checks_problem = None
        binding = self.surface.binding if self.surface is not None else None
        request = session.validate_texture(self.target, self.width, self.height, binding=binding)
        self._check_request = request
        request.add_done_callback(self._on_checked)

    def _on_checked(self, request: Request) -> None:
        if request is not self._check_request:
            return
        self._check_request = None
        self.checking = False
        if request.error is not None:
            code = request.error.code
            self.checks_problem = (msg("checks.unavailable") if code in ("needs-license", "needs-ultimate")
                                   else settings.describe_error(code))
        else:
            self.findings = [f for f in request.result().get("findings") or [] if isinstance(f, dict)]
        self.controller.touch()

    # ---- session events ------------------------------------------------------------------------------

    def on_live_status(self, surface: LiveSurface, message: Dict[str, Any]) -> None:
        if surface is self.surface:
            self.live_state = message.get("state")
            self.controller.touch()

    def on_live_closed(self, surface: LiveSurface, reason: str) -> None:
        if surface is self.surface:
            self._release()
            saved = self.status is not None and self.status.message.key.startswith("live.saved")
            if not (reason == "closed" and saved):  # keep "Saved ..." when DCT ends the live texture after a save
                self.status = Notice("INFO" if reason == "closed" else "WARNING", settings.describe_close_reason(reason))
            self.controller.touch()

    def on_live_error(self, surface: LiveSurface, error: LinkError) -> None:
        if surface is self.surface:
            self.status = _error_notice(error.code)
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

    SAVE_RETRIES = 5
    SAVE_RETRY_DELAY = 1.0

    def __init__(self, controller: "LinkController") -> None:
        self.controller = controller
        self.lease: Optional[str] = None
        #: The cloth and variation DCT shows the pushed model on (from ``model.applied``).
        self.lease_binding: Optional[Dict[str, str]] = None
        #: A pushed model that waits until DCT took the previous one off the ped: (files, binding).
        self._switch: Optional[tuple] = None
        self.revision: Optional[int] = None
        self.findings: List[Dict[str, Any]] = []
        self.root_name: Optional[str] = None
        self.pending: Optional[Request] = None
        self.busy: Optional[str] = None  # "saving" or "discarding"
        self.status: Optional[Notice] = None
        #: What Sollumz reported for the last export (warnings), shown beside the status.
        self.note: Optional[Notice] = None
        self._open_notice: Optional[Notice] = None
        self._open_notice_at = 0.0
        self.auto_push = False
        #: Whether Push Automatically is on right now; Blender reads the scene's setting.
        self.auto_enabled: Callable[[], bool] = lambda: self.auto_push
        #: Automatic pushes stop after an export with warnings until the user pushes again.
        self.paused = False
        self.delay = settings.AUTO_PUSH_DELAY_DEFAULT
        self.due_at: Optional[float] = None
        self.on_auto_push: Optional[Callable[[], None]] = None
        #: Why an automatic push waits right now (Edit Mode, a running tool), for the panel.
        self.waiting: Optional[Msg] = None
        self._saved = False
        self._save_tries = 0
        self._save_retry_at: Optional[float] = None

    @property
    def pushing(self) -> bool:
        return self.pending is not None and not self.pending.done

    @property
    def open_notice(self) -> Optional[Notice]:
        """The outcome of opening a model from Durty Cloth Tool (a result fades after a while, like the stream's)."""
        return self._open_notice

    @open_notice.setter
    def open_notice(self, notice: Optional[Notice]) -> None:
        self._open_notice = notice
        self._open_notice_at = time.monotonic()

    @property
    def save_blocker(self) -> Optional[Msg]:
        """Why Save cannot run now, or ``None``. Saving while a newer push is on its way would store the model
        DCT showed before it."""
        if self.lease is None:
            return msg("model.block.no-model")
        if self.busy == "saving":
            return msg("model.block.saving")
        if self.busy is not None:
            return msg("model.block.waiting")
        if self.pushing:
            return msg("model.block.pushing")
        if self.due_at is not None:
            return msg("model.block.due")
        return None

    def push(self, export: Callable[[str], Any], root_name: Optional[str] = None, *, automatic: bool = False,
             binding: Optional[Dict[str, str]] = None) -> Request:
        """Exports with ``export(folder)`` into a temporary folder, collects the files and pushes them. ``export``
        may return an object whose ``warnings`` says the exporter logged warnings.

        ``binding`` is the cloth a model opened from Durty Cloth Tool belongs to. The first push names it; later
        pushes use the lease DCT returned. When the model shown now belongs to another cloth, DCT is asked to take
        it off the ped first, and the push follows once it did.

        Raises :class:`strings.UserError` (or another ``ValueError``) with a message for the user.
        """
        session = self.controller.ready_session()
        problem = self.controller.feature_problem(settings.FEATURE_MODEL)
        if problem:
            raise UserError(problem)
        if self._switch is not None:
            raise UserError(msg("model.block.waiting"))
        folder = tempfile.mkdtemp(prefix="dct_link_")
        try:
            result = export(folder)
            model_bundle, collected = bundle.build_bundle(folder)
        finally:
            shutil.rmtree(folder, ignore_errors=True)
        self.root_name = root_name
        self._saved = False
        self.note = None
        self.waiting = None
        if getattr(result, "warnings", False):
            if automatic:
                self.paused = True
                self.due_at = None
                self.note = Notice("WARNING", msg("model.warnings-paused"))
            else:
                self.note = Notice("WARNING", msg("model.warnings"))
        if not automatic:
            self.paused = False
        self.status = Notice("INFO", msg("model.sending", name=collected.model.name, count=len(collected.textures)))
        if binding is not None and self.lease is not None and not same_binding(self.lease_binding, binding):
            # The model on the ped belongs to another cloth: DCT ends it first, then this one is pushed bound.
            request = session.discard_model()
            self._switch = (model_bundle, dict(binding))
            self.pending = request
            request.add_done_callback(self._on_switched)
        else:
            request = session.push_model(model_bundle, binding=binding)
            self.pending = request
            request.add_done_callback(self._on_pushed)
        self.controller.touch()
        return request

    def _on_switched(self, request: Request) -> None:
        """DCT took the previous model off the ped: push the waiting one, bound to its cloth."""
        switch, self._switch = self._switch, None
        if request is self.pending:
            self.pending = None
        if switch is None:
            return
        if request.error is not None and request.error.code != "lease-not-found":
            self.status = _error_notice(request.error.code)
            self.controller.touch()
            return
        self._forget_lease()
        self.controller.release_model_files()
        session = self.controller.session
        if session is None or not self.controller.ready:
            self.status = Notice("WARNING", settings.describe_close_reason("disconnected"))
            self.controller.touch()
            return
        bundle, binding = switch
        pushed = session.push_model(bundle, binding=binding)
        self.pending = pushed
        pushed.add_done_callback(self._on_pushed)
        self.controller.touch()

    def _on_pushed(self, request: Request) -> None:
        if request is self.pending:
            self.pending = None
        if request.error is not None:
            if request.error.code != "superseded":
                self.status = _error_notice(request.error.code)
                self.controller.touch()
            return
        self._applied(request.result())

    def _applied(self, message: Dict[str, Any]) -> None:
        self.lease = message.get("lease")
        binding = message.get("binding")
        self.lease_binding = dict(binding) if isinstance(binding, dict) else None
        self.revision = message.get("revision")
        self.findings = list(message.get("findings") or [])
        self.status = Notice("INFO", msg("model.previewing"))
        self.controller.touch()

    def _forget_lease(self) -> None:
        self.lease = None
        self.lease_binding = None
        self.revision = None
        self.findings = []

    def on_applied(self, message: Dict[str, Any]) -> None:
        """``model.applied`` as an event (also after the request finished, which changes nothing)."""
        self._applied(message)

    def save(self) -> Request:
        session = self.controller.ready_session()
        blocker = self.save_blocker
        if blocker is not None:
            raise UserError(blocker)
        self._save_tries = 0
        self.busy = "saving"
        self.status = Notice("INFO", msg("model.saving"))
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
        except LinkError as exc:
            self.busy = None
            self.status = _error_notice(exc.code)
        except UserError as exc:
            self.busy = None
            self.status = Notice("ERROR", exc.message)
        self.controller.touch()

    def _on_saved(self, request: Request) -> None:
        if self.busy != "saving":
            return  # disconnected or discarded meanwhile
        if (request.error is not None and request.error.code == "busy" and self.lease is not None
                and self._save_tries < self.SAVE_RETRIES):
            # DCT is still loading this model (or handling other requests); ask again shortly.
            self._save_tries += 1
            self._save_retry_at = time.monotonic() + self.SAVE_RETRY_DELAY
            self.status = Notice("INFO", msg("model.save-retry"))
            self.controller.touch()
            return
        self.busy = None
        if request.error is not None and request.error.code == "busy":
            self.status = Notice("WARNING", msg("model.save-busy"))
        elif request.error is not None:
            self.status = _error_notice(request.error.code)
        elif request.result().get("ok"):
            self._saved = True
            self.status = Notice("INFO", msg("model.saved"))
        else:
            self.status = _error_notice(request.result().get("code"))
        self.controller.touch()

    def discard(self) -> Request:
        session = self.controller.ready_session()
        if self.lease is None:
            raise UserError(msg("model.block.no-model"))
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
            self.status = _error_notice(request.error.code)
        else:
            self._closed(request.result().get("reason"))
        self.controller.touch()

    def on_closed(self, message: Dict[str, Any]) -> None:
        if message.get("lease") == self.lease:
            self._closed(message.get("reason"))
            self.controller.touch()

    def _closed(self, reason: Optional[str]) -> None:
        self._forget_lease()
        self.controller.release_model_files()  # the model's own files are no longer needed in Blender
        self.due_at = None
        self.waiting = None
        self.note = None
        self._save_retry_at = None
        if self.busy == "saving":
            self.busy = None
        if self.open_notice is not None and self.open_notice.level == "INFO":
            self.open_notice = None  # "Opened from Durty Cloth Tool" belonged to the model shown until now
        if reason == "closed" and self._saved:
            return  # DCT ended the preview after the save; keep "Saved ..."
        if reason == "closed":
            self.status = Notice("INFO", msg("model.discarded"))
        else:
            self.status = Notice("WARNING", settings.describe_close_reason(reason))

    def on_disconnected(self) -> None:
        if self.lease is not None or self.pending is not None:
            self.status = Notice("WARNING", settings.describe_close_reason("disconnected"))
            self.controller.release_model_files()
        self._forget_lease()
        self._switch = None
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

    def postpone(self, now: float, reason: Optional[Msg] = None) -> None:
        """The push is due but cannot run yet; ``reason`` is shown in the panel until it runs."""
        if self.due_at is None:
            self.due_at = now + settings.clamp_auto_push_delay(self.delay)
        else:
            self.due_at = max(self.due_at, now + 0.5)
        if reason != self.waiting:
            self.waiting = reason
            self.controller.touch()

    def tick(self, now: float) -> None:
        notice = self._open_notice
        if notice is not None and notice.level == "INFO" and now - self._open_notice_at > TextureStream.INFO_SECONDS:
            self._open_notice = None
            self.controller.touch()
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

class FocusInfo(NamedTuple):
    """A cloth as the Linked Cloth panel shows it: the one focused in DCT, or the one the image is linked to."""

    name: str
    letter: Optional[str]
    texture: Optional[str]
    width: Optional[int]
    height: Optional[int]
    targets: tuple
    #: The cloth and variation (``clothId``, ``textureId``); ``textureId`` is missing when DCT selected none.
    binding: Dict[str, str] = {}
    #: What DCT says about the cloth (each may be missing): the game's token such as ``jbib``, ``male`` or
    #: ``female``, the collection and the cloth's number in it.
    drawable_type: Optional[str] = None
    gender: Optional[str] = None
    collection: Optional[str] = None
    number: Optional[int] = None
    #: The cloth comes from the image's link, not from the selection in DCT.
    linked: bool = False


def same_binding(a: Optional[Dict[str, str]], b: Optional[Dict[str, str]]) -> bool:
    """The same cloth and variation (ids compare without regard to case)."""
    if not a or not b:
        return False
    return all(str(a.get(key, "")).lower() == str(b.get(key, "")).lower() for key in ("clothId", "textureId"))


def binding_of(cloth_id: Any, texture_id: Any) -> Optional[Dict[str, str]]:
    """A binding from two ids, or ``None`` when one of them is not an id DCT would accept."""
    if protocol.is_guid(cloth_id) and protocol.is_guid(texture_id):
        return {"clothId": cloth_id, "textureId": texture_id}
    return None


class TextureDocument(NamedTuple):
    """A cloth's texture map to open in Blender: what DCT sent (``host.openTexture``) or what the add-on read
    (``texture.read``). ``pixels`` are RGBA8 rows from top to bottom."""

    binding: Dict[str, str]
    target: str
    name: str
    width: int
    height: int
    pixels: Any


class OpenedImage(NamedTuple):
    """The Blender image a :class:`TextureDocument` became, ready to stream."""

    source: Any  # an ImageSource
    width: int
    height: int
    conversion: Conversion
    document: str
    warning: Optional[Msg] = None
    handle: Any = None  # whatever the Blender side needs to finish the image later


class DocumentHost(Protocol):
    """What opening items from DCT needs from Blender (``state.BlenderDocuments``)."""

    def open_texture(self, document: TextureDocument) -> OpenedImage: ...  # creates or reuses the image

    def keep_texture(self, opened: OpenedImage) -> None: ...  # after DCT heard the answer (keeps the pixels)

    def model_problem(self) -> Optional[Msg]: ...  # why models cannot be opened now (Sollumz), or None

    def import_model(self, folder: pathlib.Path, model_file: str, binding: Dict[str, str]) -> "ImportedModel": ...


class ImportedModel(NamedTuple):
    """A model imported into Blender: the Drawable Dictionary's name and how to push it (bound to its cloth)."""

    name: str
    push: Callable[[], Any]


class _ModelImport(NamedTuple):
    request: Any  # the HostOpenModel
    folder: pathlib.Path
    model_file: str
    binding: Dict[str, str]
    name: str
    poll_number: int


#: The add-on's folder (inside its data folder) for the files of models opened from DCT.
MODELS_FOLDER = "opened-models"
#: The maps in Blender image names (data names stay English, like file names).
MAP_NAMES = {"diffuse": "Diffuse", "normal": "Normal", "specular": "Specular"}


def _inside(folder: pathlib.Path, name: str) -> pathlib.Path:
    """``folder / name`` for a bare file name that stays directly inside ``folder`` (``ValueError`` otherwise)."""
    if not protocol.is_file_name(name):
        raise ValueError(f"{name!r} is not a bare file name")
    path = folder / name
    if path.resolve().parent != folder.resolve():
        raise ValueError(f"{name!r} leaves its folder")
    return path


class LinkController:
    """Owns the dct_link session and the sign-in for one Blender process."""

    RECENT_ERRORS = 10
    #: After Sign In, how long the add-on looks for Durty Cloth Tool before it shows the browser code by itself.
    BROWSER_FALLBACK_SECONDS = 6.0
    #: The longest edge of the cloth's picture in the Linked Cloth panel.
    THUMBNAIL_SIZE = 128
    #: Clothes the add-on remembers from the selection, so a linked cloth keeps its name and details.
    KNOWN_CLOTHES = 64
    #: Files of opened models older than this are left over from an earlier session and removed at start-up.
    STALE_MODEL_FILES_SECONDS = 600.0

    def __init__(
        self,
        data_dir: Callable[[], pathlib.Path],
        host_version: str,
        *,
        online: Callable[[], bool] = lambda: True,
        device_name: Callable[[], Optional[str]] = lambda: None,
        secret_store: Callable[[str, pathlib.Path, str], Any] = tokens.default_secret_store,
        open_url: Callable[[str], None] = lambda url: None,
    ) -> None:
        self._data_dir_fn = data_dir
        self._secret_store = secret_store
        self.host_version = host_version
        self.channel = settings.CHANNEL
        self.online = online
        self.device_name = device_name
        self.open_url = open_url
        # Test seams: a fixed port keeps tests off the real link ports; the sign-in may use a loopback fake.
        self.port_override: Optional[int] = None
        self.auth_base_url: str = auth.BASE_URL

        self.session: Optional[LinkSession] = None
        self.link_auth: Optional[auth.LinkAuth] = None
        self.token_source: Optional[TokenSource] = None
        self.install_id: Optional[str] = None
        self.data_dir: Optional[pathlib.Path] = None

        self.want_connected = False
        self.state = IDLE
        self.dct_seen = False
        #: Durty Cloth Tool itself is signed out; the session keeps trying and connects once it is signed in.
        self.dct_signed_out = False
        #: The user disconnected this app in Durty Cloth Tool: nothing connects again until the user selects Connect.
        self.dct_disconnected = False
        #: An attempt to find Durty Cloth Tool failed since the last Connect (the setup says it is not running yet).
        self.search_failed = False
        self.signed_out = False
        self.sign_in_prompt: Optional[SignInPrompt] = None
        #: How a sign-in through Durty Cloth Tool is going, for the Sign In step.
        self.sign_in_status: Optional[Notice] = None
        self.notice: Optional[Notice] = None
        self.incompatible: Optional[Dict[str, Any]] = None
        self.project: Optional[Dict[str, Any]] = None
        self.focused: Optional[Dict[str, Any]] = None
        self.user_name: Optional[str] = None
        self.recent_errors: Deque[str] = collections.deque(maxlen=self.RECENT_ERRORS)
        self.changed = True
        self._sign_in_task: Any = None
        self._open_when_ready = False
        self._logout_task: Any = None
        #: After Sign In: when to show the browser code if Durty Cloth Tool was not found by then.
        self._browser_fallback_at: Optional[float] = None
        self._polls = 0

        #: Blender's side of opening what DCT sends (``None``: DCT hears ``not-supported``).
        self.documents: Optional[DocumentHost] = None
        self._open_notice: Optional[Notice] = None
        self._open_notice_at = 0.0
        #: The map being read from DCT for the Linked Cloth panel's map buttons.
        self.opening_map: Optional[str] = None
        #: The link of the image chosen for the live preview (Blender reads it from the image).
        self.linked_binding: Callable[[], Optional[Dict[str, str]]] = lambda: None
        #: The picture of the cloth in the Linked Cloth panel, and who shows it (Blender's preview icon).
        self.thumbnail: Optional[Thumbnail] = None
        self.on_thumbnail: Optional[Callable[[Optional[Thumbnail]], None]] = None
        self._thumbnail_key: Optional[tuple] = None
        self._thumbnail_request: Optional[Request] = None
        self._clothes: "collections.OrderedDict[str, Dict[str, Any]]" = collections.OrderedDict()
        self._model_import: Optional[_ModelImport] = None
        self._model_folders: Set[pathlib.Path] = set()
        self._keep_texture: Optional[tuple] = None

        self.stream = TextureStream(self)
        self.model = ModelPush(self)

    # ---- set-up --------------------------------------------------------------------------------------

    @property
    def open_notice(self) -> Optional[Notice]:
        """The outcome of opening a texture from Durty Cloth Tool, for the Linked Cloth panel (a result fades after
        :attr:`TextureStream.INFO_SECONDS`; warnings and errors stay)."""
        return self._open_notice

    @open_notice.setter
    def open_notice(self, notice: Optional[Notice]) -> None:
        self._open_notice = notice
        self._open_notice_at = time.monotonic()

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
        client = auth.ClientInfo(settings.PLUGIN_KIND, settings.VERSION, self.host_version, self.channel, install_id,
                                 self.device_name() or None)
        self.link_auth = auth.LinkAuth(client, token_store, folder / "auth.lock", base_url=self.auth_base_url)
        self.token_source = TokenSource(self.link_auth, self.online, self.device_name)
        self.install_id = install_id
        self.data_dir = folder
        self._remove_stale_model_files()
        self.refresh_account()

    def prepare(self) -> None:
        """Creates the add-on's folder and reads the stored sign-in (for the panels)."""
        self._ensure_setup()
        self.refresh_account()

    def refresh_account(self) -> None:
        """Re-reads who is signed in (kept in the secret store)."""
        if self.link_auth is None:
            return
        user = self.link_auth.user
        self.user_name = user.get("name") if user else None
        if self.user_name is None and self.link_auth.signed_in:
            self.user_name = "gta.clothing"
        self.signed_out = self.link_auth.signed_out_by_user
        self.touch()

    def _session(self) -> LinkSession:
        if self.session is None:
            self._ensure_setup()
            assert self.install_id is not None and self.token_source is not None
            plugin = PluginInfo(settings.PLUGIN_KIND, settings.VERSION, self.channel, settings.HOST_NAME,
                                self.host_version, self.install_id)
            session = LinkSession(
                plugin,
                token_source=self.token_source,
                port=self.port_override,
                use_discovery_file=self.port_override is None,
            )
            for event, handler in (
                ("state", self._on_state),
                ("ready", self._on_ready),
                ("sign-in", self._on_sign_in),
                ("signed-out", self._on_signed_out),
                ("dct-signed-out", self._on_dct_signed_out),
                ("dct-disconnected", self._on_dct_disconnected),
                ("selection", self._on_selection),
                ("project", self._on_project),
                ("entitlement", lambda message: self.touch()),
                ("live-status", self.stream.on_live_status),
                ("live-closed", self.stream.on_live_closed),
                ("live-error", self.stream.on_live_error),
                ("model-applied", self.model.on_applied),
                ("model-closed", self.model.on_closed),
                ("open-texture", self._on_open_texture),
                ("open-model", self._on_open_model),
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
        self.dct_disconnected = False
        self.search_failed = False
        self.incompatible = None
        self.notice = None
        session.start()
        self.touch()

    def disconnect(self) -> None:
        self.want_connected = False
        self.stream.stop()
        if self.session is not None:
            self.session.stop()
        self.dct_signed_out = False
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
        self._browser_fallback_at = None
        self._model_import = None
        self._keep_texture = None
        self.release_model_files()
        self.session = None
        self.state = IDLE

    @property
    def ready(self) -> bool:
        return self.session is not None and self.session.state == READY

    @property
    def connecting(self) -> bool:
        """The session runs (looking for DCT, handshaking or waiting to reconnect)."""
        return self.session is not None and self.state not in (IDLE, STOPPED)

    def ready_session(self) -> LinkSession:
        if not self.ready or self.session is None:
            raise UserError(msg("notice.connect-first"))
        return self.session

    def feature_problem(self, feature: str) -> Optional[Msg]:
        if self.session is None:
            return None
        return settings.describe_feature(self.session.features.get(feature))

    @property
    def account_name(self) -> Optional[str]:
        return self.session.account_name if self.ready and self.session is not None else None

    # ---- what the panels show ------------------------------------------------------------------------

    def setup_steps(self) -> tuple:
        """Whether each setup step is done: Durty Cloth Tool found, signed in."""
        found = self.ready or self.dct_seen
        signed_in = self.ready or (self.user_name is not None and not self.signed_out)
        return found, signed_in

    @property
    def setup_needed(self) -> bool:
        return not self.ready and not all(self.setup_steps())

    def chip(self) -> str:
        """The header's one-word status: ``connected``, ``live``, ``connecting``, ``action``, ``offline`` or
        ``problem``."""
        if self.ready:
            return "live" if self.stream.is_open and self.stream.live_state == "attached" else "connected"
        if not self.online() or self.incompatible is not None:
            return "problem"
        if (self.state == SIGNING_IN or self.dct_signed_out or self.active_sign_in() is not None
                or self.starting_sign_in or (self.signed_out and self.state in (IDLE, STOPPED))):
            return "action"
        if self.connecting:
            return "connecting"
        if self.notice is not None and self.notice.level == "ERROR":
            return "problem"
        return "offline"

    def status(self) -> Msg:
        """The connection's state in a few words."""
        if self.ready:
            return msg("state.ready", name=self.account_name or "gta.clothing")
        if self.dct_disconnected:
            return msg("state.dct-disconnected")
        if self.dct_signed_out:
            return msg("state.dct-signed-out")
        if self.state == WAITING and self.dct_seen:
            return msg("state.reconnecting")
        if self.state in (IDLE, STOPPED) and self.signed_out:
            return msg("state.signed-out")
        key = f"state.{self.state}"
        return msg(key) if key in _STATE_KEYS else msg("state.idle")

    @staticmethod
    def _info(cloth: Dict[str, Any], texture_id: Optional[str], linked: bool = False) -> FocusInfo:
        """A cloth DCT described (``focused`` in the context) with one of its variations."""
        letter = texture = width = height = None
        for index, item in enumerate(cloth.get("textures") or []):
            if isinstance(item, dict) and str(item.get("textureId", "")).lower() == str(texture_id or "").lower():
                letter = settings.variation_letter(index)
                texture = item.get("name")
                width, height = item.get("width"), item.get("height")
                break
        targets = tuple(t for t in cloth.get("targets") or () if t in protocol.LIVE_TARGETS)
        binding = {"clothId": str(cloth.get("clothId") or "")}
        if texture_id:
            binding["textureId"] = texture_id
        number = cloth.get("number")
        return FocusInfo(str(cloth.get("name") or ""), letter, texture, width, height, targets, binding,
                         cloth.get("drawableType"), cloth.get("gender"), cloth.get("collection"),
                         number if isinstance(number, int) else None, linked)

    def focus_info(self) -> Optional[FocusInfo]:
        """The cloth focused in DCT with its selected variation, or ``None``."""
        focused = self.focused
        if not focused:
            return None
        return self._info(focused, focused.get("selectedTextureId"))

    def known_cloth(self, cloth_id: Optional[str]) -> Optional[Dict[str, Any]]:
        """What DCT last said about a cloth that was selected there while connected, or ``None``."""
        return self._clothes.get(str(cloth_id or "").lower())

    def _remember_cloth(self, focused: Optional[Dict[str, Any]]) -> None:
        if isinstance(focused, dict) and focused.get("clothId"):
            key = str(focused["clothId"]).lower()
            self._clothes.pop(key, None)
            self._clothes[key] = focused
            while len(self._clothes) > self.KNOWN_CLOTHES:
                self._clothes.popitem(last=False)

    def card_binding(self) -> Optional[Dict[str, str]]:
        """The cloth the image belongs to: the running live preview's link, else the chosen image's link."""
        if self.stream.active and self.stream.binding:
            return self.stream.binding
        return self.linked_binding()

    def card_info(self) -> Optional[FocusInfo]:
        """The cloth the Linked Cloth panel shows: the one the image is linked to, otherwise the focused one."""
        linked = self.card_binding()
        if linked:
            cloth = self.known_cloth(linked.get("clothId"))
            if cloth is not None:
                return self._info(cloth, linked.get("textureId"), linked=True)
            return FocusInfo("", None, None, None, None, (), dict(linked), linked=True)
        return self.focus_info()

    def cloth_label(self, binding: Optional[Dict[str, str]] = None) -> Optional[str]:
        """A cloth and its variation, as in "jbib_003_u B": the one ``binding`` names, or the focused one."""
        if binding:
            cloth = self.known_cloth(binding.get("clothId"))
            info = self._info(cloth, binding.get("textureId")) if cloth is not None else None
        else:
            info = self.focus_info()
        if info is None or not info.name:
            return None
        return f"{info.name} {info.letter}" if info.letter else info.name

    def focus_label(self) -> Optional[str]:
        """The focused cloth and its variation, as in "jbib_003_u B"."""
        return self.cloth_label(None)

    def document_name(self, binding: Dict[str, str], target: str, fallback: str) -> str:
        """The name of the Blender image for a cloth's map, as in "jbib_003_u B Normal" (English, like file names);
        ``fallback`` (DCT's name of the texture) when the cloth was not seen in the selection."""
        label = self.cloth_label(binding)
        if label is None:
            return fallback or target
        return f"{label} {MAP_NAMES.get(target, target)}"

    def diagnostics(self, extra: Optional[Dict[str, str]] = None) -> str:
        """Support details for Copy Diagnostics: versions, link state and recent error codes. English; no paths,
        names, codes the user typed, tokens or other secrets."""
        session = self.session
        features = session.features if session is not None else {}
        stream, model = self.stream, self.model
        lines = [
            "Durty Cloth Tool Creator Link diagnostics",
            f"plugin: {settings.PLUGIN_KIND} {settings.VERSION} ({self.channel})",
            f"host: {settings.HOST_NAME} {self.host_version}",
            f"protocol: {protocol.PROTOCOL_MAJOR}.{protocol.PROTOCOL_MINOR}",
            f"state: {self.state}; chip: {self.chip()}; found: {self.dct_seen}; online access: {self.online()}",
            f"signed in: {self.user_name is not None}; signed out by user: {self.signed_out}; dct signed out: "
            f"{self.dct_signed_out}; disconnected in dct: {self.dct_disconnected}",
            f"features: {', '.join(f'{k}={v}' for k, v in sorted(features.items())) or 'none'}",
            f"live: {'open' if stream.is_open else 'active' if stream.active else 'off'}; map: {stream.target or 'none'}; "
            f"dct state: {stream.live_state or 'none'}; paused: {stream.paused}; findings: "
            f"{len(stream.findings) if stream.findings is not None else 'none'}",
            f"model: {'pushed' if model.lease else 'none'}; pushing: {model.pushing}; automatic paused: {model.paused}",
            f"recent errors: {', '.join(self.recent_errors) or 'none'}",
        ]
        for key, value in (extra or {}).items():
            lines.append(f"{key}: {value}")
        return "\n".join(lines)

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

    @property
    def finding_for_sign_in(self) -> bool:
        """After Sign In: Durty Cloth Tool is being looked for, to approve the sign-in there."""
        return (self._browser_fallback_at is not None and not self.ready and self.state != SIGNING_IN
                and self.active_sign_in() is None)

    def start_sign_in(self) -> None:
        """Sign In in the Browser: starts (or reuses) the device sign-in; the browser opens once gta.clothing
        answered (see ``poll``)."""
        self._ensure_setup()
        assert self.token_source is not None
        if not self.online():
            raise auth.AuthError("offline", "online access is off")
        self.token_source.allow_sign_in()
        self.signed_out = False
        self.want_connected = True  # once signed in, connect (also after a sign-out ended the connection)
        active = self.active_sign_in()
        if active is not None:
            self.open_url(active[1])
            return
        if self._sign_in_task is None:
            self._sign_in_task = self.token_source.begin_device_sign_in()
        self._open_when_ready = True
        self.notice = None
        self.touch()

    def sign_in(self) -> None:
        """Sign In: connects, and Durty Cloth Tool's approval window asks the user to approve the sign-in. When
        Durty Cloth Tool is not found within :data:`BROWSER_FALLBACK_SECONDS`, the browser code is shown instead
        (``poll``); the code stays the same, so Durty Cloth Tool can still approve it once it is found."""
        self._ensure_setup()
        if not self.online():
            raise auth.AuthError("offline", "online access is off")
        session = self._session()
        self.want_connected = True
        self.dct_disconnected = False
        self.signed_out = False
        self.search_failed = False
        self.notice = None
        self.sign_in_status = None
        self._browser_fallback_at = time.monotonic() + self.BROWSER_FALLBACK_SECONDS
        session.sign_in()
        self.touch()

    def _check_browser_fallback(self, now: float) -> None:
        """After Sign In: show the browser code once it is clear that Durty Cloth Tool is not there to approve."""
        if self._browser_fallback_at is None:
            return
        if (self.ready or self.state == SIGNING_IN or self.active_sign_in() is not None
                or self._sign_in_task is not None or self.token_source is None):
            self._browser_fallback_at = None  # Durty Cloth Tool asks, or a code is already shown
            return
        handshaking = self.state in (HELLO, AUTHENTICATING)
        if handshaking or not (self.search_failed or now >= self._browser_fallback_at):
            return
        self._browser_fallback_at = None
        if self.online():
            self._sign_in_task = self.token_source.begin_device_sign_in()
            self._open_when_ready = False  # the code is shown; the user opens the page
            self.touch()

    def cancel_sign_in(self) -> None:
        if self.token_source is not None:
            self.token_source.cancel()
        if self._sign_in_task is not None:
            self._sign_in_task.cancel()
            self._sign_in_task = None
        self._open_when_ready = False
        self._browser_fallback_at = None
        self.sign_in_status = None
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
            self._logout_task = self.link_auth.begin_logout()
            self.notice = Notice("INFO", msg("notice.signing-out"))
        else:
            self.link_auth.store.save({"signedOut": True})
            self.notice = Notice("WARNING", msg("notice.signed-out-local"))
        self.user_name = None
        self.signed_out = True
        self.touch()

    # ---- polling -------------------------------------------------------------------------------------

    def poll(self) -> float:
        """One timer step. Returns the seconds until the next step."""
        now = time.monotonic()
        self._polls += 1
        if self.session is not None:
            self.session.poll()  # also sends the answers to DCT's requests handled in the step before
        self._poll_tasks()
        self._check_browser_fallback(now)
        self._finish_opening()
        self._refresh_thumbnail()
        notice = self._open_notice
        if notice is not None and notice.level == "INFO" and now - self._open_notice_at > TextureStream.INFO_SECONDS:
            self._open_notice = None
            self.touch()
        try:
            self.stream.tick(now)
        except Exception as exc:  # noqa: BLE001 - stop the stream, show why, keep the link running
            traceback.print_exc()
            self.stream.fail(msg("live.failed", detail=f"{type(exc).__name__}: {exc}"))
            self.touch()
        try:
            self.model.tick(now)
        except Exception as exc:  # noqa: BLE001 - show why, keep the link running
            traceback.print_exc()
            self.model.status = Notice("ERROR", msg("model.failed", detail=f"{type(exc).__name__}: {exc}"))
            self.touch()
        working = self.stream.active or self.model.pushing or self._model_import is not None
        waiting = (self._sign_in_task is not None or self._logout_task is not None or self.active_sign_in() is not None
                   or self._browser_fallback_at is not None)
        state = self.session.state if self.session is not None else IDLE
        if state == READY and working:
            return 0.02
        if state in (HELLO, SIGNING_IN, AUTHENTICATING):
            return 0.05
        if state == READY or waiting:
            return 0.1
        return 0.25

    def _remember_error(self, code: Optional[str]) -> None:
        if code:
            self.recent_errors.append(code)

    def _poll_tasks(self) -> None:
        task = self._sign_in_task
        if task is not None and task.poll():
            self._sign_in_task = None
            try:
                flow = task.result()
            except auth.AuthError as exc:
                self._open_when_ready = False
                self._remember_error(exc.code)
                self.notice = _error_notice(exc.code)
            else:
                self.notice = None  # the Sign In step shows the code
                if self._open_when_ready:
                    self._open_when_ready = False
                    self.open_url(flow.verification_uri_complete or flow.verification_uri)
            self.touch()
        task = self._logout_task
        if task is not None and task.poll():
            self._logout_task = None
            try:
                reached = bool(task.result().ended_on_server)
            except Exception:  # noqa: BLE001 - the server session could not be ended; forget it here anyway
                if self.link_auth is not None:
                    self.link_auth.store.save({"signedOut": True})
                reached = False
            self.notice = (Notice("INFO", msg("notice.signed-out")) if reached
                           else Notice("WARNING", msg("notice.signed-out-unreached")))
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
            self._remember_error(exc.code)
            self.notice = _error_notice(exc.code)
            self.touch()
            return
        if token:
            assert source is not None
            source.flow = None
            self.refresh_account()
            self.notice = Notice("INFO", msg("notice.signed-in", name=self.user_name or "gta.clothing"))
            if self.want_connected and self.session is not None and self.session.state in (IDLE, STOPPED, WAITING):
                self.session.sign_in()
            self.touch()

    # ---- opening what DCT sends ("Edit in connected app") and the cloth's maps ------------------------

    def texture_busy(self) -> Optional[Msg]:
        """Why another texture cannot be opened right now (a live preview runs or saves), or ``None``."""
        if self.stream.saving:
            return msg("notice.wait-saving")
        if self.stream.active:
            return msg("open.stop-live-first")
        return None

    def _on_open_texture(self, request: HostOpenTexture) -> None:
        """``host.openTexture``: opens the map as an image linked to its cloth and starts its live preview. DCT hears
        ``ok`` as soon as the image exists, ``busy`` while another live preview runs or saves, and ``open-failed``
        when the image could not be made."""
        name = self.document_name(request.binding, request.target, request.name)
        if self.documents is None:
            request.refuse("not-supported")
            return
        if self.texture_busy() is not None:
            request.refuse("busy")
            self.open_notice = Notice("WARNING", msg("open.texture-busy", name=name))
            self.touch()
            return
        document = TextureDocument(dict(request.binding), request.target, name, request.width, request.height,
                                   request.pixels)
        self._open_texture(document, request)

    def _open_texture(self, document: TextureDocument, request: Optional[HostOpenTexture] = None) -> None:
        assert self.documents is not None
        try:
            opened = self.documents.open_texture(document)
        except Exception as exc:  # noqa: BLE001 - DCT hears open-failed, the panel says why
            if request is not None:
                request.refuse("open-failed")
            self.open_notice = Notice("ERROR", msg("open.texture-failed", name=document.name, detail=_detail(exc)))
            self.touch()
            return
        if request is not None:
            request.accept()
        self.open_notice = Notice("INFO", msg("open.opened", name=document.name))
        self._keep_texture = (opened, self._polls)  # after DCT heard the answer (it can take a moment)
        try:
            self.stream.start(opened.source, document.target, opened.width, opened.height, opened.conversion,
                              document=opened.document, warning=opened.warning, binding=document.binding)
        except UserError as exc:
            self.stream.status = Notice("ERROR", exc.message)
        except LinkError as exc:
            self.stream.status = _error_notice(exc.code)
        self.touch()

    def open_map_problem(self, target: str) -> Optional[Msg]:
        """Why the Linked Cloth panel cannot open this map of its cloth right now, or ``None``."""
        if self.documents is None:
            return msg("notice.not-ready")
        if not self.ready:
            return msg("notice.connect-first")
        info = self.card_info()
        if info is None:
            return msg("notice.select-cloth")
        if info.targets and target not in info.targets:
            return msg(f"linked.map-missing.{target}")
        busy = self.texture_busy()
        if busy is not None:
            return busy
        if self.opening_map is not None:
            return msg("open.reading")
        problem = self.feature_problem(settings.FEATURE_SERVICES)
        if problem is not None:
            return msg("open.map-upsell") if problem.key in ("feature.needsUltimate", "feature.needsLicense") else problem
        return None

    def open_map(self, target: str) -> Request:
        """Reads a map of the Linked Cloth panel's cloth from DCT (``texture.read``) and opens it like a map DCT
        sent: as an image linked to the cloth, with its live preview running."""
        session = self.ready_session()
        if target not in protocol.LIVE_TARGETS:
            raise ValueError(f"unknown map {target!r}")
        problem = self.open_map_problem(target)
        if problem is not None:
            raise UserError(problem)
        info = self.card_info()
        assert info is not None
        binding = info.binding if "textureId" in info.binding else None
        request = session.read_texture(target, binding=binding)
        self.opening_map = target
        self.open_notice = None
        request.add_done_callback(self._on_map_read)
        self.touch()
        return request

    def _on_map_read(self, request: Request) -> None:
        self.opening_map = None
        if request.error is not None:
            code = request.error.code
            self.open_notice = (Notice("INFO", msg("open.map-upsell")) if code in ("needs-license", "needs-ultimate")
                                else _error_notice(code))
            self.touch()
            return
        header = request.result().header
        name = self.document_name(header["binding"], header["target"], header.get("name") or "")
        if self.documents is None or self.texture_busy() is not None:
            self.open_notice = Notice("WARNING", msg("open.texture-busy", name=name))  # started meanwhile
            self.touch()
            return
        self._open_texture(TextureDocument(dict(header["binding"]), header["target"], name, header["width"],
                                           header["height"], request.result().payload))

    def _on_open_model(self, request: HostOpenModel) -> None:
        """``host.openModel``: writes the files into the add-on's folder and imports them with Sollumz in the next
        timer step, after DCT heard ``ok``. ``dependency-missing`` without a usable Sollumz, ``busy`` while a model
        is pushed, saved or imported, ``open-failed`` when the files cannot be written."""
        model_file = next((name for name, _ in request.files if name.lower().endswith(bundle.MODEL_SUFFIX)), "")
        name = model_file.split(".", 1)[0] or request.name
        if self.documents is None:
            request.refuse("not-supported")
            return
        problem = self.documents.model_problem()
        if problem is not None:
            request.refuse("dependency-missing")
            self.model.open_notice = Notice("WARNING", msg("open.model-needs-sollumz", name=name, problem=problem))
            self.touch()
            return
        if self._model_import is not None or self.model.pushing or self.model.busy is not None:
            request.refuse("busy")
            self.model.open_notice = Notice("WARNING", msg("open.model-busy", name=name))
            self.touch()
            return
        try:
            folder = self._write_model_files(name, model_file, request.files)
        except (OSError, ValueError) as exc:
            request.refuse("open-failed")
            self.model.open_notice = Notice("ERROR", msg("open.model-failed", name=name, detail=_detail(exc)))
            self.touch()
            return
        self._model_import = _ModelImport(request, folder, model_file, dict(request.binding), name, self._polls)
        request.accept()  # the files are in place and the import runs in the next step
        self.model.open_notice = Notice("INFO", msg("open.model-importing", name=name))
        self.touch()

    def _write_model_files(self, name: str, model_file: str, files: List[Any]) -> pathlib.Path:
        """``<data folder>/opened-models/<model>/<model>.ydd.xml`` with its textures in ``<model>/`` beside it, the
        folder Sollumz reads them from. Every name is a bare file name and is joined inside its folder only."""
        assert self.data_dir is not None
        base = self.data_dir / MODELS_FOLDER
        base.mkdir(parents=True, exist_ok=True)
        folder = _inside(base, name)
        if folder.exists():
            shutil.rmtree(folder)
        folder.mkdir()
        self._model_folders.add(folder)
        try:
            textures = _inside(folder, name)
            for file_name, data in files:
                if file_name == model_file:
                    target = _inside(folder, file_name)
                else:
                    textures.mkdir(exist_ok=True)
                    target = _inside(textures, file_name)
                with open(target, "xb") as handle:
                    handle.write(data)
        except BaseException:
            self._remove_model_folder(folder)
            raise
        return folder

    def _finish_opening(self) -> None:
        """Work that waits until DCT heard the answer to its request: importing a model, keeping a texture's
        pixels with the Blender file."""
        keep = self._keep_texture
        if keep is not None and keep[1] < self._polls:
            self._keep_texture = None
            try:
                assert self.documents is not None
                self.documents.keep_texture(keep[0])
            except Exception:  # noqa: BLE001 - the image stays usable; only saving it with the file is up to the user
                traceback.print_exc()
        job = self._model_import
        if job is None or job.poll_number >= self._polls:
            return
        self._model_import = None
        try:
            assert self.documents is not None
            imported = self.documents.import_model(job.folder, job.model_file, job.binding)
        except Exception as exc:  # noqa: BLE001 - DCT already heard ok; the panel says what went wrong
            self._remove_model_folder(job.folder)
            self.model.open_notice = Notice("ERROR", msg("open.model-failed", name=job.name, detail=_detail(exc)))
            self.touch()
            return
        self.model.open_notice = Notice("INFO", msg("open.opened", name=imported.name))
        try:
            imported.push()
        except UserError as exc:
            self.model.status = Notice("ERROR", exc.message)
        except LinkError as exc:
            self.model.status = _error_notice(exc.code)
        self.touch()

    def release_model_files(self) -> None:
        """Removes the files of opened models (Blender keeps what it imported), except an import still to run."""
        keep = self._model_import.folder if self._model_import is not None else None
        for folder in list(self._model_folders):
            if folder != keep:
                self._remove_model_folder(folder)

    def _remove_model_folder(self, folder: pathlib.Path) -> None:
        self._model_folders.discard(folder)
        shutil.rmtree(folder, ignore_errors=True)

    def _remove_stale_model_files(self) -> None:
        """Files of opened models an earlier session left behind (Blender closed before the model was discarded)."""
        base = self.data_dir / MODELS_FOLDER if self.data_dir is not None else None
        if base is None or not base.is_dir():
            return
        cutoff = time.time() - self.STALE_MODEL_FILES_SECONDS
        for entry in base.iterdir():
            try:
                if entry.is_dir() and not entry.is_symlink() and entry.stat().st_mtime < cutoff:
                    shutil.rmtree(entry, ignore_errors=True)
            except OSError:
                continue  # another Blender may be using it; it goes with the next start

    # ---- the cloth's picture -------------------------------------------------------------------------

    def _refresh_thumbnail(self) -> None:
        """Asks DCT for the picture of the Linked Cloth panel's cloth whenever that cloth or variation changes."""
        info = self.card_info() if self.ready else None
        key = None
        if info is not None:
            key = (info.binding.get("clothId", "").lower(), info.binding.get("textureId", "").lower())
        if key == self._thumbnail_key:
            return
        pending = self._thumbnail_request
        if pending is not None and not pending.done:
            return  # asked again once DCT answered
        self._thumbnail_key = key
        self._set_thumbnail(None)
        if info is None or self.session is None or self.feature_problem(settings.FEATURE_SERVICES) is not None:
            return
        binding = info.binding if "textureId" in info.binding else None
        try:
            request = self.session.request_thumbnail(self.THUMBNAIL_SIZE, binding=binding)
        except (LinkError, ValueError):
            return  # no picture; the panel shows the cloth without one
        self._thumbnail_request = request
        request.add_done_callback(lambda done, key=key: self._on_thumbnail(done, key))

    def _on_thumbnail(self, request: Request, key: tuple) -> None:
        if key != self._thumbnail_key or request.error is not None:
            return
        result = request.result()
        self._set_thumbnail(result if getattr(result, "ok", False) else None)

    def _set_thumbnail(self, thumbnail: Optional[Thumbnail]) -> None:
        if thumbnail is None and self.thumbnail is None:
            return
        self.thumbnail = thumbnail
        if self.on_thumbnail is not None:
            try:
                self.on_thumbnail(thumbnail)
            except Exception:  # noqa: BLE001 - a picture must never stop the link
                traceback.print_exc()
        self.touch()

    # ---- session events ------------------------------------------------------------------------------

    def _on_state(self, state: str) -> None:
        self.state = state
        if state == HELLO:
            self.dct_seen = True
        elif state == WAITING and not self.dct_seen:
            self.search_failed = True
        if state != SIGNING_IN:
            self.sign_in_prompt = None
        self.touch()

    def _forget_lost_connection_notes(self) -> None:
        """The status explains the connection now; the panels' "connection lost" notes would only repeat it."""
        lost = settings.describe_close_reason("disconnected")
        for part in (self.stream, self.model):
            if part.status is not None and part.status.message == lost:
                part.status = None

    def _on_ready(self, welcome: Dict[str, Any]) -> None:
        self._forget_lost_connection_notes()
        self.signed_out = False
        self.dct_signed_out = False
        self.dct_disconnected = False
        self.sign_in_status = None
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
            self._remember_cloth(self.focused)
            self.touch()

    def _on_sign_in(self, prompt: SignInPrompt) -> None:
        self.sign_in_prompt = prompt
        if prompt.assisted_by_dct is True:
            self.sign_in_status = Notice("INFO", msg("setup.sign-in.approved"))
        elif prompt.assisted_by_dct is False:
            self.sign_in_status = Notice("WARNING", msg("setup.sign-in.declined"))
        else:
            self.sign_in_status = Notice("INFO", msg("setup.sign-in.asked"))
        self.touch()

    def _on_signed_out(self) -> None:
        self.signed_out = True
        self.user_name = None
        self.notice = None  # the Sign In step says it
        self.touch()

    def _on_dct_signed_out(self) -> None:
        self.dct_signed_out = True
        self._forget_lost_connection_notes()
        self.touch()

    def _on_dct_disconnected(self) -> None:
        """The user disconnected this app in Durty Cloth Tool. The session stopped and nothing connects again by
        itself (not even Connect Automatically): only the user's Connect or Sign In does."""
        self.want_connected = False
        self.dct_disconnected = True
        self.dct_signed_out = False
        self.notice = None  # the status says it, with Connect
        self._forget_lost_connection_notes()
        self.touch()

    def _on_selection(self, message: Dict[str, Any]) -> None:
        self.focused = message.get("focused")
        self._remember_cloth(self.focused)
        self.touch()

    def _on_project(self, message: Dict[str, Any]) -> None:
        self.project = message.get("project")
        if self.project is None:
            self.focused = None
        self._clothes.clear()  # another project: its clothes are other ones
        self._remember_cloth(self.focused)
        self.touch()

    def _on_incompatible(self, message: Dict[str, Any]) -> None:
        self.incompatible = message
        self._remember_error(message.get("code"))
        self.touch()

    def _on_error(self, error: LinkError) -> None:
        code = error.code
        self._remember_error(code)
        if code == "dct-signed-out":
            self.dct_signed_out = True
            self.touch()
            return
        if code in settings.SIGNED_OUT_CODES:
            self.user_name = None
        if code in ("token-invalid", "signed-out"):
            return  # the session refreshes and retries by itself; signed-out has its own event
        if self.incompatible is not None and code == self.incompatible.get("code"):
            return  # the status explains it, with what to update
        retrying = ("disconnected", "busy", "rate-limited", "assertion-invalid", "authentication-failed",
                    "untrusted-endpoint")  # the session tries again by itself
        level = "WARNING" if code in retrying else "ERROR"
        self.notice = Notice(level, settings.describe_error(code))
        self.touch()

    def _on_disconnected(self, code: Optional[int], reason: str) -> None:
        self.project = None
        self.focused = None
        self.opening_map = None
        self._keep_texture = None
        self._thumbnail_key = None
        self._thumbnail_request = None
        self._set_thumbnail(None)
        self.stream.on_disconnected()
        self.model.on_disconnected()
        self.touch()


_STATE_KEYS = frozenset(f"state.{s}" for s in ("idle", "connecting", "waiting", "hello", "signing-in", "authenticating"))

__all__ = [
    "DocumentHost",
    "FocusInfo",
    "ImportedModel",
    "LinkController",
    "ModelPush",
    "Notice",
    "OpenedImage",
    "TextureDocument",
    "TokenSource",
    "TextureStream",
    "binding_of",
    "same_binding",
]
