# SPDX-License-Identifier: GPL-3.0-or-later
"""Settings, public addresses and the user-facing text (no Blender needed)."""

from __future__ import annotations

import pathlib
import re

from durty_cloth_tool_link import settings, strings
from durty_cloth_tool_link.dct_link import protocol

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
PACKAGE = REPO_ROOT / "durty_cloth_tool_link"
VENDORED = PACKAGE / "dct_link"
EM_DASH = chr(0x2014)
#: The hosts the add-on names: gta.clothing with its documentation and its link pages, the Pleb Masters Community
#: Discord server with its invitation, and the copyright holder's site. It connects only to Durty Cloth Tool on
#: this computer and to gta.clothing; the others are pages it opens or names.
ADD_ON_HOSTS = frozenset({
    "gta.clothing", "docs.gta.clothing", "link.gta.clothing", "discord.com", "discord.plebmasters.de",
    "schmid-software.de",
})
#: Hosts that only the documentation, the workflows and the tests name: this repository and its badges, Sollumz's
#: documentation, and Blender's downloads and extensions.
OTHER_HOSTS = frozenset({
    "github.com", "img.shields.io", "docs.sollumz.org", "download.blender.org", "extensions.blender.org",
})
#: Durty Cloth Tool on this computer, and the fakes the tests start. Always by address, never by name.
LOOPBACK = frozenset({"127.0.0.1"})
#: Names reserved for examples; the tests use them for addresses that must be refused.
EXAMPLE_HOST = re.compile(r"(^|\.)example(\.(com|net|org))?$")
_ADDRESS = re.compile(r"\b[a-z][a-z0-9+.-]*://([^\s/\"'`<>()\[\]{},|\\?#]*)", re.IGNORECASE)
#: A name under the domain of a known host counts as a host wherever it stands, with or without a scheme.
_KNOWN_DOMAIN = re.compile(
    r"(?<![\w.-])((?:[a-z0-9-]+\.)*(?:"
    + "|".join(sorted({re.escape(".".join(host.split(".")[-2:])) for host in ADD_ON_HOSTS | OTHER_HOSTS}))
    + r"))(?![\w-])", re.IGNORECASE)
#: Folders the build and the release workflow create; a path into them need not exist.
GENERATED_FOLDERS = frozenset({"dist", "release", "release-notes", "__pycache__"})
#: Documents the release workflow writes.
GENERATED_DOCUMENTS = frozenset({"notes.md"})
#: Words joined by slashes that are not paths (and element paths in the XML Sollumz reads and writes).
NOT_PATHS = frozenset({"HTTP/1", "HTTP/1.1", "I/O", "application/json", "hello/challenge/auth", "GLB/glTF",
                       "folder/model_file", "Skeleton/Bones", "Skeleton/Bones/Item"})
#: Paths that exist somewhere else on purpose: the sculpt brush in Blender's bundled assets, and the files the tests
#: write into temporary folders or refuse because they would leave their folder.
OUTSIDE_PATHS = frozenset({
    "brushes/essentials_brushes-mesh_sculpt.blend/Brush/Grab",
    "a/b", "a/b.dds", "../etc", "../escape.dds", "jbib_003_u/jbib_diff_003_a_uni.dds",
    "jbib_003_u/jbib_normal_003.dds", "smoke_open/smoke_diff_000_a_uni.dds",
})
#: What is not a path into a repository: an address, an absolute path on someone's disk, a Git ref, an action a
#: workflow uses, and a media type.
_NOT_REPOSITORY_PATHS = (re.compile(r"\b[a-z][a-z0-9+.-]*://[^\s\"'`<>]*", re.IGNORECASE),
                         re.compile(r"\b[A-Za-z]:[\\/][^\"'`\n]*"), re.compile(r"\brefs/[\w./-]+"),
                         re.compile(r"\buses:\s*\S+"),
                         re.compile(r"\b(?:application|audio|font|image|model|text|video)/[a-z0-9.+-]+\b"))
_PATH = re.compile(r"(?<![\w/:.\\%$@~-])[A-Za-z_.][\w.-]*(?:(?:/[\w.-]+)+/?|/(?=[\s\"'`),;]|$))", re.MULTILINE)
#: A Markdown document or a Windows script (PowerShell, batch), named with or without its folder.
_DOCUMENT = re.compile(r"[\w.-]+\.(?:md|ps[dm]?\d|bat)\b")


def test_repository_addresses_per_channel():
    assert settings.repository_url("release") == "https://gta.clothing/link/blender/release/index.json"
    assert settings.repository_url("experimental") == "https://gta.clothing/link/blender/experimental/index.json"
    assert settings.repository_url("development") == settings.repository_url("release")  # never offered
    for channel in settings.CHANNEL_IDS:
        assert settings.repository_channel(settings.repository_url(channel)) == channel
    assert settings.repository_channel("https://extensions.blender.org/api/v1/extensions/") is None
    assert settings.repository_channel("https://gta.clothing/link/blender/development/index.json") is None
    assert settings.repository_channel(None) is None


def test_only_gta_clothing_links_are_opened():
    assert settings.is_gta_clothing_url("https://gta.clothing/account/link/?code=BDWPHQPK")
    assert not settings.is_gta_clothing_url("http://gta.clothing/account/link/")
    assert not settings.is_gta_clothing_url("https://gta.clothing.example.com/")
    assert not settings.is_gta_clothing_url("https://evil.example/?https://gta.clothing/")
    assert not settings.is_gta_clothing_url(None)
    # The rules dct_link applies to update links: printable ASCII, no spaces, backslash or @, and the exact prefix.
    for url in ("https://gta.clothing\\@evil.example/", "https://gta.clothing/@evil.example",
                "https://gta.clothing/a b", "https://gta.clothing/a\tb", "https://gta.clothing/\x00",
                "https://gta.clothing/é", "https://gta.clothing", "https://gta.clothing:443/",
                "https://link.gta.clothing/", "https://gta.clothing/" + "a" * 2048):
        assert not settings.is_gta_clothing_url(url), url


def test_sign_in_codes_show_like_on_gta_clothing():
    assert settings.display_user_code("BDWPHQPK") == "BDWP-HQPK"
    assert settings.display_user_code("bdwp-hqpk") == "BDWP-HQPK"


def test_stream_size_limits():
    assert settings.check_stream_size(4096, 4096) is None
    assert settings.check_stream_size(1, 1) is None
    assert "4096" in strings.english(settings.check_stream_size(4097, 16))
    assert settings.check_stream_size(0, 16) is not None


def test_auto_push_delay_is_clamped():
    assert settings.clamp_auto_push_delay(0) == settings.AUTO_PUSH_DELAY_MIN
    assert settings.clamp_auto_push_delay(100) == settings.AUTO_PUSH_DELAY_MAX
    assert settings.clamp_auto_push_delay(2.5) == 2.5


#: dct_link's local error codes (LinkError in dct_link/session.py).
LOCAL_CODES = ("disconnected", "timeout", "superseded", "cancelled", "closed", "assertion-invalid",
               "untrusted-endpoint", "signed-out", "pixel-source-failed", "callback-failed", "internal-error")


def test_every_protocol_and_session_error_code_has_text():
    missing = [code for code in (*protocol.ERROR_CODES, *LOCAL_CODES) if f"error.{code}" not in strings.EN]
    assert missing == []


def test_every_close_reason_and_plan_state_has_text():
    reasons = set(protocol.LIVE_CLOSE_REASONS) | set(protocol.MODEL_CLOSE_REASONS) | {"disconnected"}
    assert {f"close.{reason}" for reason in reasons} <= set(strings.EN)
    assert {f"feature.{state}" for state in protocol.FEATURE_STATES if state != "entitled"} <= set(strings.EN)


def test_unknown_codes_still_get_a_sentence():
    assert strings.english(settings.describe_error("something-new")) == "Something went wrong (something-new)."
    assert strings.english(settings.describe_error(None)) == "Something went wrong."
    assert settings.describe_feature("entitled") is None
    assert settings.describe_feature(None) is None
    assert strings.english(settings.describe_feature("needsUltimate")) == "This is included in Durty Cloth Tool Ultimate."


def test_targets_match_the_protocol():
    assert tuple(target for target, _, _ in settings.TARGETS) == protocol.LIVE_TARGETS


def repository_files():
    """The repository's own files: nothing from hidden tool folders (other than the workflows), build output or
    caches."""
    for path in sorted(REPO_ROOT.rglob("*")):
        folders = path.relative_to(REPO_ROOT).parts[:-1]
        if path.is_file() and not any(part in {"dist", "__pycache__"} or (part.startswith(".") and part != ".github")
                                      for part in folders):
            yield path


def text_files(include_vendored: bool = False):
    for path in repository_files():
        if path.name == "LICENSE" or (VENDORED in path.parents and not include_vendored):
            continue
        if (path.suffix in {".py", ".md", ".toml", ".yml", ".txt", ".json"} or path.name.startswith(".")
                or path.name == "NOTICE"):
            yield path


def relative(path: pathlib.Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def named_hosts(text: str) -> set[str]:
    """Every host ``text`` names: the host of each address, and each name under the domain of a known host."""
    hosts = {authority.rpartition("@")[2].partition(":")[0].rstrip(".").lower() for authority in _ADDRESS.findall(text)}
    hosts.update(name.lower() for name in _KNOWN_DOMAIN.findall(text))
    return hosts - {""}


def named_paths(text: str) -> set[str]:
    """Every relative path ``text`` names: names joined by slashes, or a folder name that ends with one."""
    for pattern in _NOT_REPOSITORY_PATHS:
        text = pattern.sub(" ", text)
    return {name.rstrip("./") for name in _PATH.findall(text)} - NOT_PATHS - OUTSIDE_PATHS - {""}


def in_repository(name: str) -> bool:
    """Whether a relative path leads to something in this repository or the add-on folder, or to build output."""
    parts = name.split("/")
    if ".." in parts:
        return False
    return parts[0] in GENERATED_FOLDERS or any((base / name).exists() for base in (REPO_ROOT, PACKAGE))


def test_no_em_dashes_in_the_repository():
    offenders = [relative(p) for p in text_files() if EM_DASH in p.read_text("utf-8")]
    assert offenders == []


def test_the_add_on_names_only_its_public_hosts():
    """What ships to users (the add-on with its vendored dct_link) names Durty Cloth Tool's public hosts and
    nothing else, so an address that is not meant for users cannot slip into a release."""
    allowed = ADD_ON_HOSTS | LOOPBACK
    offenders = [f"{relative(p)}: {host}" for p in text_files(include_vendored=True) if PACKAGE in p.parents
                 for host in sorted(named_hosts(p.read_text("utf-8")) - allowed)]
    assert offenders == []


def test_the_rest_of_the_repository_names_only_known_hosts():
    allowed = ADD_ON_HOSTS | OTHER_HOSTS | LOOPBACK
    offenders = [f"{relative(p)}: {host}" for p in text_files() if PACKAGE not in p.parents
                 for host in sorted(named_hosts(p.read_text("utf-8")) - allowed) if not EXAMPLE_HOST.search(host)]
    assert offenders == []


def test_the_repository_points_at_nothing_outside_itself():
    """Every relative path the texts name exists here (or is build output), and so does every document and
    Windows script they name: the add-on and its tools do not lean on the files of another repository."""
    documents = {p.name for p in repository_files()} | GENERATED_DOCUMENTS
    offenders = []
    for path in text_files(include_vendored=True):
        if path.name == ".gitignore":  # an ignore file lists what the repository does not hold
            continue
        text = path.read_text("utf-8")
        missing = {name for name in named_paths(text) if not in_repository(name)}
        missing |= set(_DOCUMENT.findall(text)) - documents
        offenders += [f"{relative(path)}: {name}" for name in sorted(missing)]
    assert offenders == []


def test_the_checks_notice_foreign_names():
    """The checks above are only worth something if a foreign name fails them. The samples are put together from
    pieces, so that this file passes the checks itself."""
    slash, own = "/", "gta.clothing"
    stranger = "made-up." + own
    assert named_hosts("see https:" + slash * 2 + stranger + slash + " or " + stranger.upper()) == {stranger}
    assert named_hosts("ws:" + slash * 2 + "user@127.0.0.1:47820" + slash) == {"127.0.0.1"}
    path = slash.join(["elsewhere", "module.py"])
    assert named_paths("copied from " + path + ", see elsewhere" + slash) == {path, "elsewhere"}
    assert not in_repository(path) and not in_repository(".." + slash + "tests")
    assert in_repository("tests") and in_repository(slash.join(["dct_link", "session.py"]))
    assert in_repository(slash.join(["dist", "any.zip"]))
    script, note = "build-it." + "bat", "design-notes." + "md"
    assert _DOCUMENT.findall("run " + script + " as described in " + note) == [script, note]


def test_only_the_modules_the_add_on_uses_are_shipped():
    shipped = {p.name for p in VENDORED.iterdir() if p.is_file()}
    assert shipped == {"__init__.py", "auth.py", "protocol.py", "session.py", "tokens.py", "ws.py", "LICENSE",
                       "VENDORED.md"}
