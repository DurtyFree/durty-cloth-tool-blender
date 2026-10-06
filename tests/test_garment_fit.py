# SPDX-License-Identifier: GPL-3.0-or-later
"""Fit to Body and Transfer Weights on gta.clothing, without Blender: what is uploaded, how a run goes (busy, Cancel,
failures, a file closed meanwhile), what comes back as weights, the fits left today, the fit check's usual ranges and
the texts for every answer. The service is the fake of tests/support/fake_link_api.py; nothing reaches the network."""

from __future__ import annotations

import json
import pathlib
import re
import time
from typing import Callable

import numpy as np
import pytest

from durty_cloth_tool_link import garment_fit, strings
from durty_cloth_tool_link.dct_link import auth, fit
from durty_cloth_tool_link.strings import EN
from tests.support import synthetic
from tests.support.fake_link_api import FakeLinkApi
from tests.test_link import Stores, make_controller

REPO = pathlib.Path(__file__).resolve().parent.parent


@pytest.fixture
def api():
    with FakeLinkApi() as server:
        yield server


def signed_in(tmp_path, api, online: Callable[[], bool] = lambda: True):
    """A controller signed in with gta.clothing (no Durty Cloth Tool needed for fitting)."""
    ctrl = make_controller(tmp_path, _NoDct(), api, Stores(), online=online)
    ctrl.prepare()
    with api.lock:
        tokens = api._tokens("sess-fit")
    ctrl.link_auth._store(auth._validate_tokens(tokens, ctrl.link_auth._clock()))
    ctrl.refresh_account()
    return ctrl


class _NoDct:
    port = 9


def until(ctrl, condition, timeout: float = 15.0) -> None:
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        ctrl.poll()
        if condition():
            return
        time.sleep(0.01)
    raise AssertionError(f"timed out; run: {ctrl.fitting.run and ctrl.fitting.run.state}")


def garment_upload():
    mesh = synthetic.top(arm_angle=0.0, offset=(0.0, 0.0, 0.0))
    return garment_fit.prepare_upload(mesh.positions, synthetic.triangles(mesh.faces)), mesh


def request(operation="fit", category="tshirt", markers=None, mesh=None):
    joints = (mesh or synthetic.top()).joints if markers is None else markers
    return garment_fit.build_request(operation, "male", "jbib", category, "1", joints,
                                     garment_fit.fit_options(3, True, 30, 1.5, False))


class Ended:
    """Stands in for the add-on's result handler; records each run that ended."""

    def __init__(self) -> None:
        self.runs = []

    def __call__(self, run) -> bool:
        self.runs.append(run)
        return True


# ---- what is uploaded -----------------------------------------------------------------------------------------------


def test_the_markers_go_by_the_services_names_and_only_whole_limbs():
    markers = {"neck": (0, 0, 0.6), "chest": (0, 0, 0.45), "pelvis": (0, 0, 0), "shoulder_l": (0.2, 0, 0.5),
               "elbow_l": (0.4, 0, 0.5), "wrist_l": (0.6, 0, 0.5), "shoulder_r": (-0.2, 0, 0.5),
               "elbow_r": (-0.4, 0, 0.5), "wrist_r": (-0.6, 0, 0.5), "hip_l": (0.1, 0, 0), "hip_r": (-0.1, 0, 0)}
    named = garment_fit.service_markers(markers)
    # A top's hip markers have no knees or ankles: those chains stay home, or the service would refuse them.
    assert set(named) == {"neck", "chest", "pelvis", "lShoulder", "lElbow", "lWrist", "rShoulder", "rElbow", "rWrist"}
    assert named["lWrist"] == [0.6, 0.0, 0.5]
    built = request(markers=markers)
    assert built["sourcePose"] == "rest" and built["category"] == "top" and built["markers"] == named
    weights = request("weights", markers=markers)
    assert "markers" not in weights and weights["options"] == {"seamWeldMm": 1.5}


def test_the_upload_leaves_out_triangles_the_service_refuses_and_keeps_the_flags():
    positions = np.array([[0, 0, 0], [0.1, 0, 0], [0, 0.1, 0], [0.1, 0.1, 0], [0.2, 0, 0], [0, 0, 0]], dtype=float)
    triangles = np.array([
        [0, 1, 2],  # kept
        [1, 3, 2],  # kept
        [2, 0, 1],  # the first one again, turned: refused as a repeat
        [2, 1, 0],  # the first one's back face: allowed
        [0, 1, 4],  # its corners on one line: no area
        [5, 1, 2],  # vertex 5 lies where vertex 0 does: a repeat by position
        [1, 1, 2],  # names a vertex twice
    ])
    pinned = np.array([True, False, False, False, False, False])
    lining = np.array([False, True, False, False, False, False])
    upload = garment_fit.prepare_upload(positions, triangles, pinned, lining)
    assert upload.triangles.tolist() == [[0, 1, 2], [1, 3, 2], [2, 1, 0]] and upload.dropped == 4
    assert upload.flags.tolist() == [fit.FLAG_PINNED, fit.FLAG_LINING, 0, 0, 0, 0]
    assert upload.positions.dtype == np.float32 and upload.mesh().vertex_count == 6
    assert garment_fit.prepare_upload(positions, triangles).flags is None
    # The digest belongs to the shape as it is in Blender, before anything was left out.
    assert upload.digest == garment_fit.mesh_digest(positions, triangles)
    assert upload.digest != garment_fit.mesh_digest(positions + 0.001, triangles)


@pytest.mark.parametrize("change, key", [
    (lambda p, t: (np.zeros((120001, 3)), np.array([[0, 1, 2]])), "fit.input.too-large"),
    (lambda p, t: (np.where(np.arange(len(p))[:, None] == 3, np.nan, p), t), "fit.input.broken"),
    (lambda p, t: (p + np.array([0.0, 0.0, 3.5]), t), "fit.input.far"),
    (lambda p, t: (np.zeros_like(p), t), "fit.input.degenerate"),
])
def test_a_garment_the_service_would_refuse_is_never_sent(change, key):
    mesh = synthetic.top()
    positions, triangles = change(mesh.positions, synthetic.triangles(mesh.faces))
    with pytest.raises(strings.UserError) as refused:
        garment_fit.prepare_upload(positions, triangles)
    assert refused.value.message.key == key


# ---- runs against the fake service ----------------------------------------------------------------------------------


def test_fit_to_body_uploads_polls_and_hands_back_the_garment_with_weights(tmp_path, api):
    api.fit.position_offset = (0.0, 0.0, 0.002)
    ctrl = signed_in(tmp_path, api)
    ended = Ended()
    ctrl.fitting.on_ended = ended
    upload, mesh = garment_upload()
    run = ctrl.fitting.start("fit", request(mesh=mesh), upload, ("Scene", 7))
    assert ctrl.fitting.busy and run.status_text().key == "fit.stage.uploading"
    seen = set()
    until(ctrl, lambda: seen.add(run.status_text().key) or bool(ended.runs))
    assert {"fit.stage.validating", "fit.stage.transferring", "fit.stage.weighting"} <= seen
    assert run.state == "done" and run.fraction() == 1.0 and not ctrl.fitting.busy
    moved = garment_fit.result_positions(run.result)
    assert np.allclose(moved, upload.positions + np.array([0, 0, 0.002]), atol=1e-6)
    groups, unweighted = garment_fit.weight_groups(run.result)
    assert unweighted == 0 and {"SKEL_Spine3", "SKEL_L_UpperArm", "SKEL_R_UpperArm"} <= set(groups)
    covered = np.concatenate([indices for entries in groups.values() for _, indices in entries])
    assert sorted(covered.tolist()) == list(range(len(upload.positions)))  # one bone per vertex in the fake
    sent_request, sent_mesh = api.fit.uploads[0]
    assert sent_request["operation"] == "fit" and sent_mesh[:4] == b"DCTM"
    assert garment_fit.warning_lines(run.result) == [("WARNING", strings.msg("fit.warning.marker-offset"))]


def test_a_busy_service_is_asked_again_and_cancel_gives_an_unstarted_fit_back(tmp_path, api, monkeypatch):
    monkeypatch.setattr(garment_fit.FitRun, "BUSY_WAIT", (0.05, 0.1))
    api.fit.busy = 1
    api.fit.queued_polls = 100
    ctrl = signed_in(tmp_path, api)
    ended = Ended()
    ctrl.fitting.on_ended = ended
    upload, mesh = garment_upload()
    run = ctrl.fitting.start("fit", request(mesh=mesh), upload, ("Scene", 7))
    until(ctrl, lambda: run.state == "waiting")
    assert run.status_text().key == "fit.stage.busy"
    until(ctrl, lambda: run.state == "queued" and run.job_id is not None)
    assert ctrl.fitting.cancel() and run.status_text().key == "fit.stage.cancelling"
    until(ctrl, lambda: bool(ended.runs))
    assert run.state == "cancelled" and run.refunded is True
    assert [line.key for _, line in run.lines] == ["fit.error.cancelled", "fit.refunded"]
    assert api.fit.cancels == [run.job_id] and api.fit.used == 0


@pytest.mark.parametrize("category, keys", [
    ("mock-invalid", ["fit.error.mesh-invalid", "fit.input.marker-far", "fit.refunded"]),
    ("mock-error", ["fit.error.server", "fit.refunded"]),
    ("mock-timeout", ["fit.error.timeout", "fit.counted"]),
    ("mock-not-on-body", None),
])
def test_a_fit_that_does_not_work_out_says_why(tmp_path, api, monkeypatch, category, keys):
    monkeypatch.setitem(garment_fit.REFERENCE_CATEGORIES, "jbib", category)  # the fake ends by category
    ctrl = signed_in(tmp_path, api)
    ended = Ended()
    ctrl.fitting.on_ended = ended
    upload, mesh = garment_upload()
    run = ctrl.fitting.start("fit", request(mesh=mesh), upload, ("Scene", 7))
    until(ctrl, lambda: bool(ended.runs))
    if keys is None:
        assert run.state == "done" and run.result.outcome == "notOnBody" and run.result.positions is None
    else:
        assert run.state == "failed" and [line.key for _, line in run.lines] == keys


def test_refusals_before_the_upload_are_worded_for_a_beginner(tmp_path, api):
    ctrl = signed_in(tmp_path, api)
    ended = Ended()
    ctrl.fitting.on_ended = ended
    upload, mesh = garment_upload()
    api.fit.used = 10  # the free plan's ten fits are used
    run = ctrl.fitting.start("fit", request(mesh=mesh), upload, ("Scene", 7))
    until(ctrl, lambda: bool(ended.runs))
    level, line = run.lines[0]
    assert level == "ERROR" and line.key == "fit.error.quota"
    assert re.fullmatch(r"You have used all of today's fits\. More are available in about \d+ (hours|minutes)\.",
                        strings.english(line))
    api.fit.used = 0
    stale = garment_fit.build_request("fit", "male", "jbib", "tshirt", "2026.01.01", mesh.joints,
                                      garment_fit.DEFAULT_OPTIONS)
    run = ctrl.fitting.start("fit", stale, upload, ("Scene", 7))
    until(ctrl, lambda: len(ended.runs) == 2)
    assert [line.key for _, line in run.lines] == ["fit.error.body-version"]


def test_opening_another_file_cancels_the_fit_on_gta_clothing_and_drops_its_result(tmp_path, api):
    api.fit.queued_polls = 100
    ctrl = signed_in(tmp_path, api)
    ended = Ended()
    ctrl.fitting.on_ended = ended
    upload, mesh = garment_upload()
    run = ctrl.fitting.start("fit", request(mesh=mesh), upload, ("Scene", 7))
    until(ctrl, lambda: run.job_id is not None)
    ctrl.fitting.forget()  # what the load_pre handler does
    assert not ctrl.fitting.busy
    until(ctrl, lambda: bool(api.fit.cancels))
    assert api.fit.cancels == [run.job_id] and ended.runs == []


def test_the_fits_left_today_come_from_me_and_follow_each_fit(tmp_path, api):
    ctrl = signed_in(tmp_path, api)
    ctrl.fitting.on_ended = Ended()
    ctrl.fitting.want_allowance()
    until(ctrl, lambda: ctrl.fitting.allowance is not None)
    assert ctrl.fitting.allowance == fit.FitAllowance(10, 0, 10)
    upload, mesh = garment_upload()
    run = ctrl.fitting.start("fit", request(mesh=mesh), upload, ("Scene", 7))
    until(ctrl, lambda: run.handled)
    assert ctrl.fitting.allowance.remaining_today == 9  # from the upload's answer, before /me is asked again
    asked = len([r for r in api.requests if r["path"] == "/link/api/me"])
    offline = signed_in(tmp_path / "offline", api, online=lambda: False)
    offline.fitting.want_allowance()
    for _ in range(20):
        offline.poll()
    assert offline.fitting.allowance is None  # without online access gta.clothing is not asked
    assert len([r for r in api.requests if r["path"] == "/link/api/me"]) == asked


def test_the_usual_ranges_of_game_clothing_fill_the_fit_check(tmp_path, api):
    ctrl = signed_in(tmp_path, api)
    assert ctrl.fitting.reference("male", "top", "1") is None  # asked for now
    until(ctrl, lambda: ctrl.fitting.reference("male", "top", "1") is not None)
    usual = garment_fit.usual_ranges(ctrl.fitting.reference("male", "top", "1"), "tshirt")
    assert usual["chest"] == pytest.approx((4.8, 19.1, 31.5))
    assert usual["upper_arms"] == pytest.approx((5.5, 17.9, 29.3))  # left and right, by their samples
    assert "waist" not in usual  # the reference does not measure it
    legs = fit.FitReference("1", "male", "shoes", {"footL": fit.FitRange(1, 5, 9, 10),
                                                   "footR": fit.FitRange(3, 7, 11, 30)})
    assert garment_fit.usual_ranges(legs, "shoes")["legs"] == pytest.approx((2.5, 6.5, 10.5))
    assert ctrl.fitting.reference("male", "capes", "1") is None
    until(ctrl, lambda: not ctrl.fitting.reference_pending("male", "capes", "1"))
    assert ctrl.fitting.reference("male", "capes", "1") is None  # not measured: no column, and not asked again soon


# ---- weights --------------------------------------------------------------------------------------------------------


def _result(bones, weights, names):
    count = len(bones)
    return fit.FitResult("A" * 22, "weights", "fitted", count, 1, bytes(count * 12),
                         np.asarray(bones, dtype=np.uint8).tobytes(), np.asarray(weights, dtype=np.uint8).tobytes(),
                         names, (), {})


def test_weights_become_vertex_groups_by_bone_name_and_never_the_root():
    names = {0: "SKEL_ROOT", 38: "SKEL_Spine3", 40: "SKEL_L_UpperArm", 99: "SKEL_Head"}
    result = _result([[38, 40, 0, 0], [0, 38, 0, 0], [0, 0, 0, 0], [40, 77, 0, 0]],
                     [[128, 127, 0, 0], [200, 55, 0, 0], [255, 0, 0, 0], [100, 155, 0, 0]], names)
    groups, unweighted = garment_fit.weight_groups(result)
    as_lists = {name: sorted((round(w, 6), idx.tolist()) for w, idx in entries) for name, entries in groups.items()}
    assert as_lists == {
        "SKEL_Spine3": [(round(128 / 255, 6), [0]), (1.0, [1])],  # the root's share goes to the vertex's other bones
        "SKEL_L_UpperArm": [(round(127 / 255, 6), [0]), (1.0, [3])],  # bone 77 has no name: left out
    }
    assert "SKEL_ROOT" not in groups and unweighted == 1  # vertex 2 leaned on the root only


# ---- texts ----------------------------------------------------------------------------------------------------------


def test_every_answer_of_the_service_has_a_text():
    for code in fit.FAILURE_CODES + fit.LOCAL_CODES:
        lines = garment_fit.failure_lines(code, retry_after=3600)
        assert lines[0][1].key in EN and lines[0][1].key != "fit.error.other", code
    for code in fit.INPUT_CODES:
        assert garment_fit.INPUT_TEXTS[code] in EN, code
    for code in fit.WARNING_CODES:
        assert garment_fit.WARNING_TEXTS[code] in EN, code
    for stage in fit.STAGES:
        assert garment_fit.STAGE_TEXTS[stage] in EN, stage
    keys = set(re.findall(r'"((?:fit|garment)\.[a-z0-9.-]+)"',
                          (REPO / "durty_cloth_tool_link" / "garment_fit.py").read_text("utf-8")))
    assert {key for key in keys if key.startswith("fit.") and not key.endswith(".")} <= set(EN)
    unknown = garment_fit.failure_lines("brand_new_code", [fit.FitIssue("brand_new_input", "mesh")])
    assert [line.key for _, line in unknown] == ["fit.error.other", "fit.input.other"]
    assert strings.english(garment_fit.wait_text(5400)) == "in about 2 hours"
    assert strings.english(garment_fit.wait_text(600)) == "in about 10 minutes"


def test_the_same_problem_is_said_once_and_a_lost_answer_after_the_upload_is_explained():
    issues = [fit.FitIssue("mesh_truncated", "mesh"), fit.FitIssue("mesh_header_invalid", "mesh"),
              fit.FitIssue("triangle_duplicate", "mesh")]
    lines = garment_fit.failure_lines("mesh_invalid", issues, refunded=True)
    assert [line.key for _, line in lines] == ["fit.error.mesh-invalid", "fit.input.add-on", "fit.input.duplicate",
                                               "fit.refunded"]
    assert garment_fit.failure_lines("network", uploaded=True)[0][1].key == "fit.error.network-uploaded"


# ---- the listing ----------------------------------------------------------------------------------------------------


def _worker_listing():
    """The Blender listing in the website's Worker (its hosts.js), when a checkout of the website is at hand:
    the one named by DCT_WEBSITE_CHECKOUT, else one beside this repository."""
    import os

    root = os.environ.get("DCT_WEBSITE_CHECKOUT")
    hosts = pathlib.Path(root) if root else REPO.parent / "durty-cloth-tool-website"
    hosts = hosts / "worker" / "link" / "hosts.js"
    if not hosts.is_file():
        return None
    text = hosts.read_text("utf-8")
    block = re.search(r"export const BLENDER_EXTENSION = Object\.freeze\(\{(.*?)\n\}\)", text, re.S)
    assert block, "the Worker's hosts.js has no BLENDER_EXTENSION listing"
    permissions = re.search(r"permissions: Object\.freeze\(\{(.*?)\}\)", block.group(1), re.S).group(1)
    found = {}
    for name, quote, value in re.findall(r"(\w+): (['\"])(.*?)\2,?\n", permissions):
        found[name] = value.replace("\\'", "'")
    return found


def test_the_network_permission_says_what_the_worker_lists_and_names_fitting():
    from tools import check_manifest

    expected = check_manifest.EXPECTED["permissions"]
    assert "fit clothing" in expected["network"]  # the add-on now sends garments to gta.clothing
    listing = _worker_listing()
    if listing is None:
        pytest.skip("no website checkout beside this repository (or DCT_WEBSITE_CHECKOUT)")
    assert listing == expected
