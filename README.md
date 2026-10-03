# Durty Cloth Tool Link for Blender

A Blender add-on that connects Blender to [Durty Cloth Tool](https://docs.gta.clothing) running on the same
computer, so you see your work on the freemode ped in Durty Cloth Tool's 3D preview while you work:

- **Live Preview.** Paint a texture in Blender and see it on the linked cloth after each paint stroke. Choose the
  map it replaces: Diffuse (Colour), Normal or Specular. When you like the result, save it to the cloth or as a
  new variation, or discard the changes.
- **Model.** Push a Sollumz Drawable Dictionary straight into Durty Cloth Tool's preview, replacing the linked
  cloth's model until you save or discard it. Turn on Push Automatically to send the model again a moment after
  each change.
- **Linked Cloth.** The panel shows the open project, the cloth selected in Durty Cloth Tool and its variation.
- **Texture Checks.** Durty Cloth Tool checks the image against what GTA V and the cloth need, before you save.

Nothing is saved in your project until you choose to save, and every save can be undone in the cloth's History in
Durty Cloth Tool. The add-on speaks Blender's interface language: English, German, French, Russian, Spanish,
Brazilian Portuguese, Simplified Chinese, Hindi and Arabic. It is open source under the GPL (see
[Licence](#licence)).

## Requirements

- Blender 4.2 or later on Windows (x64). Tested with Blender 4.5 LTS and 5.2 LTS; 4.2 to 4.4 are expected to
  work but are not tested.
- Durty Cloth Tool running on the same computer, with connected apps allowed (Options > Connected apps).
- A Durty Cloth Tool account (you sign in with Discord on gta.clothing). Blender and Durty Cloth Tool must use
  the same account. Some features are included in a Durty Cloth Tool plan; the panels say when yours does not
  include one.
- [Sollumz](https://docs.sollumz.org) 2.8.0 or later for pushing models (tested with Sollumz 2.9.0).
- Blender's **Allow Online Access** (Edit > Preferences > System > Network). The connection to Durty Cloth Tool
  stays on your computer, but each connection is confirmed with your gta.clothing sign-in, so without online
  access the add-on can neither sign in nor connect. The DCT tab says so while it is off.

## Install

**Drag and drop (recommended).** Open the [plugins page of your gta.clothing account](https://gta.clothing/account/plugins/)
and drag the Blender install link of the channel you want (Release or Experimental) onto a Blender window.
Blender adds the Durty Cloth Tool extension repository and installs the add-on; from then on Blender updates it
like any other extension (Get Extensions > Check for Updates). Durty Cloth Tool's Connected apps page (View >
Connect an app) offers the same link.

**From Durty Cloth Tool.** Durty Cloth Tool can install the add-on into Blender for you from its Connected apps
page (View > Connect an app). Close Blender first: Durty Cloth Tool installs it with Blender's command line.

**From a file.** Download the add-on archive and use Edit > Preferences > Get Extensions > Install from Disk.
Blender cannot update a copy installed this way; the add-on's Settings say so. To switch to updates, drag the
install link onto Blender as described above.

The extension repository is public: `https://gta.clothing/link/blender/release/index.json` (or `experimental`
instead of `release`). The install link is
`https://gta.clothing/link/blender/<channel>/durty_cloth_tool_link.zip?repository=.%2Findex.json&blender_version_min=4.2.0&platforms=windows-x64`,
which Blender reads as described in its manual (Extensions > Creating a repository > Download Links).

## The DCT tab

Open the 3D View sidebar (N) and the **DCT** tab. It has these panels, in this order:

| Panel | What it is for |
|---|---|
| Durty Cloth Tool | The connection status in one word (Connected, Live, Connecting, Action Needed, Offline, Problem). Click it for the connection details, Connect or Disconnect, and Copy Diagnostics. |
| Get Connected | Only while setup is incomplete: the setup steps, one at a time. The panels below appear once Durty Cloth Tool is found and you are signed in. |
| Linked Cloth | The project, the cloth and variation selected in Durty Cloth Tool, and the map to replace. |
| Live Preview | Start, pause and stop the live preview; Save to Cloth, Save as New Variation, Discard Changes; while it runs, the Texture Checks with Durty Cloth Tool's findings for the image. |
| Model | Push Model, Push Automatically, Save Model to Cloth, Discard, and the Sollumz status. |
| Settings | Connection, Account, Models (Automatic Push Delay), Updates, Privacy and About (closed by default). The add-on preferences show the same groups. |

The small **?** buttons explain a step or option: hover for the tooltip, or click for a popup. A greyed-out button
says why it is unavailable, in the line below it and in its tooltip.

## First connection

1. Start Durty Cloth Tool. The add-on finds it by itself (you can turn this off with Connect Automatically in
   Settings); otherwise click **Connect**.
2. **Sign In with gta.clothing.** When Blender is not signed in yet, the add-on asks Durty Cloth Tool to approve
   the sign-in: approve the request in Durty Cloth Tool (**Approve in Durty Cloth Tool** asks again). Or click
   **Sign In in the Browser** and approve it on gta.clothing after checking that the page shows the same code
   (**Copy Code** copies it).

There is nothing else to set up: Durty Cloth Tool accepts Blender once both are signed in with the same account,
and lists it on its Connected apps page (Options > Connected apps), where you can disconnect it. After a
disconnect there the add-on does not connect again until you click **Connect** (or start Blender again with
Connect Automatically on).

The sign-in is kept, so you normally do this once. It ends when you sign out, when you end the session on
gta.clothing, or after 30 days without use. After you sign out, the add-on does not start a new sign-in by
itself until you choose one of the sign-in buttons.

## Live Preview

1. Select the cloth and texture variation in Durty Cloth Tool. The Linked Cloth panel shows them.
2. Choose the map under Linked Cloth: Diffuse (Colour), Normal or Specular.
3. In Live Preview, pick the image (the eyedropper picks the image you are painting on) and click **Start Live
   Preview**. A progress bar shows while a large image is read for the first time.
4. Paint. The add-on reads the image when a paint stroke ends, so painting stays smooth, and Durty Cloth Tool
   shows the change a moment later. Changes made without painting (scripts, baking, reloading) are found when the
   add-on next checks the image, which it does less often the longer nothing changes; **Send Now** sends them at
   once. **Pause** stops sending until you click **Resume**. If your Blender cannot tell add-ons that a stroke is
   running (Blender 4.2 to 4.4 are not tested), the add-on says so once in Blender's system console and reads the
   image less often while it changes.
5. **Save to Cloth** replaces the map in the project; **Save as New Variation** adds the image as a new texture
   variation (Diffuse (Colour) only, because normal and specular maps belong to the model). **Discard Changes**
   drops your changes from the preview. A saved map can be undone in the cloth's History in Durty Cloth Tool.
   **Stop Live Preview** ends the preview without saving; your changes stay in the Blender image, so you can
   start again and save them.

Images can be up to 4096 by 4096 pixels. Colours:

- For the diffuse texture use an sRGB image, the default for painting. Linear images (32-bit float images, or
  8-bit images set to a linear colour space) are converted to sRGB. Painted colour with partial transparency is
  sent with its true colour: Blender keeps float images with the alpha mode Straight or Premultiplied
  premultiplied by alpha, and the add-on divides that out. Channel Packed and None images, and Non-Color
  images, are sent as Blender holds them.
- Normal and specular maps should be set to **Non-Color**; their values are sent as they are. The panel warns
  when an image's colour space means its values would arrive changed.
- Everything arrives as 8 bits per channel. For exact colours, paint on 8-bit images.

## Model

1. Select your Sollumz Drawable Dictionary, or any object inside it. Durty Cloth Tool takes drawable
   dictionaries; if your Drawable is not in one, use Sollumz's Create Drawable Dictionary and parent it.
2. Select the cloth in Durty Cloth Tool whose model you want to replace in the preview.
3. In the Model panel, click **Push Model**. The add-on exports the model with Sollumz as CodeWalker XML (YDD XML,
   GTA V Legacy) together with its embedded `.dds` textures into a temporary folder, sends the files to Durty
   Cloth Tool and deletes the folder. Your other Sollumz export settings, such as Exclude Skeleton, are used as
   you set them. A hidden Drawable Dictionary is exported through a visible object inside it.
4. **Save Model to Cloth** saves the model in the project (Durty Cloth Tool keeps the previous model in History);
   **Discard** drops it from the preview. Save Model to Cloth waits until Durty Cloth Tool shows your newest push,
   so it never saves an older version; if Durty Cloth Tool is still loading the model, the add-on asks again a few
   times before it tells you to try later.

With **Push Automatically** on, the add-on pushes the model again once it has stayed unchanged for a moment
(1.5 seconds by default; change it with Automatic Push Delay under Settings > Models). It waits while you are in
Edit Mode or another mode, and while a tool is running (for example a transform); the panel says what it waits
for. The push uses the scene and window that show the model. When Sollumz logs warnings during an automatic push,
automatic pushes pause until you push by hand; Sollumz's Info log has the details.

Texture and model file names may only use letters, digits, `_`, `-` and `.`, and textures need different names.
At most 255 textures and 64 MiB per model can be sent. GLB models are not pushed; add them in Durty Cloth Tool
with Add clothing instead.

## What the add-on sends, and where

### To Durty Cloth Tool, on this computer

The add-on talks to Durty Cloth Tool over a WebSocket on `127.0.0.1`, ports 47820 to 47829. An installed Durty
Cloth Tool names its port in the file `CreatorLink\endpoint.json` in its user data folder; a portable one is
found by trying the ports. When that file exists, the add-on sends sign-in data only to the Durty Cloth Tool it
names, running in your Windows session; anything else that answers gets nothing, and the add-on keeps looking.
This connection never leaves your computer. Messages the add-on sends:

| Message | When | Contents |
|---|---|---|
| `hello` | every connection | link protocol version, add-on version and channel, "Blender" and the Blender version, the random installation id (the one gta.clothing sees with your sign-in), and a random number for this connection |
| `account.assist` | signing in through Durty Cloth Tool | the sign-in code, so Durty Cloth Tool can approve it |
| `auth` | every connection | a short-lived sign-in assertion for this connection (never your gta.clothing tokens) |
| `context.get` | after connecting | asks for the open project and the selected cloth |
| `live.open` | Start Live Preview | the map (diffuse, normal or specular), the image size and the image name |
| `live.frame` | during the live preview | the changed parts of the image as pixels |
| `live.save` | Save to Cloth, Save as New Variation | which save to make |
| `live.discard`, `live.close` | Discard Changes, Stop Live Preview | which live preview to drop or close |
| `texture.validate` | when the live preview starts, Check Again | the map and the image size |
| `model.push` | Push Model | the `.ydd.xml` and `.dds` files with their names |
| `model.save`, `model.discard` | Save Model to Cloth, Discard | which pushed model to save or drop |
| `bye` | disconnecting | nothing |

Durty Cloth Tool answers with the matching results and tells the add-on when the project, the selected cloth or
your plan changes, and when a live preview or pushed model is closed on its side.

### To gta.clothing

The add-on itself calls only these public routes of `https://gta.clothing`. They run in the background, so
Blender does not wait for them.

| Route | When | What is sent |
|---|---|---|
| `POST /link/api/auth/device` | starting a sign-in | the client id `dct-link-blender`, the add-on version, the Blender version, the link protocol version, the channel, a random installation id, and the computer name (unless you turn off Show This Computer's Name When Signing In) |
| `POST /link/api/auth/token` | while a sign-in waits for approval, and when connecting with a sign-in older than 15 minutes (to renew it) | the sign-in's device code, or the renewal token |
| `POST /link/api/assertions` | every connection to Durty Cloth Tool | your sign-in (as `Authorization: Bearer`) and the random number Durty Cloth Tool chose for this connection |
| `POST /link/api/auth/logout` | Sign Out, when online access is allowed | the renewal token, to end the session |

Every request carries the header `X-DCT-Link-Client: blender/<add-on version> (protocol 1.0; channel <channel>)`
(also used as the User-Agent). The add-on opens these pages in your browser when you ask it to: the sign-in
approval page `https://gta.clothing/account/link/`, the plugins page `https://gta.clothing/account/plugins/`, the
documentation `https://docs.gta.clothing/`, the Pleb Masters Community Discord server, and its invitation
`https://discord.plebmasters.de` when a sign-in needs the Discord membership.

Blender, not the add-on, downloads the repository listing `https://gta.clothing/link/blender/<channel>/index.json`
and the add-on archive it names.

### What leaves your computer

Your pixels and models go only to Durty Cloth Tool on this computer. gta.clothing sees your sign-in and its
renewals, a sign-in assertion request each time Blender connects to Durty Cloth Tool, your sign-out, and
Blender's update checks. Nothing else is sent anywhere, and the add-on does not collect usage data. **Copy
Diagnostics** copies versions and status codes to the clipboard for support; it contains no file paths, names or
sign-in data.

## Where things are stored

- **Sign-in:** in the add-on's user folder, which Blender keeps across updates of the same
  installation: `%APPDATA%\Blender Foundation\Blender\<version>\extensions\.user\<repository>\durty_cloth_tool_link\`.
  - `tokens.dpapi`: your gta.clothing sign-in, encrypted with Windows DPAPI for your Windows user account. It
    holds the access token, the renewal token, your account id, name and avatar link, the session id and your
    plan. After you sign out it only records that you signed out.
  - `install-id`: a random id for this installation (not a secret).
  - `auth.lock`: an empty file that keeps two Blender windows from renewing the sign-in at the same time.
- **Exported models:** in a temporary folder named `dct_link_...`, deleted right after each push.

## Signing out and disconnecting

- **Sign out:** Settings > Account > **Sign Out** (in the DCT tab or the add-on preferences). This deletes the
  stored sign-in, disconnects, and, when online access is allowed, ends the session on gta.clothing. When online
  access is off, or gta.clothing cannot be reached, the add-on says that you are signed out on this computer
  only; the session on gta.clothing then ends by itself after 30 days, or end it on your account page, which
  lists signed-in plugins.
- **Disconnect:** click the status in the DCT tab, then **Disconnect**. Durty Cloth Tool can also disconnect
  Blender on its Connected apps page (Options > Connected apps); the add-on then waits until you click
  **Connect**.
- **Stop updates:** remove the Durty Cloth Tool repository in Blender's Get Extensions settings.

Uninstalling the add-on deletes its user folder (seen with Blender 4.5 and 5.2), which removes the sign-in from
this computer. It does not end the session on gta.clothing, so sign out first.

## Troubleshooting

- **Durty Cloth Tool not found:** make sure it is running and connected apps are allowed (Options > Connected
  apps).
- **Disconnected in Durty Cloth Tool:** click **Connect** in the DCT tab.
- **Durty Cloth Tool is signed out:** sign in there, then click **Connect**. The add-on also tries again by
  itself, waiting longer each time (up to about five minutes).
- **Another account:** Blender and Durty Cloth Tool must be signed in with the same account. Sign out in Blender
  and sign in again.
- **Discord membership:** the sign-in needs your Discord account to be a member of the Pleb Masters Community
  Discord server; the add-on offers **Join the Discord Server**.
- **Online access is off:** signing in and connecting both need it; allow it in Edit > Preferences > System >
  Network.
- **A button is greyed out:** the line below it says why and what makes it available (so does its tooltip).
- **Support:** Settings > About > **Copy Diagnostics**, then paste it in the Pleb Masters Community Discord server.

## Development

```
durty_cloth_tool_link/   the extension (blender_manifest.toml, the add-on modules, translations, the logo, vendored dct_link)
tests/                   pytest tests (no Blender needed) and the Blender smoke test
tools/                   dct_link sync, manifest check, release checks and the Blender smoke runner
```

- **Tests** (Python 3.11 or later): `python -m pip install -r requirements-dev.txt numpy`, then `python -m pytest`.
  They cover pixel conversion and the vertical flip, colour handling, dirty rectangles, capture scheduling,
  collecting Sollumz exports, settings, the nine languages, the manifest, the vendored copy, and the whole link
  flow against a fake Durty Cloth Tool and a fake gta.clothing on `127.0.0.1`.
- **Texts:** every text the add-on shows is in `durty_cloth_tool_link/strings.py` (English) and
  `durty_cloth_tool_link/translations/` (one module per language, Blender locale names). Add a key in all nine
  languages at once; the tests fail when one is missing or its `{fields}` differ.
- **Blender smoke:** `python tools/blender_smoke.py --blender <path to blender>` validates and builds the
  extension into `dist/` and runs `tests/blender/smoke_in_blender.py` in a background Blender with a throw-away
  user folder. Add `--sollumz <Sollumz extension folder> --sollumz-site <folder with its szio package>` to also
  push through a real Sollumz.
- **Build by hand:** `blender --command extension build --source-dir durty_cloth_tool_link --output-dir dist`.
- **Release:** set the new version in `blender_manifest.toml` and `VERSION` in `settings.py` (`X.Y.Z`, or
  `X.Y.Z-experimental.N` with N from 1 for an Experimental release), then push the tag `v<version>` from the
  default branch. `.github/workflows/release.yml` runs the tests, builds and validates the archive with the
  pinned official Blender 4.5.9, gives every file the commit time so the archive can be rebuilt byte for byte,
  and publishes `durty_cloth_tool_link-<version>.zip` with its size and SHA-256 as the release `v<version>`
  (a pre-release for Experimental). A tag that differs from the manifest version is refused, and an existing
  release is never replaced: Durty Cloth Tool pins the archive by its SHA-256, so a fix is a new version.
  Blender offers any listed version that differs from the installed one as an update, without comparing
  versions, so switching from Experimental to Release can move to a lower version number.
- **Manifest check without Blender:** `python tools/check_manifest.py`.
- **dct_link** is vendored from the Durty Cloth Tool repository: only the modules the add-on uses, each copied
  unchanged. Never edit `durty_cloth_tool_link/dct_link` by hand; update it with
  `python tools/sync_dct_link.py <Durty Cloth Tool checkout>` and check it with
  `python tools/sync_dct_link.py --check`.

## Licence

Copyright (c) 2026 Schmid Software Solutions (https://schmid-software.de). Maintained by DurtyFree (Pleb
Masters).

The add-on is free software under the GNU General Public License, version 3 or (at your option) any later
version (`GPL-3.0-or-later`, see [LICENSE](LICENSE)). The vendored `dct_link` package in
`durty_cloth_tool_link/dct_link` is MIT licensed (see its `LICENSE`).

The Durty Cloth Tool logo (`durty_cloth_tool_link/icons/dct-mark.png`) is not covered by the GPL or the MIT
licence. It is a mark of Schmid Software Solutions, included only to identify Durty Cloth Tool in the add-on's
interface, and it may not be modified or used for any other purpose (see [NOTICE](NOTICE), which the add-on
also ships). Durty Cloth Tool itself and gta.clothing are separate products and are not covered by these
licences.
