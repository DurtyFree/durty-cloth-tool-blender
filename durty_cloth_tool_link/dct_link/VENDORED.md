# Vendored dct_link

This folder holds byte-for-byte copies of the `dct_link` modules the add-on uses. `dct_link` is the Creator
Link client. It is developed together with Durty Cloth Tool and synced into this folder with
`tools/sync_dct_link.py`. It is MIT licensed (see `LICENSE` in this folder); every module keeps its SPDX
header. The rest of the add-on is GPL-3.0-or-later.

Do not edit these files by hand. Change dct_link upstream, then run
`python tools/sync_dct_link.py <Durty Cloth Tool checkout>`, which rewrites this folder and this record.
`python tools/sync_dct_link.py --check` and the test suite verify the hashes below.

- Source: the `dct_link` package and its `LICENSE` in the Durty Cloth Tool repository
- dct_link version: 0.1.0
- Creator Link protocol: 2.0
- Synced: 2026-10-06

| File | SHA-256 |
|---|---|
| `LICENSE` | `a2a344cb8f78fc31647efd0e12df7c4f7c7b4b79dab10c2c01418bb229323a75` |
| `__init__.py` | `47759ca6fc3e86a5c81d9441ff12b1e30ab7bae309757576fa8986bd4fadeb96` |
| `auth.py` | `d5039c4a6b13910b3a943b3c2199a14c57dc5c5845d7df8050608872e8722eee` |
| `fit.py` | `d26234e2a69bd1c92fa208611f9b3116e77b796830322204cb4609f262027700` |
| `ped.py` | `1fc7514bc97dc5a432c580327cfca2739d57236999dbe1e65303319ddebd4c64` |
| `protocol.py` | `3b3f154db204e4f66979c9bb1513767022fb223a7ea6a0b8a3b921557831c84d` |
| `session.py` | `b9201fc84808668df7e0308290139d1bb22511da819f10fdb5398e9603e90e36` |
| `tokens.py` | `428a1fc987065afcfab7f6e4908f51efdb839ddf134d4d51c91a7a95d95c6cd1` |
| `ws.py` | `3ae992c0ca9c97711d310f0ba001c797b0f75db9d59decace7017b7787823b05` |
