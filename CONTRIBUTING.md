# Contributing to Durty Cloth Tool Link for Blender

Thank you for helping! Bug reports, fixes, translations, tests and ideas are all welcome. This guide explains how the
repository is laid out, how to set it up on Windows, how to run the checks and what a pull request needs.

Questions are best asked in the [Pleb Masters Community Discord](https://discord.plebmasters.de). Security problems
never go into a public issue: follow [SECURITY.md](SECURITY.md). How the add-on looks to its users is described in
[the Blender documentation](https://docs.gta.clothing/creator-link/blender); a change to a control or a step there needs a matching change in those pages.

## 🧭 Before you start

- **Small fixes** (a typo, a wrong translation, a clear bug): open a pull request straight away.
- **Bigger changes** (a new feature, a new panel, a change to how the add-on behaves): open an issue first, so we can
  agree on the approach before you spend time on it.
- **Changes to the connection with Durty Cloth Tool** need a change in the `dct_link` package, which is not edited
  in this repository. See [The vendored dct_link package](#-the-vendored-dct_link-package).
- By sending a pull request you agree that your contribution is licensed under the add-on's licence,
  GPL-3.0-or-later (see [LICENSE](LICENSE)).

## 🗂️ Repository layout

```
durty_cloth_tool_link/   the extension: blender_manifest.toml, the add-on modules, the translations and the logo
durty_cloth_tool_link/dct_link/   the Creator Link client, vendored (read-only here)
tests/                   pytest tests (no Blender needed), the fakes they use, and the Blender smoke test
tools/                   manifest check, dct_link check, release checks, Blender smoke and screenshot runners,
                         avatar measurement
.github/                 CI and release workflows, issue forms and the pull request template
```

Only `durty_cloth_tool_link/` goes into the extension archive. Inside it:

- `settings.py` holds constants and public addresses, `strings.py` every English text, `translations/` the eight
  other languages.
- `link.py` runs the connection, the sign-in, the live preview and the model pushes. `bundle.py` collects a Sollumz
  export, `pixels.py` converts Blender's pixels.
- `garment*.py` are the Garment Fitting tools, and `ui_garment.py` their panel.
- `ped*.py` are Custom Ped: `ped.py` the markers, checks and rig maths, `ped_link.py` its part of the link,
  `ped_host.py` its Blender side, `ped_strings.py` its English texts, and `ui_ped.py` its panel.
- `host.py`, `state.py`, `ui.py`, `ui_garment.py`, `garment_host.py`, `ui_ped.py`, `ped_host.py`, `preferences.py` and
  `addon.py` are the Blender side.

Modules without a Blender import can be tested with plain Python. Keep it that way: put the logic in a Blender-free
module and keep the code that touches `bpy` thin.

## 🛠️ Development setup (Windows)

You need Windows (64-bit), Python 3.13 and Git. For the Blender smoke test you
also need Blender 4.2 or later (5.2 LTS recommended), and Sollumz to test models.

```powershell
git clone https://github.com/DurtyFree/durty-cloth-tool-blender.git
cd durty-cloth-tool-blender
py -3.13 -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements-dev.txt "numpy==2.3.4"
```

The add-on itself needs nothing outside Blender: Blender bundles Python and numpy. The numpy version matches
Blender's: 2.3.4 for Python 3.13 (Blender 5.x). CI also tests Python 3.11 with numpy 1.26.4 (Blender 4.2 to 4.5), on
Windows and Linux, so do not use language features newer than Python 3.11.

## ✅ Running the checks

Run these before every pull request. CI runs the same.

```powershell
python -m pytest
python tools/check_manifest.py
python tools/sync_dct_link.py --check
```

The tests cover pixel conversion, colour handling, capture scheduling, Sollumz exports, settings, the nine languages,
the manifest, the vendored copy and the whole link flow against a fake Durty Cloth Tool and a fake gta.clothing on
`127.0.0.1`. The Garment Fitting tools are tested on synthetic garments and bodies.

### Blender smoke test

For changes to the Blender side, also run the smoke test with at least one Blender version:

```powershell
python tools/blender_smoke.py --blender "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
```

It validates and builds the extension into `dist/`, then runs `tests/blender/smoke_in_blender.py` in a background
Blender. Repeat `--blender` to test several versions. Add `--sollumz <Sollumz extension folder> --sollumz-site <folder
with its szio package>` to push and open models through a real Sollumz. The smoke uses a throw-away Blender user
folder, so your own Blender settings and extensions are never touched, and nothing is sent to gta.clothing.

### Screenshots

For interface changes, attach screenshots to your pull request. `tools/blender_shots.py` walks the DCT tab through its
states against the fakes and saves a cropped screenshot of the sidebar for each:

```powershell
python tools/blender_shots.py --blender "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --out <folder>
```

Add `--expanded` to open every collapsed panel, `--language de_DE` or `--theme light` for variants, `--text-size 14`
for what a narrower sidebar cuts off or wraps, `--scenario garment` for Garment Fitting and `--scenario ped` for
Custom Ped. Blender opens a window and quits by itself.

### Measuring an avatar

The garment tools know the joints of some Marvelous Designer and CLO stock avatars (`garment_avatars.py`). To add
one, export a garment from Marvelous Designer or CLO as FBX with the rigged avatar and run:

```powershell
blender --background --factory-startup --python tools/measure_avatar.py -- <the exported .fbx>
```

It prints the avatar's joints as markers in ped space and the pose's arm angle. Only these numbers go into the
repository, with the avatar's template id and where they were measured; never the avatar, its mesh or the file.

### Building the archive by hand

```powershell
blender --command extension build --source-dir durty_cloth_tool_link --output-dir dist
```

You can install the result with **Install from Disk** to try it in your own Blender.

## ✍️ Code style

- Follow the style of the code around your change: type hints, docstrings that say what and why in plain English,
  lines of about 120 characters.
- Use the standard library and numpy only. The add-on has no other dependencies.
- Every add-on module starts with the same SPDX licence header as the existing modules (a test checks it).
- Never block Blender's interface: network work runs in background tasks that a timer checks.
- Logic never compares or stores displayed text. Pass text keys and `Msg` values from `strings.py`.
- No em dashes in texts, comments or documentation (a test checks it).
- The add-on talks only to Durty Cloth Tool on the same computer and to gta.clothing, and opens only gta.clothing,
  its documentation and the Discord server in the browser. A new address needs an issue first; the tests list the
  hosts the repository may name.
- Never commit files from GTA V or data taken from them (models, textures, skeletons, meta files). The tests build
  their garments and bodies from scratch in `tests/support/synthetic.py`.

## 🌍 Texts and translations

The add-on speaks English, German, French, Russian, Spanish, Brazilian Portuguese, Simplified Chinese, Hindi and
Arabic.

- Every text the add-on shows has a key in `EN` in `durty_cloth_tool_link/strings.py`.
- Every Custom Ped text has its key in `EN` in `durty_cloth_tool_link/ped_strings.py`, which `strings.py` merges.
- Each language has three modules in `durty_cloth_tool_link/translations/`, named after Blender's locale (`de`, `fr`,
  `ru`, `es`, `pt_BR`, `zh_HANS`, `hi`, `ar`): `<locale>.py` for the link, `garment_<locale>.py` for Garment
  Fitting and `ped_<locale>.py` for Custom Ped. Each holds a `TEXT` dictionary with the same keys.
- When you add or change an English text, change the key in all eight translations in the same pull request. The
  tests fail when a key is missing, when its `{fields}` differ from the English text, or when a protected name such
  as Durty Cloth Tool, Creator Link, gta.clothing, Blender or Sollumz is translated.
- If you cannot translate a language, say so in the pull request, and we will fill it in before merging.
- A text that counts things (`{count} vertex groups ...`) can have a second key ending in `.one` for exactly one
  thing (`{count} vertex group ...`); the add-on shows it when `count` is 1. Translate both. Where your language has
  more plural forms, word the other form so that it reads right with any number (`Groups: {count}`).
- Labels, buttons and panel titles use Title Case; descriptions, tooltips and messages are sentences. German uses the
  informal "du". Arabic is translated but not mirrored.
- Logs, the system console and Copy Diagnostics stay English.

Native speakers are very welcome to improve the existing translations.

## 🔌 The vendored dct_link package

`durty_cloth_tool_link/dct_link/` is the Creator Link client that the add-on uses to talk to Durty Cloth Tool. It is
developed together with Durty Cloth Tool and copied here byte for byte. `VENDORED.md` in that folder records the
SHA-256 of every file, and `python tools/sync_dct_link.py --check` (also run by the tests and CI) fails when a file
differs.

So please do not change files in `durty_cloth_tool_link/dct_link/` in a pull request. If the add-on needs something
from it, open an issue that describes what you need and why. The maintainers make the change together with Durty
Cloth Tool and sync the new copy here.

## 🚢 Releases

Releases are made by the maintainers; contributors do not change version numbers.

- The version lives in `durty_cloth_tool_link/blender_manifest.toml` and in `VERSION` in
  `durty_cloth_tool_link/settings.py`: `X.Y.Z`, or `X.Y.Z-experimental.N` for an Experimental release.
- Pushing the tag `v<version>` starts `.github/workflows/release.yml`. It runs the tests, builds and validates the
  archive with a pinned official Blender, makes the archive reproducible byte for byte and publishes it with its
  SHA-256 as a GitHub release (a pre-release for Experimental).
- A published release is never replaced. A fix gets a new version.
- The maintainers then publish the new version on gta.clothing's extension repository, from which Blender updates
  installed copies on the matching channel.

## 📝 Pull request checklist

- [ ] `python -m pytest`, `python tools/check_manifest.py` and `python tools/sync_dct_link.py --check` pass.
- [ ] Blender-side changes: `tools/blender_smoke.py` passes with at least one Blender version.
- [ ] Interface changes: screenshots are attached.
- [ ] New or changed texts are in all nine languages (or the pull request says which are missing).
- [ ] Nothing in `durty_cloth_tool_link/dct_link/` changed.
- [ ] No new dependency, network address or game file.
- [ ] Commit messages have a short subject in the imperative ("Fix the push of hidden models").

## 💬 Where to ask

- Questions and help: the [Pleb Masters Community Discord](https://discord.plebmasters.de)
- Bugs and feature ideas: [GitHub issues](https://github.com/DurtyFree/durty-cloth-tool-blender/issues)
- Security problems: [SECURITY.md](SECURITY.md)

Please be friendly and patient with each other. Everyone here wants to make better clothing.
