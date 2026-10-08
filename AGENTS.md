# Agent guide: Durty Cloth Tool Link for Blender

This repository is the public, open-source Blender add-on **Durty Cloth Tool Link** (extension id
`durty_cloth_tool_link`), one of the Creator Link plugins of Durty Cloth Tool. It connects Blender to Durty Cloth Tool
on the same Windows computer (Live Preview, Push Model, Edit in connected app) and adds two Experimental toolsets that
also work on their own: Garment Fitting and Custom Ped. The add-on is GPL-3.0-or-later, the vendored `dct_link`
client is MIT, and the Durty Cloth Tool logo is a protected mark (see `NOTICE`).

Read these before you change anything:

1. [README.md](README.md): what users get, in the product's own words.
2. [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md): modules, threads, the connection to Durty Cloth Tool, stored data,
   supported Blender versions, tools and releases.
3. [CONTRIBUTING.md](CONTRIBUTING.md): code style, the rules for texts and translations, the pull request checklist.

## Where things live

| Path | What it is |
|---|---|
| `durty_cloth_tool_link/` | The extension, and the only folder that ships. `blender_manifest.toml` and `VERSION` in `settings.py` carry the version. |
| `durty_cloth_tool_link/dct_link/` | The vendored Creator Link client. Read-only here, see below. |
| `durty_cloth_tool_link/strings.py`, `ped_strings.py`, `translations/` | Every user-facing text: English plus eight translations. |
| `tests/` | pytest tests without Blender; `tests/support` holds the fake Durty Cloth Tool, the fake gta.clothing and the synthetic meshes. |
| `tests/blender/` | The smoke test that runs inside Blender. |
| `tools/` | Manifest, vendoring and release checks, the Blender smoke and screenshot runners, avatar measurement. |
| `docs/` | The development document and the README images (`docs/images`). |
| `.github/workflows/` | CI (`ci.yml`) and the tag-triggered release (`release.yml`). |

## Build and test

Windows and Python 3.13, with a virtual environment (`.venv` in the repository root is ignored by Git):

```powershell
py -3.13 -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements-dev.txt "numpy==2.3.4"

python -m pytest                       # about four minutes, no Blender needed
python tools/check_manifest.py
python tools/sync_dct_link.py --check
```

For any change to the Blender side (operators, panels, `*_host.py`, `garment_dct.py`, `addon.py`), also run the smoke
test with a real Blender; Blender 5.2 is usually at the path below:

```powershell
python tools/blender_smoke.py --blender "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
```

It builds the archive into `dist/` (ignored by Git) and uses a throw-away Blender user folder. Report the exact
commands and results you ran. Interface changes also need screenshots from `tools/blender_shots.py`.

## Conventions the code follows

- Logic lives in modules that do not import Blender, tested with plain pytest; the `bpy` code stays thin.
- Never block Blender's interface: network and long work run on worker threads or in steps that a `bpy.app.timers`
  timer checks. Worker threads never touch Blender.
- Standard library and numpy only, Python 3.11 compatible (Blender 4.2 to 4.5 bundle 3.11).
- Every add-on module starts with the SPDX header and the copyright line of the existing modules. Tool scripts start
  with the `#!/usr/bin/env python3` line and then the same two lines, and tests carry the SPDX header. Docstrings say
  what and why in plain English; type hints throughout; lines of about 120 characters.
- Logic never stores, compares or parses displayed text: it passes `strings.Msg` keys. A new or changed English text
  gets all eight translations in the same change, with the same `{fields}`. Labels and buttons in Title Case,
  messages as sentences. Logs and Copy Diagnostics stay English.
- No em dashes anywhere, in code, texts or documents (a test fails on them).
- The tests also fail on a host that is not on the allowlist in `tests/test_settings.py`, and on any relative path or
  document name in a text file that does not exist in this repository. Do not name files of other repositories.
- Never commit GTA V files or data taken from them. Tests build their meshes from scratch.
- Commits: a short imperative subject in plain English ("Keep the add-on's temporary files at a short path"), and a
  body that says why when it is not obvious.

## Words to use

Use the add-on's own interface names exactly, and check `strings.py` when unsure:

- **Durty Cloth Tool**, **Creator Link**, **connected app**, **Edit in connected app**, **gta.clothing** (always lower
  case). The short name DCT appears only in the **DCT** tab and in the names of what the add-on creates in a scene,
  such as the vertex groups DCT Tears, DCT Pinned and DCT Lining and the UV map DCT Source UV.
- **Linked Cloth**, **Live Preview**, **Texture Checks**, **Save to Cloth**, **Save as New Variation**, **Push Model**,
  **Push Automatically**, **Save Model to Cloth**, **Work On**.
- **Garment Fitting**, **Fit on gta.clothing** (never "Fit to Body"), **Transfer Weights**, **Add to Project**,
  **freemode body**, **Custom Ped**, **Rig in Durty Cloth Tool**, **Create Custom Ped**.
- "Garment" is the interface's word for the object Garment Fitting works on (Import Garment, the Garment field, "the
  garment" in its messages). Documentation prose, including the README and these documents, says cloth or clothing.
- British spelling: colour, licence (the noun). Support goes to the **Pleb Masters Community Discord**.

## The public repository boundary

Everything here is public and ships to users. Describe only this add-on's own code and its public behaviour.

- No secrets, keys, tokens, unpublished endpoints, private repository paths, release infrastructure details or
  internal notes, in code, comments, tests, documents or commit messages.
- Nothing about Durty Cloth Tool's or gta.clothing's internals beyond what the add-on's code already shows.
- User-facing copy (the README, texts, release notes) describes outcomes, controls, requirements, limits and
  recovery, never algorithms, conversion heuristics or data layouts.
- Images show real screens of the add-on with no account e-mail, licence key, private path or game file.

## The vendored dct_link client

`durty_cloth_tool_link/dct_link/` is a byte-for-byte copy of the `dct_link` package from the Durty Cloth Tool
repository; `VENDORED.md` in that folder records its version, the Creator Link protocol version and every file's
SHA-256. Never edit it here. It must stay in sync with Durty Cloth Tool: a wire format change is made in Durty Cloth
Tool's Creator Link protocol package and in `dct_link` together, then copied here with
`python tools/sync_dct_link.py <Durty Cloth Tool checkout>`, in its own commit ("Sync dct_link with ...").
The copy is synced from Durty Cloth Tool's `dev` branch. `--check` also compares with a Durty Cloth Tool checkout
beside this repository when one exists; if that checkout is behind `dev`, update it or compare with `dev` instead of
syncing backwards.

## Documents

- Keep the README short: what it does, requirements, install, getting started, limits, privacy, links. Detailed
  steps belong in the public documentation it links to.
- Put technical changes (architecture, connection, stored or sent data, supported versions, tools, release process)
  into [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) in the same change.
- A change to a control or a step also needs the matching change in the public Blender documentation.

## Never do without the owner's explicit go

- Push to any remote branch, open or merge a pull request, or publish anything.
- Create, move or delete a tag. A `v<version>` tag starts a public release.
- Change version numbers, the manifest's listing values or the host allowlist.

## No AI attribution

Add no AI attribution anywhere: no co-author trailers, no generated-by lines, and no attribution in files, code
comments, documents or commit messages. Write as a human author would.
