# SPDX-License-Identifier: GPL-3.0-or-later
"""The add-on's link flows against a fake Durty Cloth Tool and a fake gta.clothing, without Blender: connecting
and both ways of signing in, a disconnect in Durty Cloth Tool, a remembered sign-out, renewing the sign-in on
connect, texture streaming (byte and float images, with the vertical flip end to end), capture scheduling, model
pushes, automatic pushes, signing out, and protocol 2: Sign In through Durty Cloth Tool first, textures and models
Durty Cloth Tool sends, the maps and picture of the linked cloth. Everything is driven by polling, as Blender's timer
does."""

from __future__ import annotations

import json
import os
import pathlib
import time
from typing import Callable, Dict, List, Optional

import numpy as np
import pytest

from durty_cloth_tool_link import link, pixels, settings, strings
from durty_cloth_tool_link.dct_link import auth, tokens
from durty_cloth_tool_link.dct_link.session import READY, STOPPED, LinkError
from tests.support.fake_dct import BINDING, FakeDct
from tests.support.fake_link_api import FakeLinkApi


class Stores:
    """In-memory secret stores that outlive one controller (like the real ones outlive Blender)."""

    def __init__(self) -> None:
        self.stores: Dict[str, tokens.MemorySecretStore] = {}

    def __call__(self, name: str, folder: pathlib.Path, install_id: str) -> tokens.MemorySecretStore:
        return self.stores.setdefault(name, tokens.MemorySecretStore())


def make_controller(tmp_path, dct, api, stores, *, online: Callable[[], bool] = lambda: True,
                    opened: Optional[List[str]] = None) -> link.LinkController:
    ctrl = link.LinkController(lambda: tmp_path / "user", "4.5.9", online=online, device_name=lambda: "TEST-PC",
                               secret_store=stores, open_url=(opened.append if opened is not None else lambda url: None))
    ctrl.port_override = dct.port
    ctrl.auth_base_url = api.base_url
    return ctrl


def drive(ctrl: link.LinkController, until: Callable[[], bool], timeout: float = 15.0) -> None:
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        ctrl.poll()
        if until():
            return
        time.sleep(0.005)
    raise AssertionError(f"timed out in state {ctrl.state}; notice: {ctrl.notice}")


@pytest.fixture
def dct():
    with FakeDct() as server:
        yield server


@pytest.fixture
def api():
    with FakeLinkApi() as server:
        yield server


@pytest.fixture
def stores():
    return Stores()


def ready_controller(tmp_path, dct, api, stores) -> link.LinkController:
    dct.on_assist = api.approve  # DCT approves the device sign-in, as the signed-in DCT does
    ctrl = make_controller(tmp_path, dct, api, stores)
    ctrl.connect()
    drive(ctrl, lambda: ctrl.ready and ctrl.focused is not None)
    return ctrl


def test_sign_in_through_dct(tmp_path, dct, api, stores):
    ctrl = ready_controller(tmp_path, dct, api, stores)
    assert ctrl.account_name == "Durty" and ctrl.user_name == "Durty"
    assert ctrl.project == {"name": "FS Studio Clothing"}
    info = ctrl.focus_info()
    assert info[:6] == ("jbib_003_u", "A", "jbib_diff_003_a_uni", 2048, 2048, ("diffuse", "normal", "specular"))
    assert info.binding == BINDING and not info.linked and info.drawable_type is None  # DCT sent no details
    assert ctrl.focus_label() == "jbib_003_u A"
    assert ctrl.chip() == "connected" and not ctrl.setup_needed
    assert len(dct.assisted_codes) == 1 and len(dct.assertions_seen) == 1
    assert "POST /link/api/auth/device" in api.paths() and "POST /link/api/assertions" in api.paths()
    device_request = next(r for r in api.requests if r["path"] == "/link/api/auth/device")
    assert device_request["body"]["deviceName"] == "TEST-PC"
    assert device_request["body"]["channel"] == settings.CHANNEL
    expected_header = f"blender/{settings.VERSION} (protocol 2.0; channel {settings.CHANNEL})"
    assert device_request["headers"]["x-dct-link-client"] == expected_header
    # Access and refresh tokens never go to DCT; only the connection-bound assertion does.
    sent_to_dct = json.dumps(dct.received)
    stored = json.loads(stores.stores["tokens"].load().decode())
    for value in stored.values():
        if isinstance(value, str) and len(value) > 20:
            assert value not in sent_to_dct
    hello = dct.received[0]
    assert hello["plugin"] == {"kind": "blender", "version": settings.VERSION, "channel": settings.CHANNEL}
    assert hello["host"] == {"name": "Blender", "version": "4.5.9"}
    # The same random installation id gta.clothing sees with the sign-in.
    assert hello["installId"] == ctrl.install_id == device_request["body"]["installId"]


def test_the_reported_channel_is_the_build_channel():
    assert settings.channel_of_version("0.1.0") == "release"
    assert settings.channel_of_version("0.2.0-experimental.3") == "experimental"
    assert settings.CHANNEL == settings.channel_of_version(settings.VERSION)


def test_a_new_connection_reuses_the_sign_in(tmp_path, dct, api, stores):
    first = ready_controller(tmp_path, dct, api, stores)
    first.disconnect()
    second = make_controller(tmp_path, dct, api, stores)
    second.prepare()
    assert second.user_name == "Durty"
    second.connect()
    drive(second, lambda: second.ready)
    assert len(dct.assisted_codes) == 1  # no new sign-in
    assert len(dct.assertions_seen) == 2  # a fresh assertion for the new connection
    second.disconnect()


def test_an_expired_sign_in_is_renewed_when_connecting(tmp_path, dct, api, stores):
    first = ready_controller(tmp_path, dct, api, stores)
    first.disconnect()
    stored = json.loads(stores.stores["tokens"].load().decode())
    stored["accessExpiresAt"] = 0  # the 15-minute access token ran out
    stores.stores["tokens"].save(json.dumps(stored).encode())
    second = make_controller(tmp_path, dct, api, stores)
    second.connect()
    drive(second, lambda: second.ready)
    renewals = [r for r in api.requests
                if r["path"] == "/link/api/auth/token" and (r["body"] or {}).get("grantType") == "refresh_token"]
    assert len(renewals) == 1 and api.paths()[-1] == "POST /link/api/assertions"
    second.disconnect()


def test_sign_in_with_the_browser_before_connecting(tmp_path, dct, api, stores):
    opened: List[str] = []
    ctrl = make_controller(tmp_path, dct, api, stores, opened=opened)
    ctrl.start_sign_in()
    drive(ctrl, lambda: bool(opened))  # the browser opens once gta.clothing answered, without blocking
    code, link_url = ctrl.active_sign_in()
    assert opened == [link_url] and link_url.startswith(api.base_url + "/account/link/?code=")
    api.approve(code)
    drive(ctrl, lambda: ctrl.user_name == "Durty")
    ctrl.connect()
    drive(ctrl, lambda: ctrl.ready)
    assert dct.assisted_codes == []  # already signed in: DCT was not asked


def test_setup_finds_durty_cloth_tool_then_signs_in_there(tmp_path, dct, api, stores):
    ctrl = make_controller(tmp_path, dct, api, stores)
    ctrl.prepare()
    assert ctrl.setup_steps() == (False, False) and ctrl.setup_needed
    ctrl.connect()  # not signed in: the session asks Durty Cloth Tool to approve a sign-in
    drive(ctrl, lambda: ctrl.sign_in_prompt is not None and bool(dct.assisted_codes))
    assert ctrl.setup_steps() == (True, False) and ctrl.chip() == "action"
    assert ctrl.sign_in_status.message.key in ("setup.sign-in.asked", "setup.sign-in.approved")
    api.approve(dct.assisted_codes[0])
    drive(ctrl, lambda: ctrl.ready)
    assert ctrl.setup_steps() == (True, True) and not ctrl.setup_needed


def test_a_disconnect_in_durty_cloth_tool_waits_for_the_user(tmp_path, dct, api, stores):
    ctrl = ready_controller(tmp_path, dct, api, stores)
    start(ctrl, ArrayImage(16, 16))
    drive(ctrl, lambda: len(dct.frames) == 1)
    dct.connections_ready[-1].kick("disconnected")  # the user disconnected Blender under Connected apps
    drive(ctrl, lambda: ctrl.dct_disconnected and ctrl.state == STOPPED)
    assert not ctrl.stream.active and ctrl.notice is None and not ctrl.want_connected
    assert ctrl.stream.status is None  # the status explains it; no "connection lost" note under Live Preview
    assert strings.english(ctrl.status()) == "Disconnected in Durty Cloth Tool" and ctrl.chip() == "offline"
    connections = dct.connections
    end = time.monotonic() + 1.5
    while time.monotonic() < end:  # nothing connects again by itself
        ctrl.poll()
        time.sleep(0.01)
    assert dct.connections == connections and ctrl.state == STOPPED
    ctrl.connect()  # the Connect button
    drive(ctrl, lambda: ctrl.ready)
    assert not ctrl.dct_disconnected and ctrl.chip() == "connected"


def test_a_disconnect_before_the_welcome_does_not_switch_the_add_on_off(tmp_path, dct, api, stores):
    """Only a Durty Cloth Tool that welcomed the add-on can disconnect it; before that the answer proves nothing (a
    program on a link port could send it), so the add-on keeps trying and connects."""
    first = ready_controller(tmp_path, dct, api, stores)
    first.disconnect()
    dct.auth_error_codes = ["disconnected"]
    second = make_controller(tmp_path, dct, api, stores)
    second.connect()
    drive(second, lambda: second.ready)
    assert not second.dct_disconnected and "untrusted-endpoint" in second.recent_errors


def test_a_browser_sign_in_after_a_sign_out_connects(tmp_path, dct, api, stores):
    """Signing out ends the connection; signing in again in the browser connects again, as through DCT."""
    opened: List[str] = []
    ctrl = ready_controller(tmp_path, dct, api, stores)
    ctrl.open_url = opened.append
    ctrl.sign_out()
    drive(ctrl, lambda: api.logouts == 1 and ctrl.state == STOPPED)
    ctrl.start_sign_in()
    drive(ctrl, lambda: bool(opened))
    api.approve(ctrl.active_sign_in()[0])
    drive(ctrl, lambda: ctrl.ready)
    assert ctrl.user_name == "Durty" and not ctrl.signed_out


def test_a_sign_out_is_remembered_until_the_user_signs_in(tmp_path, dct, api, stores):
    ctrl = ready_controller(tmp_path, dct, api, stores)
    ctrl.sign_out()
    drive(ctrl, lambda: api.logouts == 1)
    assert ctrl.user_name is None and ctrl.signed_out
    devices = len([r for r in api.requests if r["path"] == "/link/api/auth/device"])
    again = make_controller(tmp_path, dct, api, stores)
    again.prepare()
    assert again.signed_out
    again.connect()  # Connect Automatically at the next start
    drive(again, lambda: again.state == STOPPED)
    assert strings.english(again.status()) == "Signed out" and again.chip() == "action"
    assert len([r for r in api.requests if r["path"] == "/link/api/auth/device"]) == devices  # nothing started
    dct.on_assist = api.approve
    again.sign_in()
    drive(again, lambda: again.ready)
    assert not again.signed_out


class ArrayImage:
    """A Blender image stand-in: RGBA8 pixels top to bottom, served bottom-up as floats like Image.pixels."""

    def __init__(self, width: int, height: int, rgba: Optional[np.ndarray] = None) -> None:
        if rgba is None:
            rgba = np.random.default_rng(3).integers(0, 256, size=(height, width, 4), dtype=np.uint8)
        self.rgba = rgba
        self.dirty = False
        self.stroke = False
        self.removed = False
        self.reads = 0

    def problem(self) -> Optional[strings.Msg]:
        return strings.msg("live.image-removed") if self.removed else None

    def is_dirty(self) -> bool:
        return self.dirty

    def stroke_active(self) -> bool:
        return self.stroke

    def read_into(self, buffer: np.ndarray) -> None:
        self.reads += 1
        buffer[:] = (self.rgba[::-1].astype(np.float32) / np.float32(255)).reshape(-1)


def canvas(dct: FakeDct) -> bytes:
    connection = dct.connections_ready[-1]
    (lease,) = connection.leases.values()
    return bytes(lease["canvas"])


def start(ctrl: link.LinkController, image, target: str = "diffuse", conversion: pixels.Conversion = pixels.Conversion()):
    height, width = image.rgba.shape[:2] if hasattr(image, "rgba") else image.straight.shape[:2]
    ctrl.stream.start(image, target, width, height, conversion, document="jacket")


def test_texture_streaming_end_to_end(tmp_path, dct, api, stores):
    ctrl = ready_controller(tmp_path, dct, api, stores)
    image = ArrayImage(256, 128)
    start(ctrl, image)
    drive(ctrl, lambda: len(dct.frames) == 1 and ctrl.stream.live_state == "attached")
    assert dct.frames[0][2] == {"x": 0, "y": 0, "w": 256, "h": 128}
    assert canvas(dct) == image.rgba.tobytes()  # rows arrive top to bottom

    image.rgba[100:110, 200:204] = [255, 0, 0, 255]
    image.dirty = True
    drive(ctrl, lambda: len(dct.frames) == 2)
    assert dct.frames[1][2] == {"x": 192, "y": 64, "w": 64, "h": 64}
    assert canvas(dct) == image.rgba.tobytes()

    ctrl.stream.save("replace")
    drive(ctrl, lambda: not ctrl.stream.saving)
    assert ctrl.stream.status.text == "Saved to jbib_003_u A. You can undo it in History."
    assert not ctrl.stream.unsaved
    assert dct.saves[-1][2] == "replace" and dct.saves[-1][3] == image.rgba.tobytes()

    image.rgba[0, 0] = [1, 2, 3, 4]
    ctrl.stream.save("newVariation")  # sends the newest pixels first
    drive(ctrl, lambda: not ctrl.stream.saving)
    assert ctrl.stream.status.text == "Saved as a new variation of jbib_003_u A."
    assert dct.saves[-1][3] == image.rgba.tobytes()

    holder, buffers = ctrl.stream._pixel_source, ctrl.stream.buffers
    ctrl.stream.discard()
    assert holder.buffers is None and buffers.nbytes == 0  # freed now, not when DCT confirms
    drive(ctrl, lambda: not dct.connections_ready[-1].leases)
    assert dct.discards and not ctrl.stream.active


def test_separate_changes_are_sent_as_separate_rectangles(tmp_path, dct, api, stores):
    ctrl = ready_controller(tmp_path, dct, api, stores)
    image = ArrayImage(256, 256)
    start(ctrl, image)
    drive(ctrl, lambda: len(dct.frames) == 1)
    image.rgba[0:2, 0:2] = 1
    image.rgba[250:252, 250:252] = 2
    image.dirty = True
    drive(ctrl, lambda: len(dct.frames) == 3)
    assert sorted((f[2]["x"], f[2]["y"], f[2]["w"], f[2]["h"]) for f in dct.frames[1:]) == [
        (0, 0, 64, 64), (192, 192, 64, 64)]  # two small frames, not one frame spanning both
    assert canvas(dct) == image.rgba.tobytes()


def test_many_changed_areas_are_merged_into_a_few_frames(tmp_path, dct, api, stores):
    ctrl = make_controller(tmp_path, dct, api, stores)
    marked = []

    class Surface:
        closed = False

        def mark_dirty(self, rect=None):
            marked.append(rect)

    ctrl.stream.surface = Surface()
    rects = [(128 * i, 128 * i, 64, 64) for i in range(8)]  # eight distant areas changed in one step
    ctrl.stream._mark(rects)
    assert len(marked) == ctrl.stream.RECTS_PER_STEP
    for x, y, w, h in rects:
        assert any(mx <= x and my <= y and x + w <= mx + mw and y + h <= my + mh for mx, my, mw, mh in marked)


def test_a_live_texture_that_closes_before_its_answer_is_handled(tmp_path, dct, api, stores):
    ctrl = make_controller(tmp_path, dct, api, stores)

    class Surface:
        closed, close_reason = True, "disconnected"

        def close(self):
            raise LinkError("closed", "the live surface is closed")

        def mark_dirty(self, rect=None):
            raise LinkError("closed", "the live surface is closed")

    class Answer:
        error = None

        def result(self):
            return Surface()

    answer = Answer()
    ctrl.stream.opening = answer
    ctrl.stream._on_opened(answer)  # closed meanwhile: reported, not raised
    assert ctrl.stream.surface is None and ctrl.stream.status.level == "WARNING"
    Surface.closed = False
    ctrl.stream._on_opened(Answer())  # an answer nobody waits for any more: closed quietly
    assert ctrl.stream.surface is None


def test_captures_wait_for_the_paint_stroke_to_end(tmp_path, dct, api, stores):
    ctrl = ready_controller(tmp_path, dct, api, stores)
    image = ArrayImage(64, 64)
    start(ctrl, image)
    drive(ctrl, lambda: len(dct.frames) == 1)
    reads = image.reads
    image.stroke = True
    image.dirty = True
    image.rgba[0:4, 0:4] = 9
    end = time.monotonic() + 1.5
    while time.monotonic() < end:
        ctrl.poll()
        time.sleep(0.01)
    assert image.reads == reads and len(dct.frames) == 1  # nothing read while the stroke runs
    image.stroke = False
    drive(ctrl, lambda: len(dct.frames) == 2)
    assert image.reads == reads + 1 and canvas(dct) == image.rgba.tobytes()


def test_idle_checks_back_off_while_nothing_changes(tmp_path, dct, api, stores):
    ctrl = ready_controller(tmp_path, dct, api, stores)
    image = ArrayImage(32, 32)
    start(ctrl, image)
    drive(ctrl, lambda: len(dct.frames) == 1)
    stream = ctrl.stream
    image.dirty = True

    def capture() -> float:
        stream.next_check = 0.0
        now = time.monotonic()
        stream.tick(now)  # starts a capture
        while stream.buffers.busy:
            stream.tick(now)
        return round(stream.next_check - now, 3)

    assert [capture() for _ in range(7)] == [1.0, 2.0, 4.0, 8.0, 16.0, 30.0, 30.0]
    image.rgba[0, 0] = 1
    assert capture() == stream.AFTER_CHANGE
    image.strokes_known = lambda: False  # a Blender that cannot report strokes: wait longer after changes
    image.rgba[0, 0] = 2
    assert capture() == stream.AFTER_CHANGE_UNSEEN


class FloatImage:
    """A painted float image: premultiplied linear floats, rows bottom up, as Image.pixels returns them."""

    def __init__(self, width: int, height: int) -> None:
        rng = np.random.default_rng(5)
        self.straight = rng.random((height, width, 4), dtype=np.float32)
        self.straight[..., 3] = np.clip(self.straight[..., 3], 0.25, 1.0)
        self.dirty = False

    def problem(self) -> Optional[strings.Msg]:
        return None

    def is_dirty(self) -> bool:
        return self.dirty

    def stroke_active(self) -> bool:
        return False

    def read_into(self, buffer: np.ndarray) -> None:
        premultiplied = self.straight.copy()
        premultiplied[..., :3] *= premultiplied[..., 3:4]
        buffer[:] = premultiplied[::-1].reshape(-1)

    def expected(self) -> np.ndarray:
        rgba = np.empty(self.straight.shape, np.uint8)
        rgba[..., :3] = np.floor(pixels.srgb_reference(self.straight[..., :3]) * 255 + 0.5)
        rgba[..., 3] = np.floor(self.straight[..., 3] * 255 + 0.5)
        return rgba


def test_painted_float_images_arrive_as_straight_srgb(tmp_path, dct, api, stores):
    ctrl = ready_controller(tmp_path, dct, api, stores)
    image = FloatImage(96, 80)
    plan = pixels.colour_plan("diffuse", 4, True, "Linear Rec.709", False)
    start(ctrl, image, conversion=plan.conversion)
    drive(ctrl, lambda: len(dct.frames) == 1)
    received = np.frombuffer(canvas(dct), np.uint8).reshape(80, 96, 4).astype(int)
    assert np.abs(received - image.expected().astype(int)).max() <= 1
    image.straight[10:12, 5:7] = [1.0, 0.0, 0.0, 0.5]  # half-transparent red, stored premultiplied
    image.dirty = True
    drive(ctrl, lambda: len(dct.frames) == 2)
    received = np.frombuffer(canvas(dct), np.uint8).reshape(80, 96, 4)
    assert received[10, 5].tolist() == [255, 0, 0, 128]


def test_streaming_refuses_what_dct_would_refuse(tmp_path, dct, api, stores):
    ctrl = ready_controller(tmp_path, dct, api, stores)
    with pytest.raises(ValueError, match="4096"):
        ctrl.stream.start(ArrayImage(8, 8), "diffuse", 4097, 8)
    image = ArrayImage(8, 8)
    start(ctrl, image, target="normal")
    drive(ctrl, lambda: ctrl.stream.is_open)
    with pytest.raises(ValueError, match="Diffuse"):
        ctrl.stream.save("newVariation")
    image.removed = True
    drive(ctrl, lambda: not ctrl.stream.active)
    assert ctrl.stream.status.text == "The image was removed."


class Export:
    """Writes what Sollumz writes; ``warnings`` stands for Sollumz opening its Info log."""

    def __init__(self, texture: bytes = b"DDS 1", warnings: bool = False) -> None:
        self.texture, self.warnings = texture, warnings

    def __call__(self, folder: str):
        base = pathlib.Path(folder)
        (base / "jbib_003_u.ydd.xml").write_bytes(b"<DrawableDictionary />")
        (base / "jbib_003_u").mkdir()
        (base / "jbib_003_u" / "jbib_diff_003_a_uni.dds").write_bytes(self.texture)
        return self


def test_model_push_save_and_discard(tmp_path, dct, api, stores):
    ctrl = ready_controller(tmp_path, dct, api, stores)
    ctrl.model.push(Export(), "jbib_003_u")
    drive(ctrl, lambda: ctrl.model.lease is not None)
    header, files = dct.pushes[0]
    assert header["format"] == "ydd-xml" and "lease" not in header
    assert files == {"jbib_003_u.ydd.xml": b"<DrawableDictionary />", "jbib_diff_003_a_uni.dds": b"DDS 1"}

    ctrl.model.push(Export(b"DDS 2"), "jbib_003_u")
    drive(ctrl, lambda: len(dct.pushes) == 2 and not ctrl.model.pushing)
    assert dct.pushes[1][0]["lease"] == ctrl.model.lease
    assert ctrl.model.revision == 2

    ctrl.model.save()
    drive(ctrl, lambda: ctrl.model.busy is None)
    assert ctrl.model.status.text == "Saved the model to the cloth. You can undo it in History."
    ctrl.model.discard()
    drive(ctrl, lambda: ctrl.model.lease is None)
    assert ctrl.model.status.text == "Discarded the model in Durty Cloth Tool."

    with pytest.raises(ValueError, match="did not export a model"):
        ctrl.model.push(lambda folder: None, "nothing")
    assert len(dct.pushes) == 2


def test_saving_waits_for_the_newest_push_and_retries_while_dct_is_busy(tmp_path, dct, api, stores):
    ctrl = ready_controller(tmp_path, dct, api, stores)
    model = ctrl.model
    model.SAVE_RETRY_DELAY = 0.05
    model.push(Export(), "jbib_003_u")
    with pytest.raises(ValueError, match="Push a model first"):
        model.save()
    drive(ctrl, lambda: model.lease is not None and not model.pushing)
    model.push(Export(b"DDS 2"), "jbib_003_u")
    assert model.save_blocker.key == "model.block.pushing"  # saving now would store the model shown before it
    drive(ctrl, lambda: not model.pushing)
    model.due_at = time.monotonic() + 30  # an automatic push is about to run
    with pytest.raises(ValueError, match="about to be pushed"):
        model.save()
    model.due_at = None

    dct.save_busy = 2  # DCT is still converting: it answers busy, the add-on asks again
    model.save()
    drive(ctrl, lambda: model.busy is None)
    assert model.status.text.startswith("Saved the model to the cloth") and dct.busy_saves == 2 and len(dct.model_saves) == 1

    model.SAVE_RETRIES = 1
    dct.save_busy = 5
    model.save()
    drive(ctrl, lambda: model.busy is None)
    assert model.status.level == "WARNING" and "Save again" in model.status.text


def test_automatic_push_after_changes_and_its_pause_after_warnings(tmp_path, dct, api, stores):
    ctrl = ready_controller(tmp_path, dct, api, stores)
    exports = [Export(), Export(warnings=True)]
    ctrl.model.on_auto_push = lambda: ctrl.model.push(exports.pop(0), "jbib_003_u", automatic=True)
    enabled = {"on": True}
    ctrl.model.auto_enabled = lambda: enabled["on"]
    ctrl.model.delay = 0.5
    ctrl.model.schedule(time.monotonic())
    ctrl.poll()
    assert dct.pushes == []  # nothing pushed yet: automatic pushes start after the first push
    ctrl.model.push(Export(), "jbib_003_u")
    drive(ctrl, lambda: ctrl.model.lease is not None)
    ctrl.model.schedule(time.monotonic())
    ctrl.model.schedule(time.monotonic())  # a burst of changes gives one push
    drive(ctrl, lambda: len(dct.pushes) == 2 and not ctrl.model.pushing)
    time.sleep(0.6)
    ctrl.poll()
    assert len(dct.pushes) == 2

    enabled["on"] = False  # switched off (or undone) in the scene: a scheduled push is dropped
    ctrl.model.due_at = time.monotonic()
    ctrl.poll()
    assert len(dct.pushes) == 2 and ctrl.model.due_at is None
    enabled["on"] = True

    ctrl.model.schedule(time.monotonic())  # this one logs warnings: automatic pushes pause
    drive(ctrl, lambda: len(dct.pushes) == 3 and not ctrl.model.pushing and ctrl.model.paused)
    assert "paused" in ctrl.model.note.text
    ctrl.model.schedule(time.monotonic())
    assert ctrl.model.due_at is None
    ctrl.model.push(Export(), "jbib_003_u")  # pushing by hand resumes them
    drive(ctrl, lambda: len(dct.pushes) == 4 and not ctrl.model.pushing)
    assert not ctrl.model.paused


def test_sign_out(tmp_path, dct, api, stores):
    ctrl = ready_controller(tmp_path, dct, api, stores)
    ctrl.sign_out()
    drive(ctrl, lambda: api.logouts == 1 and ctrl.state == STOPPED and ctrl._logout_task is None)
    assert ctrl.user_name is None and ctrl.notice.text == "Signed out."
    assert json.loads(stores.stores["tokens"].load().decode()) == {"signedOut": True}


def test_a_sign_out_gta_clothing_did_not_hear_about_says_so(tmp_path, dct, api, stores):
    ctrl = ready_controller(tmp_path, dct, api, stores)
    api.logout_failure = 503
    ctrl.sign_out()
    drive(ctrl, lambda: ctrl._logout_task is None)
    assert ctrl.notice.level == "WARNING"
    assert ctrl.notice.text.startswith("Signed out on this computer; gta.clothing could not be reached.")
    assert json.loads(stores.stores["tokens"].load().decode()) == {"signedOut": True}


def test_nothing_goes_to_gta_clothing_without_online_access(tmp_path, dct, api, stores):
    ctrl = make_controller(tmp_path, dct, api, stores, online=lambda: False)
    with pytest.raises(auth.AuthError) as error:
        ctrl.start_sign_in()
    assert error.value.code == "offline"
    ctrl.connect()
    drive(ctrl, lambda: ctrl.state == STOPPED)
    assert ctrl.notice.message == settings.describe_error("offline") and ctrl.chip() == "problem"
    assert api.requests == []


def test_pausing_holds_changes_until_resumed(tmp_path, dct, api, stores):
    ctrl = ready_controller(tmp_path, dct, api, stores)
    image = ArrayImage(64, 64)
    start(ctrl, image)
    drive(ctrl, lambda: len(dct.frames) == 1)
    ctrl.stream.pause()
    image.rgba[0:4, 0:4] = 5
    image.dirty = True
    ctrl.stream.send_now()
    end = time.monotonic() + 1.0
    while time.monotonic() < end:
        ctrl.poll()
        time.sleep(0.01)
    assert len(dct.frames) == 1  # nothing is sent while paused
    ctrl.stream.resume()
    drive(ctrl, lambda: len(dct.frames) == 2)
    assert canvas(dct) == image.rgba.tobytes() and ctrl.stream.unsaved


def test_stopping_with_unsaved_changes_says_they_were_not_saved(tmp_path, dct, api, stores):
    ctrl = ready_controller(tmp_path, dct, api, stores)
    image = ArrayImage(32, 32)
    start(ctrl, image)
    drive(ctrl, lambda: len(dct.frames) == 1)
    image.rgba[0:4, 0:4] = 9  # a paint stroke after the first frame
    image.dirty = True
    drive(ctrl, lambda: ctrl.stream.unsaved and len(dct.frames) == 2)
    ctrl.stream.stop()
    assert ctrl.stream.status.message.key == "live.stopped-unsaved"
    assert dct.saves == []


def test_texture_checks_arrive_with_the_live_preview(tmp_path, dct, api, stores):
    ctrl = ready_controller(tmp_path, dct, api, stores)
    start(ctrl, ArrayImage(96, 80))
    drive(ctrl, lambda: ctrl.stream.findings is not None)
    assert ctrl.stream.findings == [{"code": "non-power-of-two", "severity": "warning"}]
    ctrl.stream.check_texture()
    assert ctrl.stream.checking
    drive(ctrl, lambda: not ctrl.stream.checking)
    ctrl.stream.stop()
    assert ctrl.stream.findings is None


def test_a_signed_out_durty_cloth_tool_is_shown_and_waited_for(tmp_path, dct, api, stores):
    first = ready_controller(tmp_path, dct, api, stores)
    first.disconnect()
    dct.signed_out_auths = 1  # Durty Cloth Tool answers that it is signed out, once
    second = make_controller(tmp_path, dct, api, stores)
    second.connect()
    drive(second, lambda: second.dct_signed_out)
    assert second.chip() == "action" and strings.english(second.status()) == "Durty Cloth Tool is signed out"
    second.connect()  # tries again at once instead of waiting for the next attempt
    drive(second, lambda: second.ready)
    assert not second.dct_signed_out and second.chip() == "connected"


def test_diagnostics_hold_no_names_codes_or_paths(tmp_path, dct, api, stores):
    ctrl = ready_controller(tmp_path, dct, api, stores)
    text = ctrl.diagnostics({"sollumz": "2.9.0"})
    assert text.startswith("Durty Cloth Tool Creator Link diagnostics")
    assert f"plugin: blender {settings.VERSION}" in text and "sollumz: 2.9.0" in text
    stored = json.loads(stores.stores["tokens"].load().decode())
    assert "Durty" not in text.replace("Durty Cloth Tool", "")  # the account name
    for secret in (str(tmp_path), ctrl.install_id, stored["accessToken"], stored["refreshToken"]):
        assert secret not in text


def test_dct_going_away_closes_the_stream_and_reconnects(tmp_path, dct, api, stores):
    ctrl = ready_controller(tmp_path, dct, api, stores)
    start(ctrl, ArrayImage(16, 16))
    drive(ctrl, lambda: len(dct.frames) == 1)
    dct.drop_all()
    drive(ctrl, lambda: not ctrl.stream.active)
    assert ctrl.stream.status.message == settings.describe_close_reason("disconnected")
    drive(ctrl, lambda: ctrl.state == READY, timeout=20)
    assert strings.english(ctrl.status()) == "Signed in as Durty"


@pytest.mark.skipif(os.name != "nt", reason="DPAPI exists on Windows only")
def test_the_windows_secret_store_keeps_the_sign_in_protected(tmp_path, dct, api):
    dct.on_assist = api.approve
    ctrl = make_controller(tmp_path, dct, api, tokens.default_secret_store)
    ctrl.connect()
    drive(ctrl, lambda: ctrl.ready)
    folder = tmp_path / "user"
    assert {"install-id", "tokens.dpapi"} <= {p.name for p in folder.iterdir()}
    raw = (folder / "tokens.dpapi").read_bytes()
    assert raw.startswith(b"DCTDPAPI1") and b"refreshToken" not in raw
    ctrl.disconnect()
    again = make_controller(tmp_path, dct, api, tokens.default_secret_store)
    again.connect()
    drive(again, lambda: again.ready)  # the protected files are read back, and the refresh lock works
    again.disconnect()


# ---- protocol 2: signing in, opening what Durty Cloth Tool sends, the linked cloth card -----------------------

OTHER = {"clothId": "0d9e8f7a-6b5c-4d3e-8f1a-2b3c4d5e6f70", "textureId": "1e2d3c4b-5a69-4788-9a0b-1c2d3e4f5a6b"}
FOCUSED = {"clothId": BINDING["clothId"], "name": "jbib_003_u", "selectedTextureId": BINDING["textureId"],
           "textures": [{"textureId": BINDING["textureId"], "name": "jbib_diff_003_a_uni", "width": 64, "height": 64}],
           "targets": ["diffuse", "normal"], "drawableType": "jbib", "gender": "female",
           "collection": "mp_f_freemode_01", "number": 3}


class FakeDocuments:
    """Blender's side of opening items from DCT, without Blender: images are :class:`ArrayImage` objects, an import
    records what was written for it and pushes like the Blender side does (bound to the cloth)."""

    def __init__(self, ctrl: link.LinkController) -> None:
        self.ctrl = ctrl
        self.images: Dict[str, ArrayImage] = {}
        self.kept: List[str] = []
        self.problem: Optional[strings.Msg] = None
        self.fail: Optional[BaseException] = None
        self.imports: List[Dict[str, object]] = []
        self.discarded: List[str] = []
        self.warnings = False
        #: Runs while the request is handled, before DCT is answered (for example: the link goes away meanwhile).
        self.meanwhile: Optional[Callable[[], None]] = None

    def open_texture(self, document: link.TextureDocument) -> link.OpenedImage:
        if self.fail is not None:
            raise self.fail
        if self.meanwhile is not None:
            self.meanwhile()
        rgba = np.frombuffer(bytes(document.pixels), np.uint8).reshape(document.height, document.width, 4).copy()
        image = self.images[document.name] = ArrayImage(document.width, document.height, rgba)
        return link.OpenedImage(image, document.width, document.height, pixels.Conversion(), document.name,
                                created=True)

    def keep_texture(self, opened: link.OpenedImage) -> None:
        self.kept.append(opened.document)

    def discard_texture(self, opened: link.OpenedImage) -> None:
        self.discarded.append(opened.document)
        self.images.pop(opened.document, None)

    def model_problem(self) -> Optional[strings.Msg]:
        if self.meanwhile is not None:
            self.meanwhile()
        return self.problem

    def import_model(self, folder: pathlib.Path, model_file: str, binding: Dict[str, str]) -> link.ImportedModel:
        files = {p.relative_to(folder).as_posix(): p.read_bytes() for p in folder.rglob("*") if p.is_file()}
        self.imports.append({"folder": folder, "model": model_file, "binding": binding, "files": files})
        name = model_file.split(".", 1)[0]
        return link.ImportedModel(name, lambda: self.ctrl.model.push(Export(), name, binding=binding), self.warnings)


def documents_controller(tmp_path, dct, api, stores) -> tuple:
    dct.focused = FOCUSED
    ctrl = ready_controller(tmp_path, dct, api, stores)
    documents = FakeDocuments(ctrl)
    ctrl.documents = documents
    return ctrl, documents


def opened_live_opens(dct: FakeDct) -> List[Dict[str, object]]:
    return [m for m in dct.received if m.get("type") == "live.open"]


def test_sign_in_asks_durty_cloth_tool_first(tmp_path, dct, api, stores):
    """Sign In goes through Durty Cloth Tool's approval window whenever Durty Cloth Tool is there; no browser."""
    opened: List[str] = []
    ctrl = make_controller(tmp_path, dct, api, stores, opened=opened)
    dct.on_assist = api.approve
    ctrl.sign_in()
    drive(ctrl, lambda: ctrl.ready)
    assert len(dct.assisted_codes) == 1 and opened == [] and ctrl.user_name == "Durty"


def test_sign_in_shows_the_browser_code_when_durty_cloth_tool_is_not_running(tmp_path, dct, api, stores):
    opened: List[str] = []
    ctrl = make_controller(tmp_path, dct, api, stores, opened=opened)
    ctrl.port_override = dead_port()
    ctrl.BROWSER_FALLBACK_SECONDS = 0.3
    ctrl.sign_in()
    assert ctrl.finding_for_sign_in
    drive(ctrl, lambda: ctrl.active_sign_in() is not None)
    code, url = ctrl.active_sign_in()
    assert opened == [] and url.startswith(api.base_url)  # shown with its code; the user opens the page
    assert not ctrl.finding_for_sign_in and len([r for r in api.requests if r["path"] == "/link/api/auth/device"]) == 1
    api.approve(code)
    drive(ctrl, lambda: ctrl.user_name == "Durty")
    ctrl.disconnect()


def test_the_browser_choice_and_the_session_share_one_sign_in(tmp_path, dct, api, stores):
    """Sign In in the Browser while the session starts its own device sign-in: one code, not two."""
    ctrl = make_controller(tmp_path, dct, api, stores, opened=[])
    ctrl._ensure_setup()
    first = ctrl.token_source.begin_device_sign_in()
    second = ctrl.token_source.begin_device_sign_in()
    drive(ctrl, lambda: first.poll() and second.poll())
    assert first.result() is second.result()
    assert len([r for r in api.requests if r["path"] == "/link/api/auth/device"]) == 1


def dead_port() -> int:
    import socket

    probe = socket.socket()
    probe.bind(("127.0.0.1", 0))
    port = probe.getsockname()[1]
    probe.close()
    return port


def test_an_older_durty_cloth_tool_is_told_apart(tmp_path, dct, api, stores):
    """A Durty Cloth Tool of link protocol 1 cannot read this add-on's hello: the add-on says to update it."""
    first = ready_controller(tmp_path, dct, api, stores)
    first.disconnect()
    dct.major_one = True
    ctrl = make_controller(tmp_path, dct, api, stores)
    ctrl.connect()
    drive(ctrl, lambda: ctrl.incompatible is not None and ctrl.state == STOPPED)
    assert ctrl.incompatible["code"] == "dct-too-old" and ctrl.chip() == "problem"
    assert "Update Durty Cloth Tool" in strings.english(settings.describe_error("dct-too-old"))


def test_the_linked_cloth_card_shows_dcts_details_and_picture(tmp_path, dct, api, stores):
    ctrl, _ = documents_controller(tmp_path, dct, api, stores)
    shown = []
    ctrl.on_thumbnail = shown.append
    info = ctrl.card_info()
    assert (info.name, info.letter, info.drawable_type, info.gender, info.collection, info.number, info.linked) == (
        "jbib_003_u", "A", "jbib", "female", "mp_f_freemode_01", 3, False)
    assert info.targets == ("diffuse", "normal")
    drive(ctrl, lambda: ctrl.thumbnail is not None)
    request = next(m for m in dct.received if m.get("type") == "item.thumbnail")
    assert request["size"] == ctrl.THUMBNAIL_SIZE and request["binding"] == BINDING
    assert shown == [ctrl.thumbnail] and len(ctrl.thumbnail.pixels) == ctrl.thumbnail.width * ctrl.thumbnail.height * 4

    # An image linked to another cloth: the card shows that cloth (once seen) and asks for its picture.
    other = dict(FOCUSED, clothId=OTHER["clothId"], name="uppr_001_u", selectedTextureId=OTHER["textureId"],
                 textures=[{"textureId": OTHER["textureId"], "name": "uppr_diff_001_a_uni"}], gender="male")
    dct.broadcast({"type": "event.selection", "id": "sel2", "focused": other})
    drive(ctrl, lambda: ctrl.focused is not None and ctrl.focused["name"] == "uppr_001_u")
    dct.broadcast({"type": "event.selection", "id": "sel3", "focused": FOCUSED})
    drive(ctrl, lambda: ctrl.focused["name"] == "jbib_003_u")
    ctrl.linked_binding = lambda: OTHER
    info = ctrl.card_info()
    assert info.linked and info.name == "uppr_001_u" and info.gender == "male"
    drive(ctrl, lambda: ctrl.thumbnail is not None and ctrl.thumbnail.binding == OTHER)
    ctrl.linked_binding = lambda: {"clothId": "99999999-9999-4999-8999-999999999999", "textureId": OTHER["textureId"]}
    assert ctrl.card_info().linked and ctrl.card_info().name == ""  # never selected: the card says so


def test_a_texture_opened_from_dct_is_accepted_bound_and_streamed(tmp_path, dct, api, stores):
    ctrl, documents = documents_controller(tmp_path, dct, api, stores)
    rgba = np.random.default_rng(9).integers(0, 256, size=(32, 64, 4), dtype=np.uint8)
    request_id = dct.open_texture(rgba.tobytes(), 64, 32, target="normal", binding=BINDING, name="jbib_normal_003")
    drive(ctrl, lambda: dct.host_result(request_id) is not None and len(dct.frames) == 1)
    assert dct.host_result(request_id)["ok"] is True and "code" not in dct.host_result(request_id)
    assert list(documents.images) == ["jbib_003_u A Normal"]  # named after the cloth, variation and map
    (live_open,) = opened_live_opens(dct)
    assert live_open["binding"] == BINDING and live_open["target"] == "normal" and live_open["width"] == 64
    assert canvas(dct) == rgba.tobytes()  # what DCT sent arrives back unchanged
    assert ctrl.open_notice.message == strings.msg("open.opened", name="jbib_003_u A Normal")
    assert ctrl.stream.binding == BINDING and ctrl.card_info().linked
    drive(ctrl, lambda: documents.kept == ["jbib_003_u A Normal"])  # kept with the file after DCT heard ok

    # While that live preview runs, the next texture is refused as busy and the panel says why.
    second = dct.open_texture(rgba.tobytes(), 64, 32, target="diffuse")
    drive(ctrl, lambda: dct.host_result(second) is not None)
    assert dct.host_result(second) == dict(dct.host_result(second), ok=False, code="busy")
    assert ctrl.open_notice.message.key == "open.texture-busy" and len(opened_live_opens(dct)) == 1

    # Saving names the bound cloth.
    ctrl.stream.save("replace")
    drive(ctrl, lambda: not ctrl.stream.saving)
    assert ctrl.stream.status.text == "Saved to jbib_003_u A. You can undo it in History."


def test_a_bound_image_stays_linked_after_a_reconnect(tmp_path, dct, api, stores):
    """The stream always sends the image's stored binding, also when the selection in DCT changed meanwhile."""
    ctrl, _ = documents_controller(tmp_path, dct, api, stores)
    image = ArrayImage(16, 16)
    ctrl.stream.start(image, "specular", 16, 16, binding=OTHER)
    drive(ctrl, lambda: len(dct.frames) == 1)
    dct.drop_all()
    drive(ctrl, lambda: not ctrl.stream.active)
    drive(ctrl, lambda: ctrl.ready, timeout=20)
    ctrl.stream.start(image, "specular", 16, 16, binding=OTHER)
    drive(ctrl, lambda: len(dct.frames) == 2)
    assert [m["binding"] for m in opened_live_opens(dct)] == [OTHER, OTHER]
    checks = [m for m in dct.received if m.get("type") == "texture.validate"]
    assert checks and all(m.get("binding") == OTHER for m in checks)


def test_a_texture_that_cannot_be_opened_is_refused(tmp_path, dct, api, stores):
    ctrl, documents = documents_controller(tmp_path, dct, api, stores)
    documents.fail = MemoryError()
    request_id = dct.open_texture(bytes(16 * 16 * 4), 16, 16)
    drive(ctrl, lambda: dct.host_result(request_id) is not None)
    assert dct.host_result(request_id)["code"] == "open-failed" and not ctrl.stream.active
    assert ctrl.open_notice.level == "ERROR" and ctrl.open_notice.message.key == "open.texture-failed"
    ctrl.documents = None  # an add-on without Blender's side cannot open anything
    request_id = dct.open_texture(bytes(16 * 16 * 4), 16, 16)
    drive(ctrl, lambda: dct.host_result(request_id) is not None)
    assert dct.host_result(request_id)["code"] == "not-supported"


def test_a_map_of_the_card_is_read_from_dct_and_opened_bound(tmp_path, dct, api, stores):
    ctrl, documents = documents_controller(tmp_path, dct, api, stores)
    dct.texture_size = (8, 4)
    with pytest.raises(ValueError, match="no specular map"):
        ctrl.open_map("specular")  # the cloth has no specular map
    ctrl.open_map("normal")
    assert ctrl.open_map_problem("diffuse").key == "open.reading"
    drive(ctrl, lambda: ctrl.stream.is_open and len(dct.frames) == 1)
    (read,) = dct.texture_reads
    assert read["target"] == "normal" and read["binding"] == BINDING
    assert list(documents.images) == ["jbib_003_u A Normal"] and opened_live_opens(dct)[0]["binding"] == BINDING
    assert ctrl.open_map_problem("diffuse").key == "open.stop-live-first"
    dct.set_features(services="needsUltimate")
    drive(ctrl, lambda: ctrl.session.features.get("dct.link.services") == "needsUltimate")
    ctrl.stream.stop()
    assert ctrl.open_map_problem("diffuse").key == "open.map-upsell"


def model_files(name: str = "jbib_003_u") -> List[tuple]:
    return [(f"{name}.ydd.xml", b"<DrawableDictionary />"), ("jbib_diff_003_a_uni.dds", b"DDS " + bytes(12)),
            ("jbib_normal_003.dds", b"DDS " + bytes(8))]


def test_a_model_opened_from_dct_is_imported_and_pushed_bound(tmp_path, dct, api, stores):
    ctrl, documents = documents_controller(tmp_path, dct, api, stores)
    request_id = dct.open_model(model_files(), binding=OTHER)
    drive(ctrl, lambda: ctrl.model.lease is not None and not ctrl.model.pushing)
    assert dct.host_result(request_id)["ok"] is True
    (imported,) = documents.imports
    folder = imported["folder"]
    # The files sit in the add-on's own folder, in a folder of this open's own, and the textures in a folder named
    # after the model, as Sollumz reads them.
    assert folder.name == "jbib_003_u" and folder.parent.name.startswith(request_id + "-")
    assert folder.parent.parent == tmp_path / "user" / link.MODELS_FOLDER and imported["model"] == "jbib_003_u.ydd.xml"
    assert imported["files"] == {"jbib_003_u.ydd.xml": b"<DrawableDictionary />",
                                 "jbib_003_u/jbib_diff_003_a_uni.dds": b"DDS " + bytes(12),
                                 "jbib_003_u/jbib_normal_003.dds": b"DDS " + bytes(8)}
    # DCT heard ok before the import ran.
    answered = next(i for i, m in enumerate(dct.received) if m.get("type") == "host.result")
    pushed = next(i for i, m in enumerate(dct.received) if m.get("type") == "model.push")
    assert answered < pushed
    first, = (header for header, _ in dct.pushes)
    assert first["binding"] == OTHER and "lease" not in first  # the first push names the cloth
    assert ctrl.model.open_notice.message == strings.msg("open.opened", name="jbib_003_u")
    ctrl.model.push(Export(b"DDS 2"), "jbib_003_u", binding=OTHER)
    drive(ctrl, lambda: len(dct.pushes) == 2 and not ctrl.model.pushing)
    assert dct.pushes[1][0]["lease"] == ctrl.model.lease and "binding" not in dct.pushes[1][0]  # later: the lease
    assert folder.is_dir()
    ctrl.model.save()
    drive(ctrl, lambda: ctrl.model.busy is None)
    assert ctrl.model.status.message.key == "model.saved" and folder.is_dir()
    ctrl.model.discard()
    drive(ctrl, lambda: ctrl.model.lease is None)
    assert not folder.parent.exists()  # the temporary files go with the model


def test_a_model_for_another_cloth_replaces_the_one_on_the_ped(tmp_path, dct, api, stores):
    ctrl, documents = documents_controller(tmp_path, dct, api, stores)
    ctrl.model.push(Export(), "smoke_ydd")  # the user's own model, on the focused cloth
    drive(ctrl, lambda: ctrl.model.lease is not None and not ctrl.model.pushing)
    old = ctrl.model.lease
    dct.open_model(model_files(), binding=OTHER)
    drive(ctrl, lambda: ctrl.model.lease not in (None, old) and not ctrl.model.pushing)
    assert dct.model_discards == [old]  # taken off the ped first
    assert dct.pushes[-1][0]["binding"] == OTHER and "lease" not in dct.pushes[-1][0]
    assert link.same_binding(ctrl.model.lease_binding, OTHER)


def test_a_model_without_sollumz_is_refused_with_what_to_install(tmp_path, dct, api, stores):
    ctrl, documents = documents_controller(tmp_path, dct, api, stores)
    documents.problem = strings.msg("sollumz.missing", version=settings.SOLLUMZ_MINIMUM)
    request_id = dct.open_model(model_files())
    drive(ctrl, lambda: dct.host_result(request_id) is not None)
    assert dct.host_result(request_id)["code"] == "dependency-missing"
    assert ctrl.model.open_notice.text == ("Durty Cloth Tool sent the model jbib_003_u. Install and enable Sollumz "
                                           f"{settings.SOLLUMZ_MINIMUM} or later to open and push models.")
    assert documents.imports == [] and not (tmp_path / "user" / link.MODELS_FOLDER).exists()


def test_a_model_is_refused_while_another_is_pushed(tmp_path, dct, api, stores):
    ctrl, documents = documents_controller(tmp_path, dct, api, stores)
    dct.push_delay = 1.0
    ctrl.model.push(Export(), "smoke_ydd")
    request_id = dct.open_model(model_files())
    drive(ctrl, lambda: dct.host_result(request_id) is not None)
    assert dct.host_result(request_id)["code"] == "busy" and ctrl.model.open_notice.message.key == "open.model-busy"


def test_a_failed_import_and_unloading_remove_the_files(tmp_path, dct, api, stores):
    ctrl, documents = documents_controller(tmp_path, dct, api, stores)
    documents.import_model = lambda *args: (_ for _ in ()).throw(strings.UserError(strings.msg("open.no-dictionary")))
    dct.open_model(model_files())
    drive(ctrl, lambda: ctrl.model.open_notice is not None and ctrl.model.open_notice.level == "ERROR")
    assert ctrl.model.open_notice.message.key == "open.model-failed"
    base = tmp_path / "user" / link.MODELS_FOLDER
    assert not any(base.iterdir())
    documents.import_model = FakeDocuments.import_model.__get__(documents)
    dct.open_model(model_files())
    drive(ctrl, lambda: ctrl.model.lease is not None and not ctrl.model.pushing)
    assert any(base.iterdir())
    ctrl.shutdown()  # the add-on is disabled
    assert not any(base.iterdir())


def test_model_files_stay_inside_the_add_ons_folder(tmp_path):
    for name in ("..", "../escape.dds", "a/b.dds", "CON.dds", ".hidden"):
        with pytest.raises(ValueError):
            link._inside(tmp_path, name)
    assert link._inside(tmp_path, "jbib_000_u.ydd.xml") == tmp_path / "jbib_000_u.ydd.xml"


def test_each_open_of_a_model_gets_a_folder_of_its_own(tmp_path, dct, api, stores):
    """Sollumz takes an image it loaded before when the path is the same: a second open of the same model with a
    changed diffuse must come from another path."""
    ctrl, documents = documents_controller(tmp_path, dct, api, stores)
    files = model_files()
    dct.open_model(files)
    drive(ctrl, lambda: ctrl.model.lease is not None and not ctrl.model.pushing)
    ctrl.model.discard()
    drive(ctrl, lambda: ctrl.model.lease is None)
    files[1] = ("jbib_diff_003_a_uni.dds", b"DDS " + bytes([7]) * 12)
    dct.open_model(files)
    drive(ctrl, lambda: len(documents.imports) == 2 and ctrl.model.lease is not None and not ctrl.model.pushing)
    first, second = (entry["folder"] for entry in documents.imports)
    assert first != second and first.name == second.name == "jbib_003_u"
    assert documents.imports[1]["files"]["jbib_003_u/jbib_diff_003_a_uni.dds"] == b"DDS " + bytes([7]) * 12


def test_nothing_stays_open_when_dct_no_longer_waits_for_the_answer(tmp_path, dct, api, stores):
    """accept() sends nothing once the link changed: the image made for the request and the model files go."""
    ctrl, documents = documents_controller(tmp_path, dct, api, stores)
    documents.meanwhile = lambda: ctrl.session.stop()
    dct.open_texture(bytes(16 * 16 * 4), 16, 16)
    drive(ctrl, lambda: bool(documents.discarded))
    assert documents.images == {} and not ctrl.stream.active
    assert ctrl.open_notice.message == settings.describe_close_reason("disconnected")
    ctrl.connect()
    drive(ctrl, lambda: ctrl.ready)
    dct.open_model(model_files())
    drive(ctrl, lambda: ctrl.model.open_notice is not None and ctrl.model.open_notice.level == "WARNING")
    for _ in range(5):
        ctrl.poll()
    assert documents.imports == [] and not any((tmp_path / "user" / link.MODELS_FOLDER).iterdir())
    assert [m for m in dct.received if m.get("type") == "host.result"] == []


def test_import_warnings_are_said(tmp_path, dct, api, stores):
    ctrl, documents = documents_controller(tmp_path, dct, api, stores)
    documents.warnings = True
    dct.open_model(model_files())
    drive(ctrl, lambda: ctrl.model.lease is not None and not ctrl.model.pushing)
    assert ctrl.model.open_notice.level == "WARNING"
    assert ctrl.model.open_notice.message == strings.msg("open.model-warnings", name="jbib_003_u")


def make_link(target: pathlib.Path, link_path: pathlib.Path) -> None:
    """A directory link: a junction on Windows (no privilege needed), a symbolic link elsewhere."""
    if os.name == "nt":
        import _winapi

        _winapi.CreateJunction(str(target), str(link_path))
    else:
        os.symlink(target, link_path, target_is_directory=True)


def stale_model_folder(base: pathlib.Path, name: str, model: bool = True, age: float = 3600.0) -> pathlib.Path:
    folder = base / name
    (folder / "jbib_003_u").mkdir(parents=True)
    if model:
        (folder / "jbib_003_u" / "jbib_003_u.ydd.xml").write_bytes(b"<DrawableDictionary />")
    else:
        (folder / "jbib_003_u" / "notes.txt").write_bytes(b"mine")
    old = time.time() - age
    os.utime(folder, (old, old))
    return folder


def test_start_up_removes_only_model_folders_the_add_on_left(tmp_path, dct, api, stores):
    base = tmp_path / "user" / link.MODELS_FOLDER
    left = stale_model_folder(base, "om1-0000aaaa")
    recent = stale_model_folder(base, "om2-0000bbbb", age=0)
    foreign = stale_model_folder(base, "something-else", model=False)
    loose = base / "loose.txt"
    loose.write_bytes(b"x")
    ctrl = make_controller(tmp_path, dct, api, stores)
    ctrl.prepare()
    assert not left.exists() and recent.exists() and foreign.exists() and loose.exists()


def test_start_up_leaves_a_linked_models_folder_alone(tmp_path, dct, api, stores):
    elsewhere = tmp_path / "elsewhere"
    target = stale_model_folder(elsewhere, "om1-0000aaaa")
    (tmp_path / "user").mkdir()
    make_link(elsewhere, tmp_path / "user" / link.MODELS_FOLDER)
    ctrl = make_controller(tmp_path, dct, api, stores)
    ctrl.prepare()
    assert target.exists()  # nothing behind a link is removed
    dct.on_assist = api.approve
    ctrl.connect()
    drive(ctrl, lambda: ctrl.ready)
    ctrl.documents = FakeDocuments(ctrl)
    request_id = dct.open_model(model_files())
    drive(ctrl, lambda: dct.host_result(request_id) is not None)
    assert dct.host_result(request_id).get("code") == "open-failed"  # and nothing is written through one
    assert sorted(p.name for p in elsewhere.iterdir()) == ["om1-0000aaaa"]
