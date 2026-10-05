# Security policy

Thank you for helping to keep Durty Cloth Tool Link and its users safe.

## 🔒 Reporting a vulnerability

**Please do not report security problems in public issues, pull requests, discussions or Discord channels.**

Report them privately instead:

1. On GitHub, open the **Security** tab of this repository and choose **Report a vulnerability**. Only you and the
   maintainers can see the report.
2. If that option is not available to you, send a direct message to a team member of the
   [Pleb Masters Community Discord](https://discord.plebmasters.de) server and ask for a private way to send a
   security report. Do not put the details into that first message.

Please include:

- the add-on version (**Settings > Updates** in the DCT tab, or **About** in its **?** menu), your Blender version and
  your Windows version;
- what an attacker could do, and under which conditions;
- the steps to reproduce it, ideally with a small example;
- whether you want to be named when the fix is released.

The maintainers confirm that they received your report, keep you informed while they look into it, and release a fix
as a new version of the add-on. Please give us the chance to release that fix before you talk about the problem in
public. There is no bug bounty programme.

## 🎯 Scope

In scope is the code in this repository: the Blender add-on in `durty_cloth_tool_link/`, the vendored `dct_link`
client inside it, the release workflow and the archives it publishes. Examples:

- the add-on sends your images, models, sign-in or other data anywhere other than to Durty Cloth Tool on your own
  computer and to gta.clothing;
- the stored sign-in can be read by someone who should not be able to read it;
- the add-on writes or deletes files outside its own folders, or opens a link that is not a gta.clothing,
  documentation or Discord page;
- another program, a file or a message can make the add-on or Blender do something you did not ask for;
- a published archive does not match the source it was built from.

Out of scope here:

- Durty Cloth Tool itself and gta.clothing. They are separate products and not part of this repository. You can
  still report a problem with them privately in the same way, and we will pass it on.
- Problems in Blender or Sollumz. Please report those to their projects.
- Attacks that need someone who already controls your Windows user account or your computer.
- Versions older than the latest one on each channel (Release and Experimental). Blender updates the add-on, so a fix
  ships as a new version.

## 🤝 Please act in good faith

- Only test with your own accounts, your own computer and your own data.
- Do not try to get into other people's accounts or data, and do not run load or denial-of-service tests against
  gta.clothing.
- Stop and report as soon as you find a problem; do not use it further than needed to show it.
