# SPDX-License-Identifier: GPL-3.0-or-later
"""Custom Ped against a fake Durty Cloth Tool, without Blender: the template list, the rig with its progress, Cancel,
refusals and result, and sending the character (the chunked upload, Durty Cloth Tool's answers, Cancel). Everything
is driven by polling, as Blender's timer does."""

from __future__ import annotations

import hashlib
import struct
import time
from typing import Callable

import numpy as np
import pytest

from durty_cloth_tool_link import link, ped, ped_link, strings
from durty_cloth_tool_link.dct_link import protocol
from durty_cloth_tool_link.dct_link import session as link_session
from durty_cloth_tool_link.strings import UserError
from tests.support import fake_dct, mannequin
from tests.support.fake_dct import FakeDct
from tests.support.fake_link_api import FakeLinkApi
from tests.test_link import Stores, make_controller


@pytest.fixture
def dct():
    with FakeDct() as server:
        yield server


@pytest.fixture
def api():
    with FakeLinkApi() as server:
        yield server


def drive(ctrl: link.LinkController, until: Callable[[], bool], timeout: float = 20.0) -> None:
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        ctrl.poll()
        if until():
            return
        time.sleep(0.005)
    peds = ctrl.peds
    raise AssertionError(f"timed out; rig: {peds.rig_status}; add: {peds.add_status}; templates: "
                         f"{peds.templates_problem}")


def connected(tmp_path, dct: FakeDct, api: FakeLinkApi) -> link.LinkController:
    dct.on_assist = api.approve
    ctrl = make_controller(tmp_path, dct, api, Stores())
    ctrl.peds = ped_link.PedLink(ctrl)
    ctrl.connect()
    drive(ctrl, lambda: ctrl.ready and ctrl.project is not None)
    return ctrl


def character_input():
    character = mannequin.mannequin(45.0)
    data = ped.rig_input([ped.Part(p.name, p.role, p.positions, p.triangles) for p in character.parts])
    return character, data


def english(notice) -> str:
    return strings.english(notice.message)


# ---- templates --------------------------------------------------------------------------------------------


def test_templates_list_ambient_peds_and_more_with_show_all(tmp_path, dct, api):
    ctrl = connected(tmp_path, dct, api)
    peds = ctrl.peds
    peds.fetch_templates(None, False)
    assert peds.loading_templates
    drive(ctrl, lambda: peds.templates is not None)
    models = [t["model"] for t in peds.templates]
    assert models[:2] == ["a_m_y_tester_01", "a_f_y_tester_01"] and "mp_m_freemode_01" not in models
    assert peds.template("A_M_Y_TESTER_01")["recommended"] is True
    peds.fetch_templates("male", True)
    drive(ctrl, lambda: peds.templates_for == ("male", True))
    assert {t["model"] for t in peds.templates} == {"a_m_y_tester_01", "a_m_m_tester_02", "mp_m_freemode_01"}
    assert dct.ped_template_requests[-1]["gender"] == "male" and dct.ped_template_requests[-1]["all"] is True


def test_every_installed_template_is_listed_with_its_count(tmp_path, dct, api):
    """Durty Cloth Tool listed at most 200 templates and the panel said "Choose a gender to see others" even with
    Male chosen, while a real game has more than 400 male ambient peds: the whole list arrives (in pages) and the
    panel counts it in the words of its filters."""
    dct.ped_templates = [{"model": f"a_m_y_tester_{i:03d}", "gender": "male", "pedType": "CIVMALE", "layout": "packed",
                          "group": "ambient", "recommended": i < 5} for i in range(418)]
    ctrl = connected(tmp_path, dct, api)
    peds = ctrl.peds
    peds.fetch_templates("male", False)
    drive(ctrl, lambda: peds.templates is not None)
    assert [t["model"] for t in peds.templates] == [t["model"] for t in dct.ped_templates]
    assert not peds.truncated and len(dct.ped_template_requests) == 2
    assert strings.english(peds.listed()) == "418 male ambient peds"
    peds.templates_for = (None, True)
    assert strings.english(peds.listed()) == "418 peds"
    peds.templates, peds.templates_for = peds.templates[:1], ("female", False)
    assert strings.english(peds.listed()) == "1 female ambient ped"


def test_templates_say_when_durty_cloth_tool_has_no_game_folder(tmp_path, dct, api):
    dct.fail["ped.templates"] = "game-required"
    ctrl = connected(tmp_path, dct, api)
    ctrl.peds.fetch_templates(None, False)
    drive(ctrl, lambda: ctrl.peds.templates_problem is not None)
    assert ctrl.peds.templates_problem.message == strings.msg("error.game-required")
    assert ctrl.peds.templates is None


def test_a_durty_cloth_tool_without_custom_peds_says_to_update(tmp_path, dct, api):
    dct.unknown_types = {"ped.templates"}
    ctrl = connected(tmp_path, dct, api)
    ctrl.peds.fetch_templates(None, False)
    drive(ctrl, lambda: ctrl.peds.templates_problem is not None)
    assert ctrl.peds.templates_problem.message.key == "ped.error.dct-too-old"


def test_nothing_is_asked_without_a_connection(tmp_path, dct, api):
    ctrl = make_controller(tmp_path, dct, api, Stores())
    ctrl.peds = ped_link.PedLink(ctrl)
    assert ctrl.peds.feature(ped_link.FEATURE_RIG).key == "ped.why.connect"
    with pytest.raises(UserError):
        ctrl.peds.fetch_templates(None, False)
    assert ctrl.peds.auto_templates(None, False) is None and not ctrl.peds.loading_templates


def test_the_rig_stage_lists_the_templates_by_itself_and_tries_again_quietly(tmp_path, dct, api):
    """An empty template list made Refresh the next step although nothing else could be done there: the Rig stage
    now asks for the list itself. A failed try (Durty Cloth Tool without its game folder yet) is tried again a few
    times, later each time, without a message of its own, and then left to Refresh."""
    dct.fail["ped.templates"] = "game-required"
    ctrl = connected(tmp_path, dct, api)
    peds = ctrl.peds
    now = 1000.0
    assert peds.wants_templates(None, False)
    assert peds.auto_templates(None, False, now) == peds.AUTO_POLL and peds.loading_templates
    assert peds.auto_templates(None, False, now) == peds.AUTO_POLL  # one request at a time
    drive(ctrl, lambda: peds.templates_problem is not None)
    assert peds.auto_templates(None, False, now + 1.0) == pytest.approx(peds.AUTO_RETRIES[0] - 1.0)
    assert not peds.loading_templates  # waits before trying again
    for retry, wait in enumerate(peds.AUTO_RETRIES):
        now += wait
        assert peds.auto_templates(None, False, now) == peds.AUTO_POLL, retry
        drive(ctrl, lambda: not peds.loading_templates)
    assert peds.auto_templates(None, False, now + 3600.0) is None and not peds.loading_templates
    assert not peds.wants_templates(None, False)  # Refresh is left
    assert peds.wants_templates("male", False)  # other filters start again
    # Durty Cloth Tool has its game folder now: the next connection lists the templates by itself, once.
    del dct.fail["ped.templates"]
    ctrl.disconnect()
    ctrl.connect()
    drive(ctrl, lambda: ctrl.ready)
    assert peds.auto_templates(None, False, now) == peds.AUTO_POLL
    drive(ctrl, lambda: peds.templates is not None)
    assert peds.templates_problem is None and peds.templates_for == (None, False)
    assert peds.auto_templates(None, False, now) is None and not peds.wants_templates(None, False)
    assert len(dct.ped_template_requests) == 1


# ---- the rig ----------------------------------------------------------------------------------------------


def test_a_rig_reports_its_progress_and_arrives_whole(tmp_path, dct, api):
    dct.ped_rig_seconds = 0.6
    ctrl = connected(tmp_path, dct, api)
    peds = ctrl.peds
    character, data = character_input()
    options = ped.rig_options(fingers="auto")
    peds.start_rig("a_m_y_tester_01", character.joints, data, options, rights=True, character="c1")
    assert peds.rigging and peds.busy and peds.rig_problem().key == "ped.why.rigging"
    stages = set()
    drive(ctrl, lambda: (stages.add(peds.stage) if peds.stage else None) or not peds.rigging)
    assert {"template", "weights", "report"} <= stages
    assert peds.rig is not None and peds.rig_status is None and peds.job == "j1"
    header, size = dct.ped_rigs[-1]
    assert header["rights"] is True and header["template"] == "a_m_y_tester_01"
    assert header["options"] == {"fingers": "auto"} and header["mesh"]["parts"] == ["body", "head", "hair", "eyes"]
    assert set(header["markers"]) == set(ped.BODY_MARKERS)
    assert size == 12 * data.vertices + 12 * data.triangle_count + data.vertices
    rig, sent = peds.take_rig()
    assert sent["character"] == "c1" and sent["topology"] == data.topology and sent["ranges"] == data.ranges
    assert peds.rig is None
    assert [b.name for b in rig.bones] == [b[0] for b in fake_dct.PED_BONES]
    assert len(rig.rest_positions) == 3 * data.vertices
    weights = np.frombuffer(rig.weights, dtype=np.uint8).reshape(-1, 4)
    assert (weights.sum(axis=1) == 255).all()
    indices = np.frombuffer(rig.bone_indices, dtype=np.uint8).reshape(-1, 4)
    names = [b.name for b in rig.bones]
    assert not any(ped.non_deforming(names[i]) for i in indices[:, 0])
    # The report's lines and the markers the rig moved.
    lines = ped.report_lines(rig.report)
    assert lines[0].key == "ped.result.ready"
    moved = dict(ped.refined_moves(rig.report, sent["markers"]))
    assert set(moved) == {"elbowL", "elbowR"} and moved["elbowL"] == pytest.approx(0.02, abs=1e-6)
    # The armature plan and the pose from what arrived.
    plan = ped.armature_plan(rig.bones, rig.poses)
    rest = [p.rest for p in plan]
    parents = [p.parent for p in plan]
    bases = ped.pose_bases(rest, [p.pose for p in plan], parents)
    assert bases[0][:3, 3] != pytest.approx((0.0, 0.0, 0.0))  # the pose moves the character where it stands


def test_a_rig_job_is_named_only_on_its_own_connection(tmp_path, dct, api):
    ctrl = connected(tmp_path, dct, api)
    peds = ctrl.peds
    character, data = character_input()
    peds.start_rig("a_m_y_tester_01", character.joints, data, {}, rights=True, character="c1")
    drive(ctrl, lambda: peds.rig is not None)
    assert peds.rig_job("j1", "c1") == "j1"
    assert peds.rig_job("j1", "c2") is None and peds.rig_job(None, "c1") is None
    # A new connection starts its job names again: the old job could name another character's rig there.
    dct.drop_all()
    drive(ctrl, lambda: not ctrl.ready)
    drive(ctrl, lambda: ctrl.ready, timeout=30)
    assert peds.rig_job("j1", "c1") is None


def test_cancel_stops_the_rig(tmp_path, dct, api):
    dct.ped_rig_seconds = 6.0
    ctrl = connected(tmp_path, dct, api)
    peds = ctrl.peds
    character, data = character_input()
    peds.start_rig("a_m_y_tester_01", character.joints, data, {}, rights=True, character="c1")
    drive(ctrl, lambda: peds.job is not None)
    assert peds.cancel_rig()
    assert english(peds.rig_status) == "Cancelling the rig."
    drive(ctrl, lambda: not peds.rigging, timeout=10)
    assert peds.rig is None and peds.rig_status.message.key == "ped.error.rig-cancelled"
    assert peds.rig_status.level == "INFO" and dct.ped_rig_cancels


def test_a_refused_rig_names_its_reasons_and_markers(tmp_path, dct, api):
    dct.ped_rig_refusal = ("rig-refused", [{"code": "marker_side", "markers": ["shoulderL", "shoulderR"],
                                            "message": "swapped"}, {"code": "limb_length", "markers": ["kneeL"]}])
    ctrl = connected(tmp_path, dct, api)
    character, data = character_input()
    ctrl.peds.start_rig("a_m_y_tester_01", character.joints, data, {}, rights=True, character="c1")
    drive(ctrl, lambda: not ctrl.peds.rigging)
    assert ctrl.peds.rig is None and ctrl.peds.rig_status.message.key == "ped.error.rig-refused"
    assert [(l.key, l.markers) for l in ctrl.peds.refusal] == [
        ("ped.refusal.marker_side", ("shoulderL", "shoulderR")), ("ped.refusal.limb_length", ("kneeL",))]


@pytest.mark.parametrize("code, key, level", [
    ("needs-ultimate", "ped.plan.rig", "WARNING"), ("busy", "ped.error.rig-busy", "WARNING"),
    ("game-required", "error.game-required", "ERROR"), ("mesh-too-large", "error.mesh-too-large", "ERROR"),
    ("template-not-found", "error.template-not-found", "ERROR"),
])
def test_rig_answers_in_words(tmp_path, dct, api, code, key, level):
    dct.ped_rig_refusal = (code, [])
    ctrl = connected(tmp_path, dct, api)
    character, data = character_input()
    ctrl.peds.start_rig("a_m_y_tester_01", character.joints, data, {}, rights=True, character="c1")
    drive(ctrl, lambda: not ctrl.peds.rigging)
    assert ctrl.peds.rig_status == link.Notice(level, strings.msg(key))


def test_rigging_needs_ultimate(tmp_path, dct, api):
    ctrl = connected(tmp_path, dct, api)
    dct.set_features(pedRig="needsUltimate")
    drive(ctrl, lambda: ctrl.session.features.get("dct.link.pedRig") == "needsUltimate")
    assert ctrl.peds.rig_problem() == strings.msg("ped.plan.rig")
    assert strings.english(ctrl.peds.rig_problem()) == "Rigging is included in Durty Cloth Tool Ultimate."
    character, data = character_input()
    with pytest.raises(UserError) as refused:
        ctrl.peds.start_rig("a_m_y_tester_01", character.joints, data, {}, rights=True, character="c1")
    assert refused.value.message.key == "ped.plan.rig" and not dct.ped_rigs
    assert ctrl.peds.feature(ped_link.FEATURE_ADD) is None and ctrl.peds.feature(ped_link.FEATURE_TEMPLATES) is None


def test_a_rig_without_the_rights_confirmation_is_not_sent(tmp_path, dct, api):
    ctrl = connected(tmp_path, dct, api)
    character, data = character_input()
    with pytest.raises(UserError) as refused:
        ctrl.peds.start_rig("a_m_y_tester_01", character.joints, data, {}, rights=False, character="c1")
    assert refused.value.message.key == "ped.invalid" and not dct.ped_rigs


def test_a_lost_connection_ends_the_rig(tmp_path, dct, api):
    dct.ped_rig_seconds = 6.0
    ctrl = connected(tmp_path, dct, api)
    character, data = character_input()
    ctrl.peds.start_rig("a_m_y_tester_01", character.joints, data, {}, rights=True, character="c1")
    drive(ctrl, lambda: ctrl.peds.job is not None)
    dct.drop_all()
    drive(ctrl, lambda: not ctrl.peds.rigging)
    assert ctrl.peds.rig_status.message.key == "ped.error.rig-disconnected"


# ---- sending ----------------------------------------------------------------------------------------------


def glb(size: int) -> bytes:
    body = bytes(i % 251 for i in range(size - 12))
    return b"glTF" + struct.pack("<II", 2, size) + body


def test_the_character_is_sent_and_durty_cloth_tool_creates_the_project(tmp_path, dct, api):
    ctrl = connected(tmp_path, dct, api)
    peds = ctrl.peds
    data = glb(5000)
    peds.start_add("a_m_y_tester_01", "Hero", "my_hero", data, rights=True, rig="j1", ragdoll="fred-large",
                   parts=[("Hair", "hair"), ("Eyes", "eyes")], character="c1")
    assert peds.sending and peds.add_status.message.key == "ped.send.waiting"
    drive(ctrl, lambda: not peds.sending)
    header, received = dct.ped_adds[-1]
    assert received == data and header["sha256"] == hashlib.sha256(data).hexdigest() and header["chunks"] == 1
    assert header["rights"] is True and header["rig"] == "j1" and header["ragdoll"] == "fred-large"
    assert header["parts"] == [{"mesh": "Hair", "role": "hair"}, {"mesh": "Eyes", "role": "eyes"}]
    assert peds.created == {"name": "Hero", "model": "my_hero", "template": "a_m_y_tester_01", "character": "c1"}
    assert english(peds.add_status) == ("Durty Cloth Tool created the project Hero with the ped my_hero from "
                                        "a_m_y_tester_01.")


def test_a_large_character_travels_in_chunks(tmp_path, dct, api):
    ctrl = connected(tmp_path, dct, api)
    data = glb(protocol.MAX_PED_ADD_CHUNK_BYTES + 4096)
    ctrl.peds.start_add("a_m_y_tester_01", "Hero", "my_hero", data, rights=True, rig=None, ragdoll=None, parts=[],
                        character="c1")
    drive(ctrl, lambda: not ctrl.peds.sending, timeout=60)
    header, received = dct.ped_adds[-1]
    assert header["chunks"] == 2 and received == data and "parts" not in header and "rig" not in header
    assert ctrl.peds.created is not None


def test_cancel_withdraws_the_character_while_durty_cloth_tool_asks(tmp_path, dct, api):
    dct.hold_ped_adds = True
    ctrl = connected(tmp_path, dct, api)
    peds = ctrl.peds
    peds.start_add("a_m_y_tester_01", "Hero", "my_hero", glb(2000), rights=True, rig=None, ragdoll=None, parts=[],
                   character="c1")
    drive(ctrl, lambda: bool(dct.ped_adds))
    assert peds.cancel_add() and peds.add_status.message.key == "ped.send.withdrawing"
    drive(ctrl, lambda: not peds.sending)
    assert peds.add_status.message.key == "ped.send.withdrawn" and peds.created is None


@pytest.mark.parametrize("result, key, level", [
    ({"ok": False, "code": "request-denied", "findings": []}, "ped.error.add-denied", "INFO"),
    ({"ok": False, "code": "model-rejected",
      "findings": [{"code": "rig-mismatch", "severity": "error"}, {"code": "ped-budget", "severity": "warning"}]},
     "ped.error.model-rejected", "ERROR"),
    ({"ok": False, "code": "save-failed", "findings": []}, "ped.error.save-failed", "ERROR"),
    ({"ok": False, "code": "busy", "findings": []}, "ped.error.add-busy", "WARNING"),
])
def test_durty_cloth_tools_answers_in_words(tmp_path, dct, api, result, key, level):
    dct.ped_add_result = result
    ctrl = connected(tmp_path, dct, api)
    ctrl.peds.start_add("a_m_y_tester_01", "Hero", "my_hero", glb(2000), rights=True, rig=None, ragdoll=None, parts=[],
                        character="c1")
    drive(ctrl, lambda: not ctrl.peds.sending)
    assert ctrl.peds.add_status == link.Notice(level, strings.msg(key))
    assert [f["code"] for f in ctrl.peds.findings] == [f["code"] for f in result["findings"]]
    for finding in ctrl.peds.findings:
        assert strings.english(ped_link.finding_text(finding["code"]))


def test_creating_a_project_needs_advanced_or_ultimate(tmp_path, dct, api):
    ctrl = connected(tmp_path, dct, api)
    dct.set_features(pedAdd="needsLicense")
    drive(ctrl, lambda: ctrl.session.features.get("dct.link.pedAdd") == "needsLicense")
    assert strings.english(ctrl.peds.add_problem()) == (
        "Creating a custom ped project needs Durty Cloth Tool Advanced or Ultimate.")
    with pytest.raises(UserError):
        ctrl.peds.start_add("a_m_y_tester_01", "Hero", "my_hero", glb(2000), rights=True, rig=None, ragdoll=None,
                            parts=[], character="c1")
    assert not dct.ped_add_headers


def test_a_bad_model_name_is_refused_before_anything_is_sent(tmp_path, dct, api):
    ctrl = connected(tmp_path, dct, api)
    with pytest.raises(UserError) as refused:
        ctrl.peds.start_add("a_m_y_tester_01", "Hero", "Hero", glb(2000), rights=True, rig=None, ragdoll=None,
                            parts=[], character="c1")
    assert refused.value.message.key == "ped.invalid" and not dct.ped_add_headers


def test_a_project_created_after_the_cancel_is_still_linked(tmp_path, dct, api, monkeypatch):
    # The user chose Create in Durty Cloth Tool a moment before the cancel arrived, and creating the project took
    # longer than the add-on waits: dct_link reports the answer as ped-add-late.
    monkeypatch.setattr(link_session, "_ADD_CANCEL_GRACE_SECONDS", 0.2)
    ctrl = connected(tmp_path, dct, api)
    peds = ctrl.peds
    linked = []
    peds.on_created = linked.append
    dct.hold_ped_adds = True
    dct.ignore_cancels = True
    peds.start_add("a_m_y_tester_01", "Hero", "my_hero", glb(2000), rights=True, rig=None, ragdoll=None, parts=[],
                   character="c1")
    drive(ctrl, lambda: bool(dct.ped_adds))
    assert peds.cancel_add()
    drive(ctrl, lambda: not peds.sending)
    assert peds.add_status.message.key == "ped.error.add-unanswered" and peds.created is None and not linked
    assert peds.add_problem() is None  # another send may start meanwhile
    dct.release_ped_adds()
    drive(ctrl, lambda: bool(linked))
    assert linked == [{"name": "Hero", "model": "my_hero", "template": "a_m_y_tester_01", "character": "c1"}]
    assert peds.add_status == link.Notice("WARNING", strings.msg("ped.send.created-late", name="Hero",
                                                                 model="my_hero"))
    ctrl.disconnect()


def test_a_late_refusal_confirms_the_withdrawal(tmp_path, dct, api, monkeypatch):
    monkeypatch.setattr(link_session, "_ADD_CANCEL_GRACE_SECONDS", 0.2)
    ctrl = connected(tmp_path, dct, api)
    peds = ctrl.peds
    dct.hold_ped_adds = True
    dct.ignore_cancels = True
    peds.start_add("a_m_y_tester_01", "Hero", "my_hero", glb(2000), rights=True, rig=None, ragdoll=None, parts=[],
                   character="c1")
    drive(ctrl, lambda: bool(dct.ped_adds))
    peds.cancel_add()
    drive(ctrl, lambda: not peds.sending)
    dct.release_ped_adds({"ok": False, "code": "request-denied", "findings": []})
    drive(ctrl, lambda: peds.add_status.message.key == "ped.send.withdrawn")
    assert peds.created is None
    ctrl.disconnect()


def test_another_file_withdraws_what_runs(tmp_path, dct, api):
    dct.hold_ped_adds = True
    dct.ped_rig_seconds = 6.0
    ctrl = connected(tmp_path, dct, api)
    peds = ctrl.peds
    character, data = character_input()
    peds.start_rig("a_m_y_tester_01", character.joints, data, {}, rights=True, character="c1")
    peds.start_add("a_m_y_tester_01", "Hero", "my_hero", glb(2000), rights=True, rig=None, ragdoll=None, parts=[],
                   character="c1")
    drive(ctrl, lambda: peds.job is not None and bool(dct.ped_adds))
    peds.forget()
    drive(ctrl, lambda: not peds.busy, timeout=15)
    assert dct.ped_rig_cancels and dct.ped_add_cancels and peds.rig is None and peds.created is None
