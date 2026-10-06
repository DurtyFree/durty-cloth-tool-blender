<div align="center">

<img src="durty_cloth_tool_link/icons/dct-mark.png" alt="Durty Cloth Tool" width="112">

# Durty Cloth Tool Link for Blender

**Paint, model and fit GTA V clothing in Blender, and see it on the ped in Durty Cloth Tool while you work.**

[![CI](https://github.com/DurtyFree/durty-cloth-tool-blender/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/DurtyFree/durty-cloth-tool-blender/actions/workflows/ci.yml)
[![Latest release](https://img.shields.io/github/v/release/DurtyFree/durty-cloth-tool-blender?include_prereleases&sort=semver&label=release)](https://github.com/DurtyFree/durty-cloth-tool-blender/releases)
[![Licence: GPL-3.0-or-later](https://img.shields.io/badge/licence-GPL--3.0--or--later-blue)](LICENSE)
[![Blender 4.2 or later](https://img.shields.io/badge/Blender-4.2%2B-E87D0D?logo=blender&logoColor=white)](#-requirements)
[![Platform: Windows x64](https://img.shields.io/badge/platform-Windows%20x64-0078D4)](#-requirements)

[Install](#-installation) · [Getting started](#-getting-started) · [Documentation](https://docs.gta.clothing/creator-link/blender) · [Discord](https://discord.plebmasters.de) · [Releases](https://github.com/DurtyFree/durty-cloth-tool-blender/releases)

</div>

---

**Durty Cloth Tool Link** is the free, open-source Blender add-on for [Durty Cloth Tool](https://gta.clothing/), the
Windows app for creating GTA V clothing packs for FiveM and singleplayer. The add-on adds a **DCT** tab to Blender's
3D Viewport sidebar. Connected to Durty Cloth Tool on the same computer, it shows the texture you paint and the model
you edit on the cloth in Durty Cloth Tool's 3D Preview, and saves them into your project when you are happy with the
result. Its garment tools take a garment from Marvelous Designer or any FBX, OBJ or glTF file towards a game-ready
freemode cloth and add it to your Durty Cloth Tool project.

## ✨ Features

<img src=".github/images/dct-tab-live.png" alt="The DCT tab in Blender's sidebar during a live preview: the linked cloth, the live preview controls and a texture check" width="250" align="right">

- 🎨 **Live Preview.** Paint a texture in Blender and see it on the cloth after every paint stroke, as its diffuse,
  normal or specular map. Save it to the cloth, save it as a new texture variation, or discard it.
- ✅ **Texture Checks.** Durty Cloth Tool checks your image against what GTA V and the cloth need, before you save.
- 🧱 **Model push.** Send your Sollumz Drawable Dictionary straight into Durty Cloth Tool's 3D Preview. With
  **Push Automatically**, the ped updates a moment after every change. Save the model to the cloth when it is done.
- ✏️ **Edit in connected app.** Pick a cloth in Durty Cloth Tool and open its texture maps or its model in Blender,
  already linked to that cloth and showing on the ped.
- 👕 **Linked Cloth.** See the open project and the selected cloth (variation, type, gender, collection and number),
  with its picture and buttons that open its maps in Blender.
- 🪡 **Garment Fitting (Experimental).** Import a garment, add the freemode body, place joint markers, align the
  garment to the body (a T-pose becomes the game's pose on the way), push it out of the body, snug or relax regions,
  see problem areas in colour, run a fit check, sculpt with the body as a guide and check seams for tears.
  **Game Ready** joins seams, sets the ped vertex colours, combines all materials into one texture with its
  transparency and maps, generates levels of detail and validates the result.
- ➕ **Add to Durty Cloth Tool Project (Experimental).** Put a game-ready garment on the freemode skeleton, export it
  with Sollumz and add it as a new cloth, with its colour variations, to the project open in Durty Cloth Tool.
  Durty Cloth Tool shows the cloth first, and nothing is added until you confirm it there.
- 🌍 **Nine languages.** The add-on follows Blender's interface language: English, German, French, Russian, Spanish,
  Brazilian Portuguese, Simplified Chinese, Hindi and Arabic.
- ↩️ **Undo-friendly.** Nothing changes in your project until you choose to save, and Durty Cloth Tool keeps every
  save in the cloth's History, so you can undo it.

<br clear="right">

### Free and Durty Cloth Tool Ultimate

The add-on is free to install and use. What it does with a Durty Cloth Tool project depends on your Durty Cloth Tool
plan; the panels say in place when a feature is not part of yours.

| Feature | Free | Ultimate |
|---|:---:|:---:|
| Connect Blender to Durty Cloth Tool, see the open project and the selected cloth | ✅ | ✅ |
| Garment Fitting tools that run in Blender (no account needed) | ✅ | ✅ |
| The hosted freemode body for Garment Fitting | ✅ | ✅ |
| Add a garment to your project as a new cloth (Durty Cloth Tool's project limits apply) | ✅ | ✅ |
| Live Preview, Save to Cloth and Save as New Variation | | ✅ |
| Model push, Push Automatically and Save Model to Cloth | | ✅ |
| Texture Checks, the cloth's picture and opening its maps in Blender | | ✅ |
| Edit in connected app from Durty Cloth Tool | | ✅ |

"Free" means any free gta.clothing account. See [gta.clothing](https://gta.clothing/) for the plans.

## 📋 Requirements

| You need | Version | For |
|---|---|---|
| 🪟 Windows | 64-bit | Everything: the add-on runs on Windows only |
| 🧊 Blender | 4.2 or later (tested with 4.5 LTS and 5.2 LTS) | Everything |
| 👕 [Durty Cloth Tool](https://gta.clothing/) | A current version, running on the same computer | Everything that works with a project |
| 👤 A gta.clothing account | Free, you sign in with Discord | Connecting to Durty Cloth Tool, the hosted freemode body |
| 🧩 [Sollumz](https://docs.sollumz.org/) | 2.8.0 or later (tested with 2.9.0) | Pushing and opening models, Generate LODs, adding a garment to a project |
| 🎮 GTA V, set up in Durty Cloth Tool | | The preview on the ped, adding a garment to a project |

Also good to know:

- Turn on Blender's **Allow Online Access** (**Edit > Preferences > System > Network**). Your work goes to Durty Cloth
  Tool on your own computer, but each connection is confirmed with your gta.clothing sign-in.
- Your Discord account must be a member of the [Pleb Masters Community Discord](https://discord.plebmasters.de)
  server to sign in.
- Blender and Durty Cloth Tool must be signed in with the same account.
- When the add-on and Durty Cloth Tool are too far apart in version, the DCT tab says which one to update.

## 📦 Installation

### Option 1: Drag into Blender (recommended)

1. Open the [plugins page on gta.clothing](https://gta.clothing/account/plugins/). You do not need to sign in to
   download.
2. Choose the channel: **Release** or **Experimental**. The channel you choose is the one Blender updates the add-on
   from. While the add-on is Experimental, only the Experimental channel has a version.
3. Drag **Drag into Blender** onto an open Blender window and confirm. Blender adds the Durty Cloth Tool extension
   repository.
4. Drag it onto Blender again and confirm. Blender installs the add-on.

Durty Cloth Tool offers the same button: **View > Connect an app**, on the Blender row.

### Option 2: From Durty Cloth Tool

Close Blender, choose **View > Connect an app** in Durty Cloth Tool and select **Install** on the Blender row.
Durty Cloth Tool installs the add-on into Blender for you.

### Option 3: From a file

1. Download `durty_cloth_tool_link-<version>.zip` from the
   [GitHub releases](https://github.com/DurtyFree/durty-cloth-tool-blender/releases), or **Download .zip** on the
   [plugins page](https://gta.clothing/account/plugins/).
2. In Blender, open **Edit > Preferences > Get Extensions**, open the menu at the top right and choose
   **Install from Disk**, then pick the file.

Blender cannot update a copy installed from a file, and the add-on's Settings say so. To get updates, install it
with Option 1 instead.

### 🔄 Updating

An add-on installed with Option 1 or 2 updates like any other Blender extension: **Edit > Preferences > Get
Extensions > Check for Updates**. **Settings > Updates** in the DCT tab shows your version and channel.

### 🗑️ Uninstalling

1. Sign out first: **Settings > Account > Sign Out** in the DCT tab. With online access on, this also ends the
   session on gta.clothing.
2. Uninstall **Durty Cloth Tool Link** in **Edit > Preferences > Get Extensions**. This removes the stored sign-in
   from your computer.
3. To stop Blender from looking for updates, remove the Durty Cloth Tool repository under **Repositories** on the
   same page.

## 🚀 Getting started

### Connect

1. Start Durty Cloth Tool, sign in and open a project.
2. In Blender, press **N** in the 3D Viewport and open the **DCT** tab.
3. **Get Connected** walks you through two steps:
   - **Find Durty Cloth Tool.** The add-on finds it by itself. Otherwise select **Connect**.
   - **Sign In with gta.clothing.** Select **Sign In**. Durty Cloth Tool shows the sign-in request with a code:
     check it and select **Approve**. When Durty Cloth Tool is not running, the add-on shows a code for your
     browser instead.

You do this once per Blender installation. The header of the **Durty Cloth Tool** panel then says **Connected**.

### Paint a texture live

1. In Durty Cloth Tool, select a cloth and a texture variation. The **Linked Cloth** panel shows them.
2. Under **Live Preview**, pick your **Image** and the **Map** it replaces: **Diffuse (Colour)**, **Normal** or
   **Specular**. Set normal and specular maps to **Non-Color** in Blender.
3. Select **Start Live Preview** and paint. The ped updates after each stroke.
4. Select **Save to Cloth**, **Save as New Variation** or **Discard Changes**.

Images can be up to 4096 by 4096 pixels. To start from the cloth's own texture, use **Open a Map in Blender** under
**Linked Cloth**.

### Push a model

1. In Durty Cloth Tool, select the cloth whose model you want to replace in the 3D Preview.
2. In Blender, select your Sollumz **Drawable Dictionary** (or any object inside it).
3. Under **Model**, select **Push Model**. Turn on **Push Automatically** to send it again after every change.
4. Select **Save Model to Cloth** to keep it, or **Discard**.

### Fit a garment (Experimental)

Open **Garment Fitting (Experimental)** in the DCT tab. Its first line always tells you the next step, and the
button for that step is the large one. Settings you rarely change sit in closed **Options** sections.

1. **Setup:** choose gender, slot, category and the pose the garment was made in, then **Import Garment** and
   **Add Freemode Body**. The import converts centimetres, millimetres and inches to metres, and turns a garment
   that lies down or faces backwards.
2. **Fit:** **Auto Markers**, then check the markers and move any that are off (lines in the 3D view join them and
   turn orange when something looks wrong). Then **Align to Body**: it moves and turns the garment so the markers
   sit on the body's joints, and turns its arms (or legs) onto the body's, so a T-pose becomes the game's pose
   without opening a seam.
3. **Fix:** **Run Fit Check**, **Push Out of Body**, **Show Problems**, **Snug to Body** and **Relax Stretched**, or
   sculpt by hand. These tools wait for **Align to Body**, because they measure against the body.
4. **Game Ready:** **Prepare Garment** and **Combine Materials** (which keeps transparency and bakes normal,
   specular and emission maps), then weight the garment to the freemode skeleton, then **Generate LODs** and
   **Validate**.

Every step that changes the garment can be undone with **Ctrl+Z**, and the garment keeps backups of its shape for
**Back One Step** and **Restore Pre-fit**. The [Garment Fitting guide](https://docs.gta.clothing/creator-link/blender/garment-fitting) and the
[Game Ready guide](https://docs.gta.clothing/creator-link/blender/game-ready) walk through each step.

### Add the garment to your project (Experimental)

The last part of **Game Ready** adds the garment as a new cloth to the project open in Durty Cloth Tool. You need:

- Durty Cloth Tool connected, with a freemode project open (a custom ped project takes no clothing this way), and
  GTA V set up in it: the freemode skeleton comes from your own game files.
- Sollumz.
- One material with a colour texture (**Combine Materials** makes one).
- Weights for the freemode skeleton: vertex groups named after its bones, such as `SKEL_Spine3`. Weight the garment
  yourself, for example with Blender's weight painting. **Use Durty Cloth Tool Skeleton** gives you the bones to
  weight to; levels of detail made before the weights get them when the garment is added.

Then:

1. Fill in **Cloth Name** (empty uses the garment's name) and turn on **Shows Skin** when the cloth shows some of the
   ped's skin. Slot and gender are the ones chosen under **Setup**.
2. Optionally use **Add Colour Variation** for more colour variations from other images in the same layout, up to
   26, each with its own name. Each side of a picture must divide by four and be at most 4096 pixels; powers of two
   up to 2048 pixels work best.
3. Select **Add to Durty Cloth Tool Project**. The add-on checks the garment and lists anything that blocks the add
   under the button. It puts the garment on the Durty Cloth Tool skeleton when needed (**Use Durty Cloth Tool
   Skeleton** does this on its own), exports it with Sollumz, writes the colour variations and sends it to Durty
   Cloth Tool, showing its progress; **Cancel** stops it at any point.
4. Durty Cloth Tool shows the cloth with its checks. Nothing is added until you choose **Add to project** there;
   **Cancel** in Blender withdraws the add while Durty Cloth Tool still asks.

Durty Cloth Tool's plan limits apply to every add, and the panel says when the project is full. Once the cloth is
added, the garment's model is linked to it, so **Push Model** and **Save Model to Cloth** update that cloth (with
Durty Cloth Tool Ultimate), also when Durty Cloth Tool confirms the add only after a cancel. Undo in Blender does not
remove the cloth from the project; remove it in Durty Cloth Tool. The
[Add to a Project guide](https://docs.gta.clothing/creator-link/blender/add-to-a-project) has the details.

The [Blender documentation](https://docs.gta.clothing/creator-link/blender) explains the add-on step by step, with
[live preview and models](https://docs.gta.clothing/creator-link/blender/live-preview-and-models) and [use cases](https://docs.gta.clothing/creator-link/blender/use-cases); the
[documentation](https://docs.gta.clothing/) covers Durty Cloth Tool itself.

## 🧭 How it works

- 🧊 **Inside Blender.** The add-on is a regular Blender extension. It needs nothing else installed, apart from
  Sollumz for models.
- 🖥️ **Talks to Durty Cloth Tool on your computer.** Your images, models and garments go only to Durty Cloth Tool on
  the same computer, never over the internet. Durty Cloth Tool sends back what you ask for: the cloths you open in
  Blender and, for an add, the freemode skeleton built from your own game files.
- 👤 **Signs in with gta.clothing.** You sign in once with your gta.clothing account. Durty Cloth Tool accepts
  Blender when both are signed in with the same account, and lists it under **Options > Connected apps**, where you
  can disconnect it. The add-on never sees your Discord password.
- 🌐 **What reaches gta.clothing:** your sign-in (with your computer's name, unless you turn that off under
  **Settings > Privacy**), a confirmation each time Blender connects to Durty Cloth Tool, your sign-out, the
  download of the freemode body (once per body version) and Blender's update checks.
- 🙅 **No tracking.** The add-on collects no usage data. **Copy Diagnostics** copies versions and status codes for
  support, without file paths, names or sign-in data.
- 🔐 **Your sign-in stays protected.** It is kept in the add-on's user folder, encrypted for your Windows user
  account.

## 🔗 Links

- 🌐 **gta.clothing:** [gta.clothing](https://gta.clothing/), Durty Cloth Tool's website and your account
- 📚 **Documentation:** [the Blender add-on](https://docs.gta.clothing/creator-link/blender) on [docs.gta.clothing](https://docs.gta.clothing/)
- 🔌 **Plugins page:** [the plugins page on gta.clothing](https://gta.clothing/account/plugins/), with the install
  links of every Durty Cloth Tool plugin
- 💬 **Community and support:** the [Pleb Masters Community Discord](https://discord.plebmasters.de). Use **Copy
  Diagnostics** in the **?** menu of the DCT tab and paste it with your question.
- 🐛 **Bugs and ideas:** [GitHub issues](https://github.com/DurtyFree/durty-cloth-tool-blender/issues)

## 🤝 Contributing

Bug reports, fixes, translations and ideas are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md) for the development
setup, the tests and how to send a pull request. For questions, join the
[Pleb Masters Community Discord](https://discord.plebmasters.de).

## 🔒 Security

Please do not report security problems in public issues. [SECURITY.md](SECURITY.md) explains how to report them
privately.

## 📜 Licence

Copyright (c) 2026 Schmid Software Solutions ([schmid-software.de](https://schmid-software.de)). Maintained by
DurtyFree (Pleb Masters).

- The add-on is free software under the GNU General Public License, version 3 or (at your option) any later version
  (`GPL-3.0-or-later`, see [LICENSE](LICENSE)).
- The `dct_link` package in `durty_cloth_tool_link/dct_link` is MIT licensed (see its `LICENSE`).
- The Durty Cloth Tool logo (`durty_cloth_tool_link/icons/dct-mark.png`) is not covered by the GPL or the MIT
  licence. It is a mark of Schmid Software Solutions, included only to identify Durty Cloth Tool, and may not be
  modified or used for any other purpose (see [NOTICE](NOTICE)).
- Durty Cloth Tool itself is proprietary software, and gta.clothing is a separate service. Neither is part of this
  repository or covered by these licences.
