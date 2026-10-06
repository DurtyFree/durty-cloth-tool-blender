# SPDX-License-Identifier: GPL-3.0-or-later
"""Adding a garment to a Durty Cloth Tool project, without Blender: the skeleton template's bones, the checks before
anything is sent (names, pictures, vertex groups, the export), the PNG pictures, the files of the add, and the whole
exchange with a fake Durty Cloth Tool (the template kept per gender, the add, Durty Cloth Tool's answers, Cancel while
its dialog is open, a lost connection)."""

from __future__ import annotations

import io
import pathlib
import struct
import time
import zlib
from typing import Callable

import numpy as np
import pytest

from durty_cloth_tool_link import garment_add, link, strings
from durty_cloth_tool_link.dct_link import protocol
from durty_cloth_tool_link.dct_link import session as link_session
from tests.support import synthetic
from tests.support.fake_dct import ADDED_BINDING, FakeDct
from tests.support.fake_link_api import FakeLinkApi
from tests.test_link import Stores, make_controller


# ---- the skeleton template ----------------------------------------------------------------------------------


def test_the_template_lists_its_bones_in_the_games_order():
    xml = synthetic.skeleton_template_xml("female")
    assert garment_add.template_bones(xml) == synthetic.skeleton_names()
    assert garment_add.armature_problem(synthetic.skeleton_names(), synthetic.skeleton_names()) is None


@pytest.mark.parametrize("xml", [b"not xml", b"<Drawable />", b"<DrawableDictionary><Item /></DrawableDictionary>",
                                 b"<DrawableDictionary><Item><Skeleton><Bones><Item><Name>A</Name></Item><Item><Name>A"
                                 b"</Name></Item></Bones></Skeleton></Item></DrawableDictionary>"])
def test_a_template_without_usable_bones_is_refused(xml):
    with pytest.raises(garment_add.TemplateError):
        garment_add.template_bones(xml)


def test_an_armature_must_hold_the_templates_bones_in_order():
    """A blend index is the bone's position in the armature: a reordered or changed armature would move the wrong
    bones in game."""
    bones = synthetic.skeleton_names()
    swapped = [bones[1], bones[0], *bones[2:]]
    assert garment_add.armature_problem(swapped, bones).key == "add.skeleton.order"
    problem = garment_add.armature_problem(bones[:-1], bones)
    assert problem.key == "add.skeleton.bones" and problem.fields == {"count": len(bones) - 1, "expected": len(bones)}


def test_vertex_groups_are_weights_only_when_they_name_a_bone():
    bones = synthetic.skeleton_names()
    report = garment_add.group_report(["SKEL_Spine3", "DCT Tears", "DCT_tmp_spine", "Group", "SKEL_L_UpperArm"], bones)
    assert report == (["SKEL_Spine3", "SKEL_L_UpperArm"], ["Group"], ["DCT Tears", "DCT_tmp_spine"])
    problems = garment_add.group_problems(report)
    assert [p.key for p in problems] == ["add.why.unknown-groups"] and problems[0].fields["names"] == "Group"
    assert [p.key for p in garment_add.group_problems(garment_add.group_report(["DCT Tears"], bones))] == [
        "add.why.no-weights"]
    many = garment_add.group_problems(garment_add.group_report([f"g{i}" for i in range(7)] + ["SKEL_ROOT"], bones))
    assert many[0].fields == {"count": 7, "names": "g0, g1, g2, g3, g4 …"}


# ---- names and pictures -------------------------------------------------------------------------------------


def test_names_follow_the_protocols_text_rules():
    assert garment_add.name_problem("Denim Jacket") is None
    assert garment_add.name_problem("  ").key == "add.why.name-empty"
    assert garment_add.name_problem("x" * 129).key == "add.why.name-invalid"
    assert garment_add.name_problem("bad\x07name").key == "add.why.name-invalid"
    assert garment_add.variation_title("", "jacket_diffuse") == "jacket_diffuse"
    assert garment_add.variation_title(" Blue ", "x") == "Blue"
    assert garment_add.variation_title("a\tb", "x") == "a b"
    assert len(garment_add.variation_title("y" * 300, "x")) == protocol.MAX_TEXT_LENGTH


@pytest.mark.parametrize("size, blocking, warnings", [
    ((2048, 2048), None, []),
    ((4096, 1024), None, ["add.picture.large"]),
    ((4100, 1024), "add.picture.too-large", []),
    ((1022, 1024), "add.picture.not-multiple-of-four", []),
    ((1000, 1000), None, ["add.picture.non-power-of-two"]),
    ((8, 8), None, ["add.picture.small"]),
    ((0, 8), "add.picture.empty", []),
])
def test_pictures_are_checked_as_durty_cloth_tool_checks_them(size, blocking, warnings):
    """An edge above 4096 or a side that does not divide by four refuses the add in Durty Cloth Tool; the rest is
    advice, as its texture checks give it."""
    check = garment_add.picture_check(*size, "jacket_diffuse")
    assert (check.blocking.key if check.blocking else None) == blocking
    assert [w.key for w in check.warnings] == warnings


def read_png(data: bytes):
    """A minimal PNG reader for the test: RGBA8, one IDAT, every filter type a writer may use."""
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    offset, chunks = 8, {}
    while offset < len(data):
        length = struct.unpack(">I", data[offset:offset + 4])[0]
        kind = data[offset + 4:offset + 8]
        body = data[offset + 8:offset + 8 + length]
        crc = struct.unpack(">I", data[offset + 8 + length:offset + 12 + length])[0]
        assert zlib.crc32(kind + body) & 0xFFFFFFFF == crc
        chunks[kind] = body
        offset += 12 + length
    width, height, depth, colour, _, _, _ = struct.unpack(">IIBBBBB", chunks[b"IHDR"])
    assert (depth, colour) == (8, 6) and b"IEND" in chunks
    raw = np.frombuffer(zlib.decompress(chunks[b"IDAT"]), dtype=np.uint8).reshape(height, width * 4 + 1)
    rows = np.zeros((height, width * 4), dtype=np.uint8)
    for y in range(height):
        kind, line = raw[y, 0], raw[y, 1:].astype(np.int64)
        assert kind == 1  # Sub
        out = np.zeros(width * 4, dtype=np.int64)
        for x in range(width * 4):
            out[x] = (line[x] + (out[x - 4] if x >= 4 else 0)) % 256
        rows[y] = out
    return width, height, rows.reshape(-1)


def test_pictures_are_written_as_png_without_loss():
    rng = np.random.default_rng(3)
    rgba = rng.integers(0, 256, 6 * 4 * 4, dtype=np.uint8)
    width, height, back = read_png(garment_add.png_bytes(rgba.tobytes(), 6, 4))
    assert (width, height) == (6, 4) and np.array_equal(back, rgba)
    with pytest.raises(ValueError):
        garment_add.png_bytes(rgba.tobytes(), 5, 4)


# ---- the export ---------------------------------------------------------------------------------------------


GEOMETRY = "<Item><Geometries><Item><VertexBuffer /></Item></Geometries></Item>"


def export_xml(drawables: int = 1, models: int = 1, skeleton: bool = False) -> bytes:
    items = ""
    for _ in range(drawables):
        bones = "<Skeleton><Bones><Item><Name>SKEL_ROOT</Name></Item></Bones></Skeleton>" if skeleton else ""
        items += f"<Item><Name>d</Name>{bones}<DrawableModelsHigh>{GEOMETRY * models}</DrawableModelsHigh></Item>"
    return f"<?xml version='1.0' encoding='UTF-8'?>\n<DrawableDictionary>{items}</DrawableDictionary>".encode()


def test_an_empty_or_partial_export_is_refused():
    """Sollumz reports success for an empty dictionary, so the add-on reads what it wrote."""
    assert garment_add.export_problem(garment_add.export_summary(io.BytesIO(export_xml()))) is None
    summary = garment_add.export_summary(io.BytesIO(export_xml(models=2)))
    assert summary == (1, 2, 2, 0)
    for xml, key in ((b"<DrawableDictionary />", "add.export.empty"), (export_xml(models=0), "add.export.empty"),
                     (export_xml(drawables=2), "add.export.several"), (export_xml(skeleton=True), "add.export.skeleton")):
        assert garment_add.export_problem(garment_add.export_summary(io.BytesIO(xml))).key == key
    with pytest.raises(ValueError):
        garment_add.export_summary(io.BytesIO(b"<Drawable />"))
    with pytest.raises(ValueError):
        garment_add.export_summary(io.BytesIO(b"<DrawableDictionary><Item>"))


def test_the_add_names_its_files_and_variations():
    files, variations = garment_add.item_files(
        ("jacket_ydd.ydd.xml", b"<x/>"), [("Variation_A.png.dds", b"DDS "), ("jbib_normal.dds", b"DDS ")],
        [garment_add.Variation("Blue", b"png1"), garment_add.Variation("Red", b"png2")])
    names = [name for name, _ in files]
    assert names[:3] == ["jacket_ydd.ydd.xml", "Variation_A.png.dds", "jbib_normal.dds"]
    assert names[3:] == ["variation_a.png", "variation_b.png"]
    assert variations == [("variation_a.png", "Blue"), ("variation_b.png", "Red")]
    assert protocol.item_files_reason([{"name": n, "length": len(d)} for n, d in files],
                                      [{"file": f, "name": t} for f, t in variations]) is None
    clash, _ = garment_add.item_files(("m.ydd.xml", b"x"), [("VARIATION_A.png", b"x")], [garment_add.Variation("A", b"p")])
    assert [name for name, _ in clash][-1] == "dct_variation_a.png"
    with pytest.raises(ValueError):
        garment_add.item_files(("m.ydd.xml", b"x"), [], [])
    assert garment_add.payload_size(files) == 4 + 4 + 4 + 4 + 4


def test_every_finding_and_answer_has_words():
    for code in protocol.FINDING_CODES:
        assert garment_add.finding_text(code).key in strings.EN, code
    for code in protocol.ERROR_CODES:
        level, message = garment_add.result_message(code)
        assert level in ("INFO", "WARNING", "ERROR") and message.key in strings.EN, code
    assert garment_add.result_message("request-denied", withdrawn=True)[1].key == "add.result.withdrawn"
    assert garment_add.result_message("item-limit") == ("WARNING", strings.msg("add.result.item-limit"))
    for code in ("cancelled", "timeout", "disconnected"):
        assert garment_add.failure_message(code)[1].key == f"add.result.{ {'cancelled': 'cancel-unanswered'}.get(code, code)}"
    assert garment_add.template_refusal("game-required").key == "add.skeleton.game-required"
    assert garment_add.template_refusal("unknown-message-type").key == "add.dct-too-old"
    errors_first = garment_add.sorted_findings([{"code": "too-small", "severity": "info"},
                                                {"code": "rig-invalid", "severity": "error"},
                                                {"code": "non-power-of-two", "severity": "warning"}])
    assert [f["severity"] for f in errors_first] == ["error", "warning", "info"]


# ---- the exchange with Durty Cloth Tool ---------------------------------------------------------------------


@pytest.fixture
def dct():
    with FakeDct() as server:
        server.skeleton_files = {gender: [(synthetic.skeleton_template_file(gender), synthetic.skeleton_template_xml(gender))]
                                 for gender in ("male", "female")}
        yield server


@pytest.fixture
def api():
    with FakeLinkApi() as server:
        yield server


def drive(ctrl: link.LinkController, until: Callable[[], bool], timeout: float = 15.0) -> None:
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        ctrl.poll()
        if until():
            return
        time.sleep(0.005)
    raise AssertionError(f"timed out; add: {ctrl.item_add.status}; skeletons: {ctrl.skeletons.problems}")


def connected(tmp_path: pathlib.Path, dct: FakeDct, api: FakeLinkApi) -> link.LinkController:
    dct.on_assist = api.approve
    ctrl = make_controller(tmp_path, dct, api, Stores())
    ctrl.connect()
    drive(ctrl, lambda: ctrl.ready and ctrl.project is not None)
    return ctrl


def add_files():
    return garment_add.item_files(("jacket.ydd.xml", export_xml()), [("jbib_normal.dds", b"DDS " + bytes(124))],
                                  [garment_add.Variation("Blue", garment_add.png_bytes(bytes(16 * 16 * 4), 16, 16)),
                                   garment_add.Variation("Red", garment_add.png_bytes(bytes(16 * 16 * 4), 16, 16))])


def test_the_skeleton_template_is_asked_once_per_gender_and_kept(tmp_path, dct, api):
    ctrl = connected(tmp_path, dct, api)
    assert ctrl.skeletons.get("female") is None
    ctrl.skeletons.fetch("female")
    assert ctrl.skeletons.fetching("female")
    drive(ctrl, lambda: ctrl.skeletons.get("female") is not None)
    assert ctrl.skeletons.bones("female") == synthetic.skeleton_names()
    assert ctrl.skeletons.fetch("female") is None  # kept: nothing is asked again
    ctrl.disconnect()
    assert ctrl.skeletons.get("female") is not None  # kept for as long as Blender runs
    assert dct.templates_sent == ["female"]
    ctrl.connect()
    drive(ctrl, lambda: ctrl.ready)
    ctrl.skeletons.fetch("male")
    drive(ctrl, lambda: ctrl.skeletons.get("male") is not None)
    assert dct.templates_sent == ["female", "male"]
    assert "skeletons: female, male" in ctrl.diagnostics()
    ctrl.disconnect()


@pytest.mark.parametrize("code, key", [("game-required", "add.skeleton.game-required"), ("busy", "add.skeleton.busy"),
                                       ("unknown-message-type", "add.dct-too-old")])
def test_a_refused_template_says_what_to_do(tmp_path, dct, api, code, key):
    ctrl = connected(tmp_path, dct, api)
    dct.fail["skeleton.template"] = code
    ctrl.skeletons.fetch("male")
    drive(ctrl, lambda: "male" in ctrl.skeletons.problems)
    assert ctrl.skeletons.problems["male"].message.key == key and ctrl.skeletons.get("male") is None
    del dct.fail["skeleton.template"]
    ctrl.skeletons.fetch("male")  # asking again clears the problem
    assert "male" not in ctrl.skeletons.problems
    drive(ctrl, lambda: ctrl.skeletons.get("male") is not None)
    ctrl.disconnect()


def test_a_template_that_is_not_a_skeleton_is_not_kept(tmp_path, dct, api):
    ctrl = connected(tmp_path, dct, api)
    dct.skeleton_files = None  # the stand-in without bones
    ctrl.skeletons.fetch("male")
    drive(ctrl, lambda: "male" in ctrl.skeletons.problems)
    assert ctrl.skeletons.problems["male"].message.key == "add.skeleton.invalid" and ctrl.skeletons.get("male") is None
    ctrl.disconnect()


def test_the_skeleton_needs_a_connection(tmp_path, dct, api):
    ctrl = make_controller(tmp_path, dct, api, Stores())
    with pytest.raises(strings.UserError):
        ctrl.skeletons.fetch("male")
    assert ctrl.item_add.problem().key == "notice.connect-first"


def test_an_add_sends_the_cloth_and_links_the_answer(tmp_path, dct, api):
    ctrl = connected(tmp_path, dct, api)
    files, variations = add_files()
    linked = []
    dct.add_result = {"ok": True, "binding": dict(ADDED_BINDING),
                      "findings": [{"code": "non-power-of-two", "severity": "warning"},
                                   {"code": "rig-unchecked", "severity": "info"},
                                   {"code": "single-bone-rig", "severity": "error"}]}
    ctrl.item_add.start("jbib", "female", False, "Denim Jacket", variations, files, on_added=linked.append)
    assert ctrl.item_add.adding and ctrl.item_add.problem().key == "add.why.adding"
    drive(ctrl, lambda: not ctrl.item_add.adding)
    header, received = dct.item_adds[-1]
    assert (header["drawableType"], header["gender"], header["skin"], header["name"]) == ("jbib", "female", False,
                                                                                            "Denim Jacket")
    assert header["variations"] == [{"file": "variation_a.png", "name": "Blue"},
                                    {"file": "variation_b.png", "name": "Red"}]
    assert [(name, bytes(data)) for name, data in received] == [(name, bytes(data)) for name, data in files]
    assert linked == [ADDED_BINDING]
    status = ctrl.item_add.status
    assert status.level == "INFO" and status.message.key == "add.result.added"
    assert strings.english(status.message) == "Added Denim Jacket to the project as Top (jbib)."
    assert [f["code"] for f in ctrl.item_add.findings] == ["single-bone-rig", "non-power-of-two", "rig-unchecked"]
    assert ctrl.item_add.added["binding"] == ADDED_BINDING
    ctrl.disconnect()


@pytest.mark.parametrize("code, key, level", [
    ("item-limit", "add.result.item-limit", "WARNING"),
    ("no-project", "add.result.no-project", "ERROR"),
    ("item-refused", "add.result.item-refused", "ERROR"),
    ("busy", "add.result.busy", "WARNING"),
    ("rate-limited", "add.result.rate-limited", "WARNING"),
])
def test_an_add_durty_cloth_tool_refuses_says_why(tmp_path, dct, api, code, key, level):
    ctrl = connected(tmp_path, dct, api)
    files, variations = add_files()
    linked = []
    dct.fail["item.add"] = code
    ctrl.item_add.start("lowr", "male", True, "Cargo Pants", variations, files, on_added=linked.append)
    drive(ctrl, lambda: not ctrl.item_add.adding)
    assert (ctrl.item_add.status.level, ctrl.item_add.status.message.key) == (level, key)
    assert linked == [] and ctrl.item_add.added is None
    assert dct.item_adds[-1][0]["skin"] is True
    ctrl.disconnect()


def test_a_rejected_model_keeps_durty_cloth_tools_findings(tmp_path, dct, api):
    ctrl = connected(tmp_path, dct, api)
    files, variations = add_files()
    dct.add_result = {"ok": False, "code": "model-rejected",
                      "findings": [{"code": "not-multiple-of-four", "severity": "error"}]}
    ctrl.item_add.start("jbib", "male", False, "Jacket", variations, files)
    drive(ctrl, lambda: not ctrl.item_add.adding)
    assert ctrl.item_add.status.message.key == "add.result.rejected"
    assert ctrl.item_add.findings == [{"code": "not-multiple-of-four", "severity": "error"}]
    ctrl.disconnect()


def test_cancel_withdraws_the_add_while_durty_cloth_tool_asks(tmp_path, dct, api):
    ctrl = connected(tmp_path, dct, api)
    files, variations = add_files()
    dct.hold_adds = True  # Durty Cloth Tool's dialog stays open
    request = ctrl.item_add.start("feet", "male", False, "Boots", variations, files)
    drive(ctrl, lambda: bool(dct.item_adds))
    assert ctrl.item_add.cancel() is True and ctrl.item_add.withdrawing
    assert ctrl.item_add.status.message.key == "add.withdrawing"
    assert ctrl.item_add.cancel() is False  # one withdrawal per add
    drive(ctrl, lambda: not ctrl.item_add.adding)
    assert dct.add_cancels == [request.id]
    assert ctrl.item_add.status.message.key == "add.result.withdrawn" and ctrl.item_add.added is None
    ctrl.disconnect()


def test_the_user_choosing_cancel_in_durty_cloth_tool_is_said(tmp_path, dct, api):
    ctrl = connected(tmp_path, dct, api)
    files, variations = add_files()
    dct.hold_adds = True
    ctrl.item_add.start("accs", "female", False, "Tank Top", variations, files)
    drive(ctrl, lambda: bool(dct.item_adds))
    dct.release_adds({"ok": False, "code": "request-denied", "findings": []})
    drive(ctrl, lambda: not ctrl.item_add.adding)
    assert ctrl.item_add.status.message.key == "add.result.denied"
    ctrl.disconnect()


def test_a_lost_connection_during_the_add_is_said(tmp_path, dct, api):
    ctrl = connected(tmp_path, dct, api)
    files, variations = add_files()
    dct.hold_adds = True
    ctrl.item_add.start("jbib", "male", False, "Jacket", variations, files)
    drive(ctrl, lambda: bool(dct.item_adds))
    dct.drop_all()
    drive(ctrl, lambda: not ctrl.item_add.adding)
    assert ctrl.item_add.status.message.key == "add.result.disconnected"
    ctrl.disconnect()


def test_an_add_needs_a_project_and_a_valid_request(tmp_path, dct, api):
    ctrl = connected(tmp_path, dct, api)
    files, variations = add_files()
    with pytest.raises(strings.UserError) as refused:
        ctrl.item_add.start("jbib", "male", False, "", variations, files)  # dct_link's own rules
    assert refused.value.message.key == "add.invalid"
    dct.broadcast({"type": "event.project", "id": "prj1", "project": None})
    drive(ctrl, lambda: ctrl.project is None)
    assert ctrl.item_add.problem().key == "add.why.no-project"
    with pytest.raises(strings.UserError):
        ctrl.item_add.start("jbib", "male", False, "Jacket", variations, files)
    assert dct.item_adds == []
    ctrl.disconnect()


# ---- late answers, an older Durty Cloth Tool and a full-size skeleton ---------------------------------------------


def test_a_cloth_added_after_the_cancel_is_still_linked(tmp_path, dct, api, monkeypatch):
    # The user chose Add in Durty Cloth Tool a moment before the cancel arrived, and the import took longer than the
    # add-on waits: the answer comes after the panel stopped showing the add (dct_link reports it as item-add-late).
    monkeypatch.setattr(link_session, "_ADD_CANCEL_GRACE_SECONDS", 0.2)
    ctrl = connected(tmp_path, dct, api)
    files, variations = add_files()
    linked = []
    dct.hold_adds = True
    dct.ignore_cancels = True
    ctrl.item_add.start("jbib", "male", False, "Late Jacket", variations, files, on_added=linked.append)
    drive(ctrl, lambda: bool(dct.item_adds))
    assert ctrl.item_add.cancel()
    drive(ctrl, lambda: not ctrl.item_add.adding)
    assert ctrl.item_add.status.message.key == "add.result.cancel-unanswered" and linked == []
    assert ctrl.item_add.problem() is None  # another add may start meanwhile
    dct.add_result = {"ok": True, "binding": dict(ADDED_BINDING), "findings": []}
    dct.release_adds()
    drive(ctrl, lambda: bool(linked))
    assert linked == [ADDED_BINDING] and ctrl.item_add.added["binding"] == ADDED_BINDING
    assert ctrl.item_add.status.message.key == "add.result.added-late"
    ctrl.disconnect()


def test_an_add_left_waiting_too_long_is_withdrawn_and_a_late_answer_still_counts(tmp_path, dct, api, monkeypatch):
    monkeypatch.setattr(link_session, "_ADD_CANCEL_GRACE_SECONDS", 0.2)
    ctrl = connected(tmp_path, dct, api)
    ctrl.item_add.TIMEOUT = 0.2
    files, variations = add_files()
    linked = []
    dct.hold_adds = True
    dct.ignore_cancels = True
    request = ctrl.item_add.start("jbib", "female", False, "Slow Coat", variations, files, on_added=linked.append)
    drive(ctrl, lambda: not ctrl.item_add.adding)
    assert dct.add_cancels == [request.id]
    assert ctrl.item_add.status.message.key == "add.result.timeout"
    dct.release_adds()
    drive(ctrl, lambda: bool(linked))
    assert ctrl.item_add.status.message.key == "add.result.added-late"
    ctrl.disconnect()


def test_a_late_refusal_confirms_the_cancel(tmp_path, dct, api, monkeypatch):
    monkeypatch.setattr(link_session, "_ADD_CANCEL_GRACE_SECONDS", 0.2)
    ctrl = connected(tmp_path, dct, api)
    files, variations = add_files()
    dct.hold_adds = True
    dct.ignore_cancels = True
    ctrl.item_add.start("feet", "male", False, "Boots", variations, files)
    drive(ctrl, lambda: bool(dct.item_adds))
    ctrl.item_add.cancel()
    drive(ctrl, lambda: not ctrl.item_add.adding)
    dct.release_adds({"ok": False, "code": "request-denied", "findings": []})
    drive(ctrl, lambda: ctrl.item_add.status.message.key == "add.result.withdrawn")
    assert ctrl.item_add.added is None
    ctrl.disconnect()


def test_a_durty_cloth_tool_that_cannot_read_the_add_says_so_at_once(tmp_path, dct, api):
    ctrl = connected(tmp_path, dct, api)
    files, variations = add_files()
    dct.unknown_types = {"item.add", "skeleton.template"}
    ctrl.item_add.start("jbib", "male", False, "Jacket", variations, files)
    drive(ctrl, lambda: not ctrl.item_add.adding, timeout=5.0)  # answered by its id, never a 15-minute wait
    assert ctrl.item_add.status.message.key == "add.dct-too-old"
    ctrl.skeletons.fetch("male")
    drive(ctrl, lambda: "male" in ctrl.skeletons.problems, timeout=5.0)
    assert ctrl.skeletons.problems["male"].message.key == "add.dct-too-old"
    assert dct.refused_frames == [("item.add", "unknown-message-type"), ("skeleton.template", "unknown-message-type")]
    assert ctrl.ready  # the connection stays
    ctrl.disconnect()


def test_a_full_size_skeleton_keeps_its_order_and_joints():
    bones = synthetic.skeleton_bones_128()
    xml = synthetic.skeleton_template_xml("male", bones)
    names = garment_add.template_bones(xml)
    assert len(names) == 128 and names == [name for name, _, _ in bones]
    assert garment_add.armature_problem(names, names) is None
    swapped = names[:]
    swapped[5], swapped[6] = swapped[6], swapped[5]
    assert garment_add.armature_problem(swapped, names).key == "add.skeleton.order"
    # Depth first: every bone comes after its parent, and a parent's subtree is one block.
    parents = [parent for _, parent, _ in bones]
    assert all(parent < index for index, parent in enumerate(parents) if parent >= 0)
    joints = garment_add.template_joints(xml)
    heads = synthetic.joints_of(bones)
    assert set(joints) == set(heads)
    assert all(np.linalg.norm(np.array(joints[name]) - np.array(heads[name])) < 1e-5 for name in heads)


def test_the_payload_is_estimated_before_any_picture_is_written():
    least, most = garment_add.payload_estimate(1000, [(2048, 2048), (16, 16)])
    assert least == 1000 and most >= 1000 + 2048 * 2048 * 4 + 16 * 16 * 4
    picture = garment_add.png_bytes(np.random.default_rng(1).integers(0, 255, 64 * 64 * 4, dtype=np.uint8), 64, 64)
    assert len(picture) <= garment_add.payload_estimate(0, [(64, 64)])[1]
