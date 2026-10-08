# Developing Durty Cloth Tool Link

This is the technical reference for the Blender add-on: how the code is organised, how it talks to Durty Cloth Tool
and gta.clothing, how it is tested on which Blender versions, and how a release is built. The user-facing guide is
the [README](/README.md) and the public documentation; the contribution workflow (setup, checks, texts, pull
requests) is in [CONTRIBUTING.md](/CONTRIBUTING.md).

This repository is public. Everything here describes the add-on's own open-source code. Durty Cloth Tool's internals,
gta.clothing's services and the release infrastructure outside this repository are not documented here.

## Repository layout

```
durty_cloth_tool_link/          the extension: blender_manifest.toml, the modules, translations, icons, LICENSE, NOTICE
durty_cloth_tool_link/dct_link/ the Creator Link client, vendored byte for byte (read-only here)
tests/                          pytest tests (no Blender needed) and their fakes in tests/support
tests/blender/                  the smoke test that runs inside Blender, with a Sollumz stand-in
tools/                          manifest, vendoring and release checks, Blender smoke and screenshot runners, avatar
                                measurement
docs/                           this document and the README images (docs/images)
.github/                        CI and release workflows, issue forms and the pull request template
```

Only `durty_cloth_tool_link/` goes into the extension archive. `pyproject.toml` and `requirements-dev.txt` exist for
the tests only.

## Architecture

The add-on is a Blender extension (`blender_manifest.toml`, schema 1.0.0) with one rule above all: logic lives in
modules that do not import Blender, so plain Python and pytest can test it, and the code that touches `bpy` stays thin.
`__init__.py` itself imports nothing from Blender.

### Modules without Blender

| Module | What it holds |
|---|---|
| `settings.py` | The version, public addresses, the extension repository per channel, limits, and the mapping from codes to texts |
| `strings.py`, `ped_strings.py` | Every English text (`EN`), the `Msg` type (a key plus fields) and the plural forms |
| `translations/` | The eight other languages, three modules each (`<locale>`, `garment_<locale>`, `ped_<locale>`), registered in the add-on's own translation context |
| `link.py` | `LinkController`: connecting, sign-in, Live Preview, Texture Checks, model pushes, what Durty Cloth Tool opens in Blender, the linked cloth's picture, temporary folders |
| `pixels.py` | Reading Blender's float pixels into RGBA8 rows, change detection and dirty rectangles, in small steps per timer tick |
| `bundle.py` | Collecting a Sollumz export (one `*.ydd.xml` and its `*.dds` files) into a model push |
| `garment.py` | Garment Fitting maths: types and slots, markers and their plausibility, Align to Body, regions, the fit check, problem colours, seam welding, pose presets, the next-step hint |
| `garment_avatars.py` | Joints of known Marvelous Designer and CLO stock avatars, as markers |
| `garment_body.py` | Downloading the hosted freemode body for the signed-in account and keeping each version |
| `garment_fit.py` | Fit on gta.clothing and Transfer Weights: preparing the upload, one run with polling and Cancel, the fits left today |
| `garment_add.py` | Add to Project rules: the skeleton template's bones, the checks before anything is sent, the variation pictures, Durty Cloth Tool's answer |
| `ped.py` | Custom Ped maths: markers (click guide, Auto Markers, from an old rig), character checks, the rig result as an armature plan, test poses, local checks |
| `ped_link.py` | Custom Ped's part of the link: the template list, the rig with its progress, sending the rigged character |

### Blender side

| Module | What it holds |
|---|---|
| `addon.py` | Registration: translations, the logo icon, classes, the timer that drives the link, file-load, undo and depsgraph handlers |
| `state.py` | The single link controller and helpers the panels, operators and timers share |
| `host.py` | Blender I/O: the add-on's user folder, reading images, detecting paint strokes, Sollumz export and import, redraws |
| `ui.py` | The **DCT** tab: the Durty Cloth Tool, Get Connected, Linked Cloth, Live Preview, Model and Settings panels and their operators |
| `ui_garment.py`, `garment_host.py`, `garment_dct.py` | Garment Fitting's panel and operators, its mesh work in Blender, and the Sollumz setup and export for Add to Project |
| `ui_ped.py`, `ped_host.py` | Custom Ped's panel and operators, and its work on the character in Blender (markers, ray casts, applying a rig, GLB export) |
| `preferences.py` | The add-on preferences, mirroring the sidebar's Settings |

**Work On** in the Durty Cloth Tool panel switches the tab between three views (Linked Cloth, Garment Fitting, Custom
Ped) so unrelated tools never show together. Garment Fitting and Custom Ped share one pattern: a next-step line, five
numbered stages that open when they hold the next step and fold with a tick when done, and closed **Options**
sections for rarely changed settings.

### Threads and timers

Blender's API is single-threaded. `LinkController.poll` runs on the main thread from a `bpy.app.timers` timer and
drives the dct_link session with bounded work per call; session callbacks run inside that call. Network calls to
gta.clothing (sign-in, renewal, assertions, the body download, fitting) run on worker threads that never touch
Blender, and the timer only checks whether they finished. Never block Blender's interface: new network or disk work
goes into a background task that a timer checks.

### Texts

Logic never stores or compares displayed text. It passes keys and `Msg` values, and the panels render them in
Blender's interface language when they draw. Logs, the system console and Copy Diagnostics stay English. The rules for
keys, plural forms and translations are in [CONTRIBUTING.md](/CONTRIBUTING.md#-texts-and-translations).

## How the add-on talks to Durty Cloth Tool

The connection is the vendored `dct_link` package, the Creator Link client shared by Durty Cloth Tool's Python host
plugins. Its modules describe themselves in their docstrings; in short:

- **Finding Durty Cloth Tool.** `session.py` reads the endpoint file Durty Cloth Tool writes for the current Windows
  user, or probes its port, and connects only to `127.0.0.1`. Nothing of the connection leaves the computer.
- **The connection.** `ws.py` is a small WebSocket client for that loopback connection (no extensions, size limits
  that match the protocol). It can be polled, which is how Blender drives it.
- **The protocol.** `protocol.py` is the Creator Link protocol 2 wire format: message definitions, validation and
  frame codecs. Everything a peer sends is treated as untrusted and validated before use.
- **Signing in.** `auth.py` signs in to gta.clothing with a device code that Durty Cloth Tool can approve in its own
  window, or the browser can. For each connection it trades the access token for a short-lived sign-in assertion
  bound to that connection; only the assertion goes to Durty Cloth Tool. `tokens.py` keeps the tokens in the add-on's
  user folder, protected with Windows DPAPI for the current user.
- **What travels.** Live Preview streams RGBA8 frames with dirty rectangles (`pixels.py`); a model push sends the
  Sollumz export as `ydd-xml` (`bundle.py`); Add to Project sends the export, the colour variations and the cloth's
  settings; Custom Ped asks Durty Cloth Tool for the template list and the rig, then sends the rigged character as a
  GLB. Durty Cloth Tool answers with what the user asked for: cloths to open in Blender, the freemode skeleton built
  from the user's own game files, rig results.
- **Fitting.** `fit.py` is the client of gta.clothing's garment fitting routes, used by `garment_fit.py`. It uploads
  only the garment's triangles in ped space, its markers and the chosen options, after checking them against the
  service's size rules.

`durty_cloth_tool_link/dct_link/VENDORED.md` records the dct_link version, the Creator Link protocol version and the
SHA-256 of every file. The package is developed in the Durty Cloth Tool repository together with Creator Link's
shared protocol package, and copied here with `tools/sync_dct_link.py`. Never edit the vendored files by hand:

```powershell
python tools/sync_dct_link.py <path to the Durty Cloth Tool checkout>   # replace the copy and rewrite VENDORED.md
python tools/sync_dct_link.py --check [<checkout>]                     # verify the hashes, and the checkout when given
```

`--check` also compares with a Durty Cloth Tool checkout that sits beside this repository. When that checkout is
older than the vendored copy, it reports a difference even though the copy is right; compare with the upstream branch
the copy was synced from instead.

## Network and data

The add-on connects to Durty Cloth Tool on `127.0.0.1` and to gta.clothing, and opens only gta.clothing, its
documentation and the Pleb Masters Community Discord in the browser. `tests/test_settings.py` lists every host the
repository may name (`ADD_ON_HOSTS` for what ships, `OTHER_HOSTS` for documentation, workflows and tests) and fails on
any other. A new address needs an issue and an owner decision first.

What reaches gta.clothing: the sign-in (with the computer's name unless the user turns that off), a confirmation for
each connection, the sign-out, the hosted body download (once per body version), Blender's update checks of the
extension repository, and, once the user agreed, a garment for Fit on gta.clothing or Transfer Weights with the
questions for the fits left today and the usual ranges of game clothing. The add-on collects no usage data.

Files the add-on keeps:

- the add-on's user folder (`bpy.utils.extension_path_user`): the install id, the protected sign-in and the hosted
  freemode body, one folder per body version;
- short-lived folders named `dct-<kind>-<random>` in the system's temporary folder for exports and opened models,
  kept at a short path because Sollumz nests a model's name twice; stale ones from a Blender that closed are removed.

Never commit files from GTA V or data taken from them (models, textures, skeletons, meta files). The tests build
their garments, bodies and characters from scratch (`tests/support/synthetic.py`, `tests/support/mannequin.py`).

## Supported Blender versions

| What | Version | Where it is enforced or tested |
|---|---|---|
| Oldest Blender | 4.2.0 | `blender_version_min` in the manifest |
| Platform | Windows x64 | `platforms` in the manifest; DPAPI and the loopback connection to Durty Cloth Tool |
| Python | 3.11 (Blender 4.2 to 4.5) and 3.13 (Blender 5.x) | CI runs the tests with both, with numpy 1.26.4 and 2.3.4 as Blender bundles them, on Windows and Linux |
| Smoke-tested | 4.5 LTS and 5.2 LTS | `tools/blender_smoke.py`, run locally before a release and for Blender-side changes |
| Release build | 4.5.9 LTS | the official build pinned by SHA-256 in `.github/workflows/release.yml` |
| Sollumz | 2.8.0 or later, tested with 2.9.0 | `SOLLUMZ_MINIMUM` and `SOLLUMZ_TESTED` in `settings.py` |

Keep the code free of language features newer than Python 3.11. Version-specific behaviour the code knows about:
Blender before 5.2 cannot import the compressed hosted body (`garment_body.py` asks for the plain copy and otherwise
explains it), and Blender 5.2 can crash when a UV layer is added before the existing UVs are read (`garment_host.py`
reads them first).

## Tests and tools

Set up and run the checks as [CONTRIBUTING.md](/CONTRIBUTING.md#-running-the-checks) describes:

```powershell
python -m pytest
python tools/check_manifest.py
python tools/sync_dct_link.py --check
```

The pytest suite needs no Blender. It covers pixel conversion, Sollumz exports, settings and hosts, the nine
languages, the manifest and the vendored copy, the release checks, Garment Fitting and Custom Ped on synthetic meshes,
and the whole link flow against a fake Durty Cloth Tool (`tests/support/fake_dct.py`) and a fake gta.clothing
(`tests/support/fake_link_api.py`) on `127.0.0.1`. It also enforces repository rules: no em dashes in texts and
documents, only known hosts, every relative path and document a text names exists here, and the SPDX header of every
add-on module.

### Blender smoke test

```powershell
python tools/blender_smoke.py --blender "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
```

For each `--blender` (repeatable) it validates the source, builds the archive into `dist/`, validates the archive, and
runs `tests/blender/smoke_in_blender.py` in a background Blender with a throw-away user folder, so your own Blender
settings and extensions are never touched and nothing is sent to gta.clothing. The smoke drives the link, Garment
Fitting (`tests/blender/garment_smoke.py`) and Custom Ped (`tests/blender/ped_smoke.py`) through their operators. A
Sollumz stand-in (`tests/blender/sollumz_stub.py`) is used unless you add `--sollumz <Sollumz extension folder>
--sollumz-site <folder with its szio package>` to test with a real Sollumz.

### Screenshots

`tools/blender_shots.py` walks the DCT tab through its states against the fakes in a Blender window and saves a
cropped screenshot of the sidebar for each:

```powershell
python tools/blender_shots.py --blender "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --out <folder>
```

`--scenario garment` or `--scenario ped` walks Garment Fitting or Custom Ped, `--expanded` opens every collapsed
panel, `--language de_DE` and `--theme light` give variants, and `--text-size 14` shows what a narrow sidebar cuts or
wraps. The fakes sign in as "Durty", the name the screenshots show.

### Measuring an avatar

`garment_avatars.py` holds the joints of known Marvelous Designer and CLO stock avatars. To add one, export a garment
as FBX with the rigged avatar and run:

```powershell
blender --background --factory-startup --python tools/measure_avatar.py -- <the exported .fbx>
```

It prints the avatar's joints as markers in ped space and the pose's arm angle. Only these numbers go into the
repository, with the avatar's template id and where they were measured; never the avatar, its mesh or the file.

### Building the archive by hand

```powershell
blender --command extension build --source-dir durty_cloth_tool_link --output-dir dist
```

Install the result with **Install from Disk** to try it in your own Blender. `dist/` is ignored by Git.

## Versions and releases

Releases are made by the maintainers. Creating or moving a tag is a release action that needs the owner's explicit go.

- The version lives in `blender_manifest.toml` and in `VERSION` in `settings.py` (the tests check that they match):
  `X.Y.Z`, or `X.Y.Z-experimental.N` for an Experimental build. The channel follows from the version.
- The manifest's listing values (id, name, tagline, maintainer, type, website, tags, licence, platforms, permissions)
  must equal the listing in gta.clothing's extension repository; `tools/check_manifest.py` checks them and Blender's
  rules for taglines and permission texts.
- Pushing the tag `v<version>` on a commit of `main` starts `.github/workflows/release.yml`: the tests run, the
  pinned Blender validates and builds the archive, `tools/release_tool.py` gives every file the commit time so the
  archive is reproducible byte for byte and checks its contents, and the publish job (the only one with write access,
  running no repository code) creates the GitHub release with the archive and its SHA-256, as a pre-release for
  Experimental versions.
- A published release is never replaced; a fix gets a new version.
- The maintainers then publish the version in gta.clothing's extension repository, from which Blender updates installed
  copies on the matching channel. That step happens outside this repository.

## Keeping documents current

- Update this document in the same change when you change the architecture, the connection, what the add-on stores or
  sends, the supported versions, the tools or the release process.
- Keep the [README](/README.md) short: what the add-on does, requirements, install, getting started, limits and
  links. Step-by-step guidance belongs in the public documentation, which a change to a control or a step must follow.
- Replace a README image only with a real screenshot of the add-on that shows no private data; keep images in
  `docs/images` as WebP, well under 500 KB each, with descriptive alt text.
