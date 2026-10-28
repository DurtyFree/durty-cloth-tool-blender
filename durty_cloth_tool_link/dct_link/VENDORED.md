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
- Creator Link protocol: 2.2
- Synced: 2026-10-28

| File | SHA-256 |
|---|---|
| `LICENSE` | `a2a344cb8f78fc31647efd0e12df7c4f7c7b4b79dab10c2c01418bb229323a75` |
| `__init__.py` | `fd27be9fcc223a9578b1fa53b3549ddd8fce75121a61d4aed1f6f98e26ed9592` |
| `auth.py` | `d5039c4a6b13910b3a943b3c2199a14c57dc5c5845d7df8050608872e8722eee` |
| `fit.py` | `6f69f417bb89d96b2f0d880c70335e215c187cadd3c62fd2ccfd1996b71ead9c` |
| `ped.py` | `1fc7514bc97dc5a432c580327cfca2739d57236999dbe1e65303319ddebd4c64` |
| `protocol.py` | `6f45c07b2d3b16cf763dcbdd7e3ae2b14b87bd02059a303cb09b29a128a1ae8d` |
| `session.py` | `a38c93dd327aa4e0c6b9287cc3cbf4060101b1e7212a7e8c76ca0fa95328b491` |
| `tokens.py` | `428a1fc987065afcfab7f6e4908f51efdb839ddf134d4d51c91a7a95d95c6cd1` |
| `ws.py` | `3ae992c0ca9c97711d310f0ba001c797b0f75db9d59decace7017b7787823b05` |
