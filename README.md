# Durty Cloth Tool Link for Blender

A Blender add-on that connects Blender to [Durty Cloth Tool](https://docs.gta.clothing) running on the same
computer, so you see your work on the freemode ped in Durty Cloth Tool's 3D preview while you work:

- **Live Preview.** Paint a texture in Blender and see it on the linked cloth after each paint stroke. Choose the
  map it replaces: Diffuse (Colour), Normal or Specular. When you like the result, save it to the cloth or as a
  new variation, or discard the changes.
- **Model.** Push a Sollumz Drawable Dictionary straight into Durty Cloth Tool's preview, replacing the linked
  cloth's model until you save or discard it. Turn on Push Automatically to send the model again a moment after
  each change.
- **Edit from Durty Cloth Tool.** Choose Edit in connected app in Durty Cloth Tool: a texture map opens in Blender
  as an image linked to its cloth with the live preview running, and a model opens through Sollumz, linked to its
  cloth and pushed again after each change.
- **Linked Cloth.** The panel shows the open project and the cloth with its picture, variation, drawable type,
  gender, collection and number, and opens the cloth's diffuse, normal or specular map in Blender.
- **Texture Checks.** Durty Cloth Tool checks the image against what GTA V and the cloth need, before you save.
- **Garment Fitting (Experimental).** Bring a garment from Marvelous Designer (or any FBX, OBJ or glTF) towards a
  game-ready freemode cloth: markers, fit checks against the freemode body, fixes by region or by hand, and the
  game-ready steps (seams, one texture, levels of detail, checks). See
  [Garment fitting (experimental)](#garment-fitting-experimental).

Nothing is saved in your project until you choose to save, and every save can be undone in the cloth's History in
Durty Cloth Tool. The add-on speaks Blender's interface language: English, German, French, Russian, Spanish,
Brazilian Portuguese, Simplified Chinese, Hindi and Arabic. It is open source under the GPL (see
[Licence](#licence)).

## Requirements

- Blender 4.2 or later on Windows (x64). Tested with Blender 4.5 LTS and 5.2 LTS; 4.2 to 4.4 are expected to
  work but are not tested.
- Durty Cloth Tool running on the same computer, with connected apps allowed (Options > Connected apps), in a
  version that speaks Creator Link protocol 2. With an older Durty Cloth Tool the DCT tab says to update it.
- A Durty Cloth Tool account (you sign in with Discord on gta.clothing). Blender and Durty Cloth Tool must use
  the same account. Some features are included in a Durty Cloth Tool plan; the panels say when yours does not
  include one.
- [Sollumz](https://docs.sollumz.org) 2.8.0 or later for opening and pushing models and for Generate LODs (tested with
  Sollumz 2.9.0). Textures and the other garment fitting tools work without it.
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
| Durty Cloth Tool | The connection status in one word (Connected, Live, Connecting, Action Needed, Offline, Problem). Click it for the connection details, Connect or Disconnect. The **?** menu in the panel header holds Help, the Pleb Masters Community Discord, Copy Diagnostics and About. |
| Get Connected | Only while setup is incomplete: the setup steps, one at a time. The panels below appear once Durty Cloth Tool is found and you are signed in. |
| Linked Cloth | The project and the cloth: the one selected in Durty Cloth Tool, or the one the chosen image is linked to, with its picture, variation and details, and buttons that open its maps in Blender. |
| Live Preview | The image and the map it replaces; start, pause and stop the live preview; Save to Cloth, Save as New Variation, Discard Changes; while it runs, the Texture Checks with Durty Cloth Tool's findings for the image. |
| Model | Push Model, Push Automatically, Save Model to Cloth, Discard, and the Sollumz status. |
| Garment Fitting (Experimental) | The next step in one line, and the panels Setup, Fit, Fix and Game Ready (all but Setup closed by default). See [Garment fitting (experimental)](#garment-fitting-experimental). |
| Settings | Connection, Account, Models (Automatic Push Delay), Updates and Privacy (closed by default). The add-on preferences show the same groups. |

The small **?** buttons explain a step or option: hover for the tooltip, or click for a popup. A greyed-out button
says why it is unavailable, in the line below it and in its tooltip.

## First connection

1. Start Durty Cloth Tool. The add-on finds it by itself (you can turn this off with Connect Automatically in
   Settings); otherwise click **Connect**.
2. **Sign In with gta.clothing.** Click **Sign In**: Durty Cloth Tool shows the sign-in request with a code, and
   you approve it there. When Durty Cloth Tool is not running, the add-on shows the code for your browser instead
   after a few seconds (**Open Sign-in Page**, **Copy Code**); approve it on gta.clothing after checking that the
   page shows the same code. **Sign In in the Browser** goes to that page straight away.

There is nothing else to set up: Durty Cloth Tool accepts Blender once both are signed in with the same account,
and lists it on its Connected apps page (Options > Connected apps), where you can disconnect it. After a
disconnect there the add-on does not connect again until you click **Connect** (or start Blender again with
Connect Automatically on).

The sign-in is kept, so you normally do this once. It ends when you sign out, when you end the session on
gta.clothing, or after 30 days without use. After you sign out, the add-on does not start a new sign-in by
itself until you choose one of the sign-in buttons.

## Live Preview

1. Select the cloth and texture variation in Durty Cloth Tool. The Linked Cloth panel shows them.
2. In Live Preview, pick the image (the eyedropper picks the image you are painting on) and the map it replaces:
   Diffuse (Colour), Normal or Specular.
3. Click **Start Live Preview**. A progress bar shows while a large image is read for the first time.
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

To start from the cloth's own texture instead, use the map buttons under Linked Cloth (**Open a Map in Blender**),
or Edit in connected app in Durty Cloth Tool (see below).

Images can be up to 4096 by 4096 pixels. Colours:

- For the diffuse texture use an sRGB image, the default for painting. Linear images (32-bit float images, or
  8-bit images set to a linear colour space) are converted to sRGB. Painted colour with partial transparency is
  sent with its true colour: Blender keeps float images with the alpha mode Straight or Premultiplied
  premultiplied by alpha, and the add-on divides that out. Channel Packed and None images, and Non-Color
  images, are sent as Blender holds them.
- Normal and specular maps should be set to **Non-Color**; their values are sent as they are. The panel warns
  when an image's colour space means its values would arrive changed.
- Everything arrives as 8 bits per channel. For exact colours, paint on 8-bit images.

## Edit from Durty Cloth Tool

In Durty Cloth Tool, choose **Edit in connected app** for a cloth or a texture variation and pick Blender. Blender
must be running with the add-on connected; Durty Cloth Tool puts the cloth on the ped and sends it.

- **A texture map** (diffuse, normal or specular) opens as an image named after the cloth, variation and map, for
  example `jbib_003_u A Normal`, and its live preview starts at once. Normal and specular maps are set to
  Non-Color. The image remembers its cloth and map (also in the saved .blend file), so its live preview always goes
  to that cloth, whatever is selected in Durty Cloth Tool; **Unlink** under Linked Cloth lets it follow the
  selection again. Opening the same map again reuses the image only while its pixels are still exactly what was
  opened into it; otherwise a new image is made, so paint, a saved or repacked file and an appended image are never
  overwritten. The image is packed into the .blend file. While a live preview runs or saves, Durty Cloth Tool is
  told that Blender is busy: stop it first.
- **A model** opens with Sollumz: the add-on writes the `.ydd.xml` and its `.dds` textures into a folder of its
  own for this open in its user folder (the textures in a folder named after the model, where Sollumz looks for
  them), imports them with Sollumz's import (your Sollumz import settings, with textures packed into the .blend
  file), selects the new Drawable Dictionary, links it to its cloth and turns on Push Automatically. Its first push
  names the cloth; later pushes update that preview. A model of another cloth that was on the ped before is taken
  off first. Save Model to Cloth and Discard work as for any pushed model. When Sollumz reports errors while
  importing, the model is not linked and the Model panel says so; warnings are shown with the model. Without
  Sollumz (or with one that is too old), Durty Cloth Tool is told what is missing and the Model panel says what
  to install.
- **The link of a model** shows in the Model panel ("Linked to jbib_003_u A") with **Unlink**. Opening the same
  cloth's model again moves the link to the new one. A copy made with Duplicate carries the link too: the Model
  panel says so, and the copy is not pushed until one of the two is unlinked.

The panels say what happened ("Opened from Durty Cloth Tool: ..."); a problem after Blender took the item is shown
there too.

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

## Garment fitting (experimental)

Garment Fitting (Experimental) in the DCT tab takes a garment made elsewhere, for example in Marvelous Designer,
and works it towards a cloth the game can wear. Its first line always says what to do next. In this version every
tool runs in Blender on your computer; only the freemode body is downloaded (see below). Fitting the garment to the
GTA pose, giving it weights and adding it to a Durty Cloth Tool project come in a later version and will use
gta.clothing, with a daily limit for each account.

The tools change only the garment chosen under Setup, the markers and the body they added. Every step that changes
the garment can be undone with Ctrl+Z, and the garment keeps up to three backups of its mesh in the .blend file (the
shape before the first fitting step and the newest ones) for **Restore Pre-fit**.

**Setup**

- **Gender, Slot, Category, Source Pose.** Male or Female; the slot (Top `jbib`, Undershirt `accs`, Legs `lowr`,
  Shoes `feet`) and its categories (Vest, T-shirt, Long Sleeve, Long Jacket or Tunic, Pants, Shorts, Shoes); and the
  pose the garment was made in (A-pose, T-pose or Custom).
- **Import Garment** reads FBX, OBJ, GLB and glTF files, converts centimetres and millimetres to metres and joins
  the parts into one object. **Avatar Stood on the Ground** (on by default) moves a garment made on an avatar
  standing at height 0, as in Marvelous Designer, down to the ped. **Use Selected Garment** works on a mesh that is
  already in the scene.
- **Add Freemode Body** downloads the freemode body of the chosen gender from gta.clothing for your signed-in
  account and adds it as its own object. Each body version is downloaded once and kept in the add-on's user folder,
  so it also works offline afterwards. **Use a Body File** adds a body from a GLB, glTF, FBX or OBJ file instead (in
  metres and in the game's pose). The hosted body is compressed in a way that Blender 5.2 reads; older Blender
  versions get an uncompressed copy when gta.clothing offers one, otherwise use a body file.

**Fit**

- **Auto Markers** places eleven joint markers (neck, chest, pelvis, shoulders, elbows, wrists, hips; for trousers
  the pelvis and hips) on the garment. Move any marker that is off. **Mirror L to R** copies the ped's left side to
  its right. **Save Pose Preset** and **Load Pose Preset** keep marker layouts in the add-on's user folder for similar
  garments. **Marker Size** changes how large they are drawn.
- **T-pose to A-pose** lowers the arms of a garment made in T-pose to the **Arm Angle**, using the markers; the
  markers follow.
- **Restore Pre-fit** puts back the shape from before the first fitting step.

**Fix**

- **Push Out of Body** moves everything inside the body, or closer than the gap, to the gap outside it.
- **Snug to Body** brings a region (Shoulders, Upper Arms, Chest, Back, Waist, Hips, Neck, Legs) closer to the
  body, down to its gap, by the amount you choose. **Relax Stretched** eases stretched parts of a region back towards
  their original size.
- **Show Problems** colours the garment: red inside the body, yellow too close, purple stretched, blue a floating
  shoulder. The refresh button colours it again after a change; selecting Show Problems again removes the colours.
- **Run Fit Check** measures how far each region stands off the body, in millimetres (the middle value and the
  range of most of its vertices). The usual range of game clothing for each region comes with the fitting service.
- **Start Sculpting** opens Sculpt Mode with the Grab brush (radius, strength, Mirror X), the body shown as a
  wireframe. **Accept** keeps the shape and reports how many vertices moved and how many are inside the body before
  and after; with **Keep Out of Body** on, what you pushed into the body goes back out along your stroke. **Cancel**
  puts back the shape from before the session.
- **Check Tears** poses the garment's armature through a few test poses (arms up, arms forward, legs forward, a
  twist) and reports where seams between panels open; the vertices go into the vertex group `DCT Tears`. It needs an
  armature and weights on the garment, which come with the fit.

**Game Ready**

- **Prepare Garment** joins the seams between panels within the **Weld Distance** (never a lining onto its shell),
  removes loose parts, triangulates, shades smooth and adds the ped shader's vertex colours as Sollumz names them:
  `Color 1` #FF8000 (the light the garment receives; #FFBAFF lets emissive materials glow) and `Color 2` black
  without alpha (no vertex wind, no sweat), as Sollumz's clothing tutorial recommends for most clothing. Both values
  can be changed, and existing ones are kept unless you choose to replace them.
- **Combine Materials** packs all UV islands into one layout (long thin strips such as hems are cut into pieces
  first, so the rest gets more of the texture) and bakes the colour of every material into one 2048 or 4096 pixel
  texture, which becomes the garment's only material. The new layout is `UVMap 0`; the original one is kept as
  `DCT Source UV`. Transparency is not baked.
- **Generate LODs** fills Sollumz's Medium and Low LOD slots with copies decimated to the triangle budgets you set;
  their weights come from the High level. It needs Sollumz.
- **Validate** checks weights (unweighted vertices, more than four bones per vertex), broken coordinates, the UV
  layout, the vertex colours, the vertices of each level of detail against what game clothing usually has, and how
  much of the garment is inside the body. It says CLEAN, or lists what to look at.

What the garment tools keep: the backups as meshes with a fake user, the latest fit check and validation, and a few
markers of progress as custom properties of the garment (`dct_garment`, `dct_fit_backups`, `dct_fit_report`,
`dct_findings`, `dct_prepared` and similar); the markers as empties in the collection `DCT Garment Markers`; the
body in `DCT Freemode Body`; the problem colours as the colour attribute `DCT Problems`; and, during a sculpt
session, the shape it started from as the attribute `dct_presculpt`.

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
| `account.assist` | Sign In | the sign-in code, so Durty Cloth Tool can approve it |
| `auth` | every connection | a short-lived sign-in assertion for this connection (never your gta.clothing tokens) |
| `context.get` | after connecting | asks for the open project and the selected cloth |
| `live.open` | Start Live Preview, an opened map | the map (diffuse, normal or specular), the image size and the image name, and for an image linked to its cloth the ids of that cloth and variation |
| `live.frame` | during the live preview | the changed parts of the image as pixels |
| `live.save` | Save to Cloth, Save as New Variation | which save to make |
| `live.discard`, `live.close` | Discard Changes, Stop Live Preview | which live preview to drop or close |
| `texture.validate` | when the live preview starts, Check Again | the map and the image size |
| `texture.read` | the map buttons under Linked Cloth | which map of which cloth to send |
| `item.thumbnail` | when the Linked Cloth panel shows another cloth | the cloth and the picture size |
| `host.result` | when Durty Cloth Tool sent a texture or model | whether Blender opened it, or why not |
| `model.push` | Push Model, an opened model | the `.ydd.xml` and `.dds` files with their names; the first push of an opened model also the ids of its cloth |
| `model.save`, `model.discard` | Save Model to Cloth, Discard | which pushed model to save or drop |
| `bye` | disconnecting | nothing |

Durty Cloth Tool answers with the matching results and tells the add-on when the project, the selected cloth or
your plan changes, and when a live preview or pushed model is closed on its side. It sends the textures and models
you choose Edit in connected app for.

### To gta.clothing

The add-on itself calls only these public routes of `https://gta.clothing`. They run in the background, so
Blender does not wait for them.

| Route | When | What is sent |
|---|---|---|
| `POST /link/api/auth/device` | starting a sign-in | the client id `dct-link-blender`, the add-on version, the Blender version, the link protocol version, the channel, a random installation id, and the computer name (unless you turn off Show This Computer's Name When Signing In) |
| `POST /link/api/auth/token` | while a sign-in waits for approval, and when connecting with a sign-in older than 15 minutes (to renew it) | the sign-in's device code, or the renewal token |
| `POST /link/api/assertions` | every connection to Durty Cloth Tool | your sign-in (as `Authorization: Bearer`) and the random number Durty Cloth Tool chose for this connection |
| `POST /link/api/auth/logout` | Sign Out, when online access is allowed | the renewal token, to end the session |

For **Add Freemode Body** (Garment Fitting) the add-on calls gta.clothing's link origin `https://link.gta.clothing`,
as Creator Link's hosted panel does:

| Route | When | What is sent |
|---|---|---|
| `GET /link/manifest/<channel>.json` | Add Freemode Body | nothing (it names the current body version) |
| `POST /link/panel/ticket` | Add Freemode Body, when that body version is not kept yet | your sign-in (as `Authorization: Bearer`), the channel and the current panel version |
| `GET /link/assets/body/<version>/freemode_<gender>.glb` | right after the ticket | the short-lived ticket (as `Authorization: Ticket`) |

Every request carries the header `X-DCT-Link-Client: blender/<add-on version> (protocol 2.0; channel <channel>)`
(also used as the User-Agent). The add-on opens these pages in your browser when you ask it to: the sign-in
approval page `https://gta.clothing/account/link/`, the plugins page `https://gta.clothing/account/plugins/`, the
documentation `https://docs.gta.clothing/`, the Pleb Masters Community Discord server, and its invitation
`https://discord.plebmasters.de` when a sign-in needs the Discord membership.

Blender, not the add-on, downloads the repository listing `https://gta.clothing/link/blender/<channel>/index.json`
and the add-on archive it names.

### What leaves your computer

Your pixels and models go only to Durty Cloth Tool on this computer; the garment fitting tools of this version send
nothing of your garment anywhere. gta.clothing sees your sign-in and its renewals, a sign-in assertion request each
time Blender connects to Durty Cloth Tool, your sign-out, the download of the freemode body (once per body version)
and Blender's update checks. Nothing else is sent anywhere, and the add-on does not collect usage data. **Copy
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
  - `body\<version>\freemode_<gender>.glb`: the freemode body Add Freemode Body downloaded, one folder per body
    version.
  - `garment-presets\<name>.json`: the pose presets you saved (marker positions, category and source pose).
- **Exported models:** in a temporary folder named `dct_link_...`, deleted right after each push.
- **Models opened from Durty Cloth Tool:** in `opened-models` in the add-on's user folder, one folder per open,
  while the model is on the ped. They are deleted when the model is discarded or closed, when the add-on is
  disabled, and (left over from a Blender that closed) when the add-on starts; at start-up only folders the add-on
  made are removed, and nothing when `opened-models` is a link. Blender keeps what it imported, with the textures
  packed.
- **Textures opened from Durty Cloth Tool:** packed into the .blend file, with the ids of the cloth and variation
  and the map as custom properties of the image (`dct_cloth_id`, `dct_texture_id`, `dct_map`, and `dct_pixels`,
  the SHA-256 of the pixels it was opened with). A model opened from Durty Cloth Tool keeps the ids on its Drawable
  Dictionary. Opening and linking each add an undo step, so undo and redo keep the link.

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
- **Durty Cloth Tool is older than the add-on:** update Durty Cloth Tool, then click **Connect**. When the add-on is
  older than Durty Cloth Tool, **Get the Update** opens the plugins page.
- **Busy when sending from Durty Cloth Tool:** a live preview is running or saving in Blender (or a model is being
  pushed). Stop it, then choose Edit in connected app again.
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
- **Support:** the **?** menu in the header of the DCT tab > **Copy Diagnostics**, then paste it in the Pleb
  Masters Community Discord server.

## Development

```
durty_cloth_tool_link/   the extension (blender_manifest.toml, the add-on modules, translations, the logo, vendored dct_link)
tests/                   pytest tests (no Blender needed) and the Blender smoke test
tools/                   dct_link sync, manifest check, release checks and the Blender smoke runner
```

- **Tests** (Python 3.11 or later): `python -m pip install -r requirements-dev.txt numpy`, then `python -m pytest`.
  They cover pixel conversion and the vertical flip, colour handling, dirty rectangles, capture scheduling,
  collecting Sollumz exports, settings, the nine languages, the manifest, the vendored copy, and the whole link
  flow against a fake Durty Cloth Tool and a fake gta.clothing on `127.0.0.1`, including the textures and models
  Durty Cloth Tool sends. The garment fitting tools' arithmetic (markers on synthetic garments, regions, the fit
  check, problem colours, seams, UV strips, validation, presets) and the hosted body download are tested the same
  way (`tests/test_garment.py`, `tests/test_garment_body.py`).
- **Texts:** every text the add-on shows is in `durty_cloth_tool_link/strings.py` (English) and
  `durty_cloth_tool_link/translations/` (one module per language, Blender locale names). Add a key in all nine
  languages at once; the tests fail when one is missing or its `{fields}` differ.
- **Blender smoke:** `python tools/blender_smoke.py --blender <path to blender>` validates and builds the
  extension into `dist/` and runs `tests/blender/smoke_in_blender.py` in a background Blender with a throw-away
  user folder. Add `--sollumz <Sollumz extension folder> --sollumz-site <folder with its szio package>` to also
  push through a real Sollumz (and open a model with its import). The smoke also runs every garment fitting tool on
  a synthetic garment and body (`tests/blender/garment_smoke.py`; no game files are used or needed).
- **Interface screenshots:** `python tools/blender_shots.py --blender <path to blender> --out <folder>` builds the
  extension, opens a Blender window with a throw-away user folder (both tools drop Blender's `BLENDER_USER_*`
  folder variables, so your own profile is never used), walks the DCT tab through its states against
  the fake Durty Cloth Tool and saves a cropped screenshot of the sidebar for each (`--expanded`, `--language
  de_DE` and `--theme light` for variants; `--scenario garment` walks Garment Fitting instead). Blender quits by
  itself.
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
- **dct_link** (the Creator Link client, protocol 2) is developed in the Durty Cloth Tool repository and vendored
  here: only the modules the add-on uses, each copied unchanged. Never edit `durty_cloth_tool_link/dct_link` by
  hand; update it with `python tools/sync_dct_link.py <Durty Cloth Tool checkout>` and check it with
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
