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
- Left out: `es256.py`, `keys.json`, `loader.py`, `manifest.py`, `updater.py` (the modules for self-updating hosts;
  Blender updates the add-on, and nothing in the add-on imports them).

| File | SHA-256 |
|---|---|
| `LICENSE` | `a2a344cb8f78fc31647efd0e12df7c4f7c7b4b79dab10c2c01418bb229323a75` |
| `__init__.py` | `bd7438584ad8ef138caf7cb8a7d773bdcea085729aeb7711642a87e95a696ca9` |
| `auth.py` | `1fc58432729c8cfd8c375ed63f43a13e7844032210f62c7746e5c984cfe604a5` |
| `protocol.py` | `a572e6c8654f5b06c8f850e958aea9227276c14a464bc590dd70cf1bb7cc1cb1` |
| `session.py` | `46c427d4586be5599129837b6e63c4dbecd135eab7e7865fd01106afc425fd85` |
| `tokens.py` | `a8a528af705ea3e342e101d2632da09d801cfde1bc0bae6999d82b90a4749e17` |
| `ws.py` | `288e1193a82690eb993a629b29152dd955351154c3eeb4ef3ea6847d4fd4be77` |
