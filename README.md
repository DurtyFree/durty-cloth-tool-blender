# Durty Cloth Tool Link for Blender

A Blender add-on that connects Blender to [Durty Cloth Tool](https://docs.gta.clothing) running on the same
computer, so you can see your work on the freemode ped in Durty Cloth Tool's 3D preview while you work:

- **Texture streaming.** Paint a texture in Blender and see it on the cloth selected in Durty Cloth Tool after
  each paint stroke. Choose whether it replaces the diffuse, normal or specular texture. When you like the
  result, save it to the cloth or as a new texture variation, or discard it.
- **Model push.** Export a Sollumz Drawable Dictionary straight into Durty Cloth Tool's preview, replacing the
  selected cloth's model until you save or discard it. Turn on Push Automatically to send the model again
  shortly after each change.
- **What is selected in Durty Cloth Tool.** The panel shows the open project, the selected cloth and its
  selected texture.

Nothing is saved in your project until you choose Save. The add-on is open source under the GPL (see
[Licence](#licence)).

## Requirements

- Blender 4.2 or later on Windows (x64). Tested with Blender 4.5 LTS and 5.2 LTS; 4.2 to 4.4 are expected to
  work but are not tested.
- Durty Cloth Tool running on the same computer, with Creator Link turned on in its options.
- A Durty Cloth Tool account (you sign in with Discord on gta.clothing). Blender and Durty Cloth Tool must use
  the same account. Some features need a Durty Cloth Tool plan that includes them; the panels tell you when
  yours does not.
- [Sollumz](https://docs.sollumz.org) for pushing models (tested with Sollumz 2.9).
- Blender's **Allow Online Access** (Edit > Preferences > System > Network). The connection to Durty Cloth Tool
  stays on your computer, but each connection is confirmed with your gta.clothing sign-in, so without online
  access the add-on can neither sign in nor connect. The DCT panel says so while it is off.

## Install

Install the add-on from the Durty Cloth Tool extension repository, so Blender can keep it up to date. A guide on
`https://docs.gta.clothing/creator-link/blender` (the add-on's website link) is being written; until it is
published, this README is the guide.

1. On gta.clothing, open the [plugins page of your account](https://gta.clothing/account/plugins/), choose the
   Release or Experimental channel and create a **Blender repository token**. The token is shown once; keep it
   until you have pasted it into Blender.
2. In Blender, open Edit > Preferences > Get Extensions, open the Repositories menu, click **+** and choose
   **Add Remote Repository**. Use this URL (or `experimental` instead of `release`):

   `https://gta.clothing/link/blender/release/index.json`

   Turn on **Requires Access Token** and paste the token as **Secret**.
3. Find **Durty Cloth Tool Link** in Get Extensions and install it.

A copy installed from a downloaded archive (Install from Disk) works, but Blender cannot update it. The add-on
preferences say so. To switch to updates, add the repository (the **Add Update Repository** button in the
add-on preferences does it with your token), uninstall the copy from the archive, and install the add-on from
the repository. Blender keeps the sign-in and the pairing per installation, so you pair and sign in again
after switching.

### Updates and channels

Blender checks the repository for updates like any other extension repository (Get Extensions > Check for
Updates). The add-on tells Durty Cloth Tool and gta.clothing which channel the installed version belongs to.
The Update Channel setting in the add-on preferences decides which repository **Add Update Repository** adds;
when a Durty Cloth Tool repository already exists, the button switches it to the chosen channel and token.
Moving from Experimental back to Release keeps the newer Experimental version until Release catches up; to go
back at once, uninstall the add-on and install it again from the Release repository.

You can revoke a repository token on the plugins page at any time. Blender then stops getting updates until
you add a new token.

## First connection

1. Start Durty Cloth Tool and turn on Creator Link in its options.
2. In Blender, open the 3D View sidebar (N) and the **DCT** tab. The add-on looks for Durty Cloth Tool by itself
   (you can turn this off with Connect Automatically in the preferences); otherwise click **Connect**.
3. **Pair.** In Durty Cloth Tool, click **Connect an app** (Options > Creator Link). For the next two minutes,
   Durty Cloth Tool answers a pairing request with a six-digit code. Click **Request Code** in Blender, type
   the code Durty Cloth Tool shows and click **Pair**. You pair once per Blender installation. If Durty Cloth
   Tool forgets this Blender (for example after you removed it there), the panel asks before pairing again.
4. **Sign in.** If Blender is not signed in yet, the add-on starts a sign-in and asks Durty Cloth Tool to
   approve it with the account Durty Cloth Tool uses. Approve it there, or click **Open Sign-in Page** and
   approve it in your browser after checking that the page shows the same code. You can also sign in first,
   from the add-on preferences, with **Sign In with Browser**.

The sign-in is kept, so you normally do this once. It ends when you sign out, when you end the session on
gta.clothing, or after 30 days without use. After you sign out, the add-on does not start a new sign-in by
itself until you choose one of the Sign In buttons.

## Texture streaming

1. Select the cloth and texture variation in Durty Cloth Tool.
2. In the DCT tab, under Texture Streaming, pick the image (the eyedropper picks the image you are painting
   on), choose Diffuse, Normal or Specular, and click **Start Streaming**.
3. Paint. The add-on reads the image when a paint stroke ends, so painting stays smooth, and Durty Cloth Tool
   shows the change a moment later. Changes made without painting (scripts, baking, reloading) are found when
   the add-on next checks the image, which it does less often the longer nothing changes; **Send Now** sends
   them at once. If your Blender cannot tell add-ons that a stroke is running (Blender 4.2 to 4.4 are not
   tested), the add-on says so once in Blender's system console and reads the image less often while it
   changes.
4. **Save to Cloth** replaces the texture in the project; **Save as New Variation** adds the image as a new
   texture variation (diffuse only). **Discard** drops your changes from the preview.

Images can be up to 4096 by 4096 pixels. Colours:

- For the diffuse texture use an sRGB image, the default for painting. Linear images (32-bit float images, or
  8-bit images set to a linear colour space) are converted to sRGB. Painted colour with partial transparency is
  sent with its true colour: Blender keeps float images with the alpha mode Straight or Premultiplied
  premultiplied by alpha, and the add-on divides that out. Channel Packed and None images, and Non-Color
  images, are sent as Blender holds them.
- Normal and specular maps should be set to **Non-Color**; their values are sent as they are. The panel warns
  when an image's colour space means its values would arrive changed.
- Everything arrives as 8 bits per channel. For exact colours, paint on 8-bit images.

## Model push

1. Select your Sollumz Drawable Dictionary, or any object inside it. Durty Cloth Tool takes drawable
   dictionaries; if your Drawable is not in one, use Sollumz's Create Drawable Dictionary and parent it.
2. Select the cloth in Durty Cloth Tool whose model you want to replace in the preview.
3. In the DCT tab, under Model Push, click **Push Model**. The add-on exports the model with Sollumz as
   CodeWalker XML (YDD XML, GTA V Legacy) together with its embedded `.dds` textures into a temporary folder,
   sends the files to Durty Cloth Tool and deletes the folder. Your other Sollumz export settings, such as
   Exclude Skeleton, are used as you set them. A hidden Drawable Dictionary is exported through a visible object
   inside it.
4. **Save to Cloth** saves the model in the project (Durty Cloth Tool keeps the previous model in History);
   **Discard** drops it from the preview. Save to Cloth waits until Durty Cloth Tool shows your newest push, so
   it never saves an older version; if Durty Cloth Tool is still loading the model, the add-on asks again a
   few times before it tells you to try later.

With **Push Automatically** on, the add-on pushes the model again once it has stayed unchanged for a moment
(1.5 seconds by default, see Automatic Push Delay in the preferences). It waits while you are in Edit Mode or
another mode, and while a tool is running (for example a transform); the panel says what it waits for. The
push uses the scene and window that show the model. When Sollumz logs warnings during an automatic push,
automatic pushes pause until you push by hand; Sollumz's Info log has the details.

Texture and model file names may only use letters, digits, `_`, `-` and `.`, and textures need different names.
At most 255 textures and 64 MiB per model can be sent. GLB models are not pushed; add them in Durty Cloth Tool
with Add clothing instead.

## What the add-on sends, and where

### To Durty Cloth Tool, on this computer

The add-on talks to Durty Cloth Tool over a WebSocket on `127.0.0.1`, ports 47820 to 47829. An installed Durty
Cloth Tool names its port in the file `CreatorLink\endpoint.json` in its user data folder; a portable one is
found by trying the ports. This connection never leaves your computer. Messages the add-on sends:

| Message | When | Contents |
|---|---|---|
| `hello` | every connection | link protocol version, add-on version and channel, "Blender" and the Blender version, a random number for this connection, and the pairing id once paired |
| `pair.request` | pairing | a display name, "Blender on" plus the computer name |
| `pair.complete` | pairing | the six-digit code you typed |
| `account.assist` | signing in through Durty Cloth Tool | a proof of the pairing and the sign-in code, so Durty Cloth Tool can approve it |
| `auth` | every connection | a proof of the pairing and a short-lived sign-in assertion for this connection (never your gta.clothing tokens) |
| `context.get` | after connecting | asks for the open project and the selected cloth |
| `live.open` | Start Streaming | the texture kind (diffuse, normal or specular), the image size and the image name |
| `live.frame` | while streaming | the changed parts of the image as pixels |
| `live.save` | Save to Cloth, Save as New Variation | which save to make |
| `live.discard`, `live.close` | Discard, Stop | which live texture to drop or close |
| `model.push` | Push Model | the `.ydd.xml` and `.dds` files with their names |
| `model.save`, `model.discard` | Save to Cloth, Discard | which pushed model to save or drop |
| `bye` | disconnecting | nothing |

Durty Cloth Tool answers with the matching results and tells the add-on when the project, the selected cloth or
your plan changes, and when a live texture or pushed model is closed on its side.

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
approval page `https://gta.clothing/account/link/` and the plugins page `https://gta.clothing/account/plugins/`.

Blender, not the add-on, downloads the repository listing `https://gta.clothing/link/blender/<channel>/index.json`
and the add-on archive it names, sending your repository token as `Authorization: Bearer`.

### What leaves your computer

Your pixels and models go only to Durty Cloth Tool on this computer. gta.clothing sees your sign-in and its
renewals, a sign-in assertion request each time Blender connects to Durty Cloth Tool, your sign-out, and
Blender's update checks. Nothing else is sent anywhere, and the add-on does not collect usage data.

## Where things are stored

- **Sign-in and pairing:** in the add-on's user folder, which Blender keeps across updates of the same
  installation: `%APPDATA%\Blender Foundation\Blender\<version>\extensions\.user\<repository>\durty_cloth_tool_link\`.
  - `tokens.dpapi`: your gta.clothing sign-in, encrypted with Windows DPAPI for your Windows user account. It
    holds the access token, the renewal token, your account id, name and avatar link, the session id and your
    plan. After you sign out it only records that you signed out.
  - `pairing.dpapi`: the pairing with Durty Cloth Tool (an id and a secret), encrypted the same way.
  - `install-id`: a random id for this installation (not a secret).
  - `auth.lock`: an empty file that keeps two Blender windows from renewing the sign-in at the same time.

  If DPAPI is not available, the secrets are kept in files only your user can read, and a warning is printed
  to Blender's system console.
- **Repository token:** Blender keeps it with the repository in its own preferences.
- **Exported models:** in a temporary folder named `dct_link_...`, deleted right after each push.

## Signing out and removing the pairing

- **Sign out:** Edit > Preferences > Add-ons > Durty Cloth Tool Link > **Sign Out**. This deletes the stored
  sign-in, disconnects, and, when online access is allowed, ends the session on gta.clothing. When online
  access is off, or gta.clothing cannot be reached, the add-on says that you are signed out on this computer
  only; the session on gta.clothing then ends by itself after 30 days, or end it on your account page, which
  lists signed-in plugins.
- **Remove the pairing:** in the same preferences, **Remove Pairing** deletes the pairing in Blender. Also
  remove Blender from the paired apps in Durty Cloth Tool's Creator Link options.
- **Stop updates:** revoke the repository token on the plugins page, or remove the repository in Blender's Get
  Extensions settings.

Uninstalling the add-on deletes its user folder (seen with Blender 4.5 and 5.2), which removes the sign-in and
pairing from this computer. It does not end the session on gta.clothing, so sign out first.

## Troubleshooting

- **Durty Cloth Tool not found:** make sure it is running and Creator Link is turned on in its options.
- **Pairing does not show a code:** click Connect an app in Durty Cloth Tool (Options > Creator Link), then
  click Request Code in Blender within two minutes.
- **Another account:** Blender and Durty Cloth Tool must be signed in with the same account. Sign out in Blender
  and sign in again.
- **Online access is off:** signing in and connecting both need it; allow it in Edit > Preferences > System >
  Network.
- **Save to Cloth is greyed out:** a push is on its way or about to start; Save becomes available once Durty
  Cloth Tool shows it. Hover the button to see why.
- **Push Model is greyed out or refused:** install and enable Sollumz, and select a Drawable Dictionary or an
  object inside one.

## Development

```
durty_cloth_tool_link/   the extension (blender_manifest.toml, the add-on modules, vendored dct_link)
tests/                   pytest tests (no Blender needed) and the Blender smoke test
tools/                   dct_link sync, manifest check and the Blender smoke runner
```

- **Tests** (Python 3.11 or later): `python -m pip install -r requirements-dev.txt numpy`, then `python -m pytest`.
  They cover pixel conversion and the vertical flip, colour handling, dirty rectangles, capture scheduling,
  collecting Sollumz exports, settings, the manifest, the vendored copy, and the whole link flow against a fake
  Durty Cloth Tool and a fake gta.clothing on `127.0.0.1`.
- **Blender smoke:** `python tools/blender_smoke.py --blender <path to blender>` validates and builds the
  extension into `dist/` and runs `tests/blender/smoke_in_blender.py` in a background Blender with a throw-away
  user folder. Add `--sollumz <Sollumz extension folder> --sollumz-site <folder with its szio package>` to also
  push through a real Sollumz.
- **Build by hand:** `blender --command extension build --source-dir durty_cloth_tool_link --output-dir dist`.
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
`durty_cloth_tool_link/dct_link` is MIT licensed (see its `LICENSE`). Durty Cloth Tool itself and gta.clothing
are separate products and are not covered by this licence.
