# SPDX-License-Identifier: GPL-3.0-or-later
"""The hosted freemode body: the ticket and download against a fake gta.clothing on 127.0.0.1, the cache in the
add-on's folder, and the answers the panel turns into messages (no Blender needed)."""

from __future__ import annotations

import pytest

from durty_cloth_tool_link import garment_body, garment_reference
from durty_cloth_tool_link.dct_link import auth
from tests.support import synthetic_pack
from tests.support.synthetic_pack import served
from tests.support.fake_link_api import FakeLinkApi, make_jwt

GLB = b"glTF" + (2).to_bytes(4, "little") + (64).to_bytes(4, "little") + bytes(52)


def glb_with(header: bytes) -> bytes:
    """A GLB whose JSON chunk is ``header`` (padded with spaces)."""
    header += b" " * (-len(header) % 4)
    return (b"glTF" + (2).to_bytes(4, "little") + (20 + len(header)).to_bytes(4, "little")
            + len(header).to_bytes(4, "little") + b"JSON" + header)


COMPRESSED = glb_with(b'{"asset":{"version":"2.0"},"extensionsRequired":["EXT_meshopt_compression"]}')
HEADER = auth.client_header(auth.ClientInfo("blender", "0.1.0-experimental.1", "5.2.1", "experimental",
                                            "00000000-0000-4000-8000-000000000000"))


@pytest.fixture
def api():
    with FakeLinkApi() as fake:
        fake.body_files = {"freemode_male.glb": GLB, "freemode_female.glb": GLB + b"female"}
        yield fake


def download(api, tmp_path, *, gender="male", token="valid", blender=(5, 2, 1), online=True):
    if token == "valid":
        token = make_jwt()
        api.access_tokens.append(token)
    return garment_body.BodyDownload(gender=gender, channel="experimental", cache_root=tmp_path,
                                     client_header=HEADER, access_token=lambda: token, blender_version=blender,
                                     origin=api.base_url, online=online).run()


def test_the_body_is_downloaded_with_a_ticket_and_kept(api, tmp_path):
    first = download(api, tmp_path)
    assert first.error is None and first.result is not None
    assert first.result.path == tmp_path / "body" / "2026.10.03.1" / "freemode_male.glb"
    assert first.result.path.read_bytes() == GLB and not first.result.cached
    paths = api.paths()
    assert paths == ["GET /link/manifest/experimental.json", "POST /link/panel/ticket",
                     "GET /link/assets/body/2026.10.03.1/freemode_male.glb",
                     "GET /link/assets/body/2026.10.03.1/freemode_joints.json",  # optional; this version has none
                     "GET /link/assets/body/2026.10.03.1/reference/reference.json"]  # optional too
    assert first.result.joints is None
    ticket_request = next(r for r in api.requests if r["path"] == "/link/panel/ticket")
    assert ticket_request["body"] == {"channel": "experimental", "version": "1.2.0"}
    assert ticket_request["headers"]["authorization"].startswith("Bearer ")
    body_request = api.requests[2]
    assert body_request["headers"]["authorization"] == "Ticket " + api.tickets[0]

    again = download(api, tmp_path)
    assert again.result is not None and again.result.cached and again.result.path == first.result.path
    assert api.paths()[-1] == "GET /link/manifest/experimental.json"  # the version is kept: no second ticket


def test_a_new_body_version_is_downloaded_again(api, tmp_path):
    download(api, tmp_path)
    api.manifest["body"]["version"] = "2026.11.01.1"
    newer = download(api, tmp_path)
    assert newer.result.version == "2026.11.01.1" and not newer.result.cached
    assert (tmp_path / "body" / "2026.10.03.1" / "freemode_male.glb").is_file()


def test_older_blender_versions_get_the_plain_body_or_a_message(api, tmp_path):
    api.body_files["freemode_female_plain.glb"] = GLB + b"plain"
    result = download(api, tmp_path, gender="female", blender=(4, 5, 3)).result
    assert result.path.name == "freemode_female_plain.glb"
    assert garment_body.body_files("male", (5, 2, 0)) == ["freemode_male.glb"]
    assert garment_body.body_files("male", (4, 2, 0)) == ["freemode_male_plain.glb"]
    # Without a plain copy an older Blender is told so, instead of being handed a body its importer fails on.
    older = download(api, tmp_path / "other", gender="male", blender=(4, 2, 0))
    assert older.error == "compressed" and older.result is None
    api.body_files["freemode_male_plain.glb"] = COMPRESSED  # a mislabelled file is refused too
    assert download(api, tmp_path / "third", gender="male", blender=(4, 2, 0)).error == "compressed"
    path = tmp_path / "compressed.glb"
    path.write_bytes(COMPRESSED)
    assert garment_body.needs_meshopt(path) and garment_body.required_extensions(GLB) == []


def test_the_joints_of_a_body_version_are_kept_beside_it(api, tmp_path):
    api.body_files["freemode_joints.json"] = b'{"schema": 1, "space": "ped", "units": "m", "male": {}}'
    first = download(api, tmp_path)
    assert first.result.joints == tmp_path / "body" / "2026.10.03.1" / "freemode_joints.json"
    assert first.result.joints.is_file()
    again = download(api, tmp_path)
    assert again.result.cached and again.result.joints == first.result.joints
    api.body_files["freemode_joints.json"] = b"[not joints"
    assert download(api, tmp_path / "other").result.joints is None  # unreadable joints never stop the body


def test_without_online_access_only_a_kept_body_is_used(api, tmp_path):
    assert download(api, tmp_path, online=False).error == "offline"
    assert api.paths() == []
    download(api, tmp_path)
    kept = download(api, tmp_path, online=False)
    assert kept.result is not None and kept.result.cached


def test_a_kept_body_is_used_when_gta_clothing_cannot_be_reached(api, tmp_path):
    download(api, tmp_path)
    unreachable = garment_body.BodyDownload(gender="male", channel="experimental", cache_root=tmp_path,
                                            client_header=HEADER, access_token=lambda: None,
                                            blender_version=(5, 2, 1), origin="http://127.0.0.1:9", timeout=2.0)
    result = unreachable.run().result
    assert result is not None and result.cached
    fresh = garment_body.BodyDownload(gender="male", channel="experimental", cache_root=tmp_path / "none",
                                      client_header=HEADER, access_token=lambda: None, blender_version=(5, 2, 1),
                                      origin="http://127.0.0.1:9", timeout=2.0)
    assert fresh.run().error == "network"


@pytest.mark.parametrize("change, code", [
    (lambda api: setattr(api, "manifest", None), "no-body"),
    (lambda api: api.manifest.pop("body"), "no-body"),
    (lambda api: setattr(api, "body_entitled", False), "not-entitled"),
    (lambda api: api.body_files.clear(), "no-body"),
    (lambda api: api.body_files.update({"freemode_male.glb": b"<html>not a body</html>"}), "invalid"),
])
def test_refusals_become_messages(api, tmp_path, change, code):
    change(api)
    assert download(api, tmp_path).error == code
    assert not (tmp_path / "body").exists() or not any((tmp_path / "body").rglob("*.glb"))


def test_without_a_sign_in_no_ticket_is_asked_for(api, tmp_path):
    assert download(api, tmp_path, token=None).error == "signed-out"
    assert "POST /link/panel/ticket" not in api.paths()
    assert download(api, tmp_path, token="expired").error == "signed-out"  # the fake answers 401


def test_a_refused_sign_in_is_renewed_once_and_a_failed_renewal_is_no_crash(api, tmp_path):
    good = make_jwt()
    api.access_tokens.append(good)
    tokens = iter(["stale", good])
    renewed = []
    job = garment_body.BodyDownload(gender="male", channel="experimental", cache_root=tmp_path, client_header=HEADER,
                                    access_token=lambda: next(tokens), blender_version=(5, 2, 1),
                                    origin=api.base_url, invalidate_token=lambda: renewed.append(True)).run()
    assert job.result is not None and renewed == [True]

    def broken():
        raise auth.AuthError("network", "gta.clothing could not be reached", retryable=True)

    failed = garment_body.BodyDownload(gender="female", channel="experimental", cache_root=tmp_path / "x",
                                       client_header=HEADER, access_token=broken, blender_version=(5, 2, 1),
                                       origin=api.base_url).run()
    assert failed.error == "network"


def test_kept_versions_sort_by_their_numbers(tmp_path):
    for version in ("2026.9.1", "2026.10.03-rc1", "2026.10.03.1"):
        folder = tmp_path / "body" / version
        folder.mkdir(parents=True)
        (folder / "freemode_male.glb").write_bytes(GLB)
    assert garment_body.cached_body(tmp_path, "male").version.startswith("2026.10.03")  # 10 sorts after 9


def test_signed_out_a_body_kept_before_is_used(api, tmp_path):
    download(api, tmp_path)
    api.manifest["body"]["version"] = "2026.11.01.1"  # a newer body needs a ticket, so the kept one is used
    kept = download(api, tmp_path, token=None).result
    assert kept is not None and kept.cached and kept.version == "2026.10.03.1"


def test_only_the_link_origin_or_a_loopback_test_server():
    assert garment_body.check_origin("https://link.gta.clothing/") == "https://link.gta.clothing"
    assert garment_body.check_origin("http://127.0.0.1:8080") == "http://127.0.0.1:8080"
    for url in ("https://gta.clothing", "https://link.gta.clothing.example.com", "http://evil.example",
                "http://user@127.0.0.1:80", "https://127.0.0.1/path"):
        with pytest.raises(ValueError):
            garment_body.check_origin(url)
    assert garment_body.valid_version("2026.10.03.1") and garment_body.valid_version("2026.10.03-rc1")
    for bad in ("../etc", ".", "..", "-1", "1.", "CON", "nul.1", "a/b", "x" * 33, "", None):
        assert not garment_body.valid_version(bad), bad


def test_the_download_runs_on_a_thread_and_can_be_cancelled(api, tmp_path):
    token = make_jwt()
    api.access_tokens.append(token)
    job = garment_body.BodyDownload(gender="male", channel="release", cache_root=tmp_path, client_header=HEADER,
                                    access_token=lambda: token, blender_version=(5, 2, 1), origin=api.base_url)
    job.cancel()
    job.start()
    job._thread.join(10)
    assert job.poll() and job.error == "cancelled"


# ---- the Reference Data Pack -------------------------------------------------------------------------

def reference_folder(tmp_path, version="2026.10.03.1"):
    return tmp_path / "body" / version / "reference"


def test_the_reference_data_pack_comes_with_the_body_in_its_own_folder(api, tmp_path):
    pack = synthetic_pack.files()
    api.body_files.update(synthetic_pack.body_files())
    first = download(api, tmp_path)
    folder = reference_folder(tmp_path)
    assert first.error is None and first.result.reference == folder
    assert {p.name for p in folder.iterdir() if not p.name.startswith(".")} == set(pack)
    assert (folder / "NOTICE.txt").read_bytes() == synthetic_pack.NOTICE
    assert all((folder / name).read_bytes() == data for name, data in pack.items())
    assert sorted(p.name for p in folder.parent.iterdir()) == ["freemode_male.glb", "reference"]  # nothing half-written
    assert "GET /link/assets/body/2026.10.03.1/reference/reference.json" in api.paths()

    tickets = len(api.tickets)
    again = download(api, tmp_path)
    assert again.result.cached and again.result.reference == folder and len(api.tickets) == tickets


def test_a_body_version_without_the_pack_downloads_the_body_only(api, tmp_path):
    first = download(api, tmp_path)
    assert first.result is not None and first.result.reference is None
    assert not reference_folder(tmp_path).exists()
    tickets = len(api.tickets)
    again = download(api, tmp_path)
    assert again.result.cached and again.result.reference is None
    assert len(api.tickets) == tickets  # the version's file list never changes: it is not asked again


def test_a_kept_body_from_before_the_pack_asks_for_it_once(api, tmp_path):
    download(api, tmp_path)
    (tmp_path / "body" / "2026.10.03.1" / garment_body.NO_REFERENCE).unlink()  # kept by an add-on without the pack
    api.body_files.update(synthetic_pack.body_files())
    kept = download(api, tmp_path)
    assert kept.result.cached and kept.result.reference == reference_folder(tmp_path)


def test_a_withdrawn_pack_is_deleted(api, tmp_path):
    api.body_files.update(synthetic_pack.body_files())
    download(api, tmp_path)
    assert reference_folder(tmp_path).is_dir()
    api.manifest["body"]["version"] = "2026.11.01.1"  # the next body version no longer lists the pack
    api.body_files = {name: data for name, data in api.body_files.items() if not name.startswith(served(""))}
    newer = download(api, tmp_path)
    assert newer.result.version == "2026.11.01.1" and newer.result.reference is None
    assert not reference_folder(tmp_path).exists()
    assert (tmp_path / "body" / "2026.10.03.1" / "freemode_male.glb").is_file()  # the old body itself stays


def test_a_withdrawal_is_honoured_even_signed_out(api, tmp_path):
    api.body_files.update(synthetic_pack.body_files())
    download(api, tmp_path)
    api.manifest["body"]["version"] = "2026.11.01.1"
    kept = download(api, tmp_path, token=None).result
    assert kept.version == "2026.10.03.1" and kept.reference is None
    assert not reference_folder(tmp_path).exists()
    api.manifest.pop("body")  # no body published at all: nothing names the pack either
    download(api, tmp_path / "other")
    assert not any((tmp_path / "other").rglob("reference"))


def test_offline_the_kept_pack_is_used_while_it_is_whole(api, tmp_path):
    api.body_files.update(synthetic_pack.body_files())
    download(api, tmp_path)
    kept = download(api, tmp_path, online=False).result
    assert kept.cached and kept.reference == reference_folder(tmp_path)
    unreachable = garment_body.BodyDownload(gender="male", channel="experimental", cache_root=tmp_path,
                                            client_header=HEADER, access_token=lambda: None,
                                            blender_version=(5, 2, 1), origin="http://127.0.0.1:9", timeout=2.0)
    assert unreachable.run().result.reference == reference_folder(tmp_path)
    poses = reference_folder(tmp_path) / "poses_male.json"
    poses.write_bytes(poses.read_bytes().replace(b"climb", b"crawl"))  # changed after the download
    assert download(api, tmp_path, online=False).result.reference is None


@pytest.mark.parametrize("change", [
    lambda files: files.update({served("cuts_male.glb"): b"glTF" + bytes(garment_reference.MAX_GLB_BYTES)}),
    lambda files: files.update({served("NOTICE.txt"): b"x" * (garment_reference.MAX_TEXT_BYTES + 1)}),
    lambda files: files.update({served("reference.json"): b'{"format": 2}'}),
    lambda files: files.update({served("reference.json"): files[served("reference.json")].replace(
        b'"skeleton.json"', b'"../skeleton.json"')}),
    lambda files: files.update({served("poses_female.json"): b"[not json"}),
    lambda files: files.pop(served("skeleton.json")),
])
def test_a_pack_that_breaks_the_limits_is_never_kept(api, tmp_path, change):
    pack = synthetic_pack.body_files()
    change(pack)
    api.body_files.update(pack)
    result = download(api, tmp_path).result
    assert result is not None and not result.cached and result.reference is None  # the body still comes
    assert [p.name for p in (tmp_path / "body" / "2026.10.03.1").iterdir()] == ["freemode_male.glb"]


def test_copy_diagnostics_names_the_packs_presence_and_version(api, tmp_path):
    assert garment_body.pack_summary(tmp_path) == "none"
    api.body_files.update(synthetic_pack.body_files())
    download(api, tmp_path)
    assert garment_body.pack_summary(tmp_path) == "present, body version 2026.10.03.1, format 1"
    (reference_folder(tmp_path) / "NOTICE.txt").write_bytes(b"changed")
    assert garment_body.pack_summary(tmp_path) == "none (a kept pack no longer matches its record)"
