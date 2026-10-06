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
| `fit.py` | `9de5001ce22df3493dfda07eb6f7173b9c72795928519e43a8de9ea3e33097d9` |
| `ped.py` | `68088887c2b99995cd7bb57b2ed787f46e952581a05f78761d4708fccc2292fd` |
| `protocol.py` | `9654ca85440484907417bcfb024f9991ba048d00a9ca25dca1698142a6f1381c` |
| `session.py` | `265e4e8b77af93022775a26a4fc6f9f894ff7ac3f837ca779a8640cceea55a0c` |
| `tokens.py` | `428a1fc987065afcfab7f6e4908f51efdb839ddf134d4d51c91a7a95d95c6cd1` |
| `ws.py` | `3ae992c0ca9c97711d310f0ba001c797b0f75db9d59decace7017b7787823b05` |
