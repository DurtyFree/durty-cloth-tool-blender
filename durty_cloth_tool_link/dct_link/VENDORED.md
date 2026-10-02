# Vendored dct_link

This folder holds byte-for-byte copies of the `dct_link` modules the add-on uses. `dct_link` is the Creator
Link client that Durty Cloth Tool shares between its Python host plugins; its self-update modules are left
out because Blender updates the add-on. It is MIT licensed (see `LICENSE` in this folder); every module
keeps its SPDX header. The rest of the add-on is GPL-3.0-or-later.

Do not edit these files by hand. Change dct_link upstream, then run
`python tools/sync_dct_link.py <Durty Cloth Tool checkout>`, which rewrites this folder and this record.
`python tools/sync_dct_link.py --check` and the test suite verify the hashes below.

- Source: `plugins/python/dct_link` and `plugins/python/LICENSE` in the Durty Cloth Tool repository
- dct_link version: 0.1.0
- Source revision: not recorded yet: the sync records the Durty Cloth Tool commit once plugins/python/dct_link is committed there unchanged
- Left out: `es256.py`, `keys.json`, `loader.py`, `manifest.py`, `updater.py`. The package description in
  `__init__.py` still names them, because it describes the whole dct_link package; nothing in the add-on
  imports them.

| File | SHA-256 |
|---|---|
| `LICENSE` | `a2a344cb8f78fc31647efd0e12df7c4f7c7b4b79dab10c2c01418bb229323a75` |
| `__init__.py` | `287bebcc311ea77b8e558aa1000efe5ed48a1620e1920daa85ddc2455351d8ff` |
| `auth.py` | `fa68b8f605b57b43996b416cefb3a316ba8bed9a325dd0f64ca5f30d63529151` |
| `protocol.py` | `ef63a396b479fa5b02aba433fcf559fb3869a803981f0799bd3447cfc697a659` |
| `session.py` | `79b2f82df62cbe9f3044179ee290fd9100049846d510b6be87ac475f58ec4bb2` |
| `tokens.py` | `b8bb93cf0668754e33d676677cad30357d5dc6788d17fe74e6592d55a81a7cd7` |
| `ws.py` | `288e1193a82690eb993a629b29152dd955351154c3eeb4ef3ea6847d4fd4be77` |
