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
- Synced: 2026-10-05

| File | SHA-256 |
|---|---|
| `LICENSE` | `a2a344cb8f78fc31647efd0e12df7c4f7c7b4b79dab10c2c01418bb229323a75` |
| `__init__.py` | `671a42b49677d378e9bbd3a91c1d270f3dcd0efe629642d2322a78c863f36684` |
| `auth.py` | `d5039c4a6b13910b3a943b3c2199a14c57dc5c5845d7df8050608872e8722eee` |
| `protocol.py` | `d4466cd295a488f7120cb1d7ee8c89ff4cb2492cc3e9fe8709a92bf2dd4c30f9` |
| `session.py` | `a37cc0cfb7226a85c87fae3eaf7ff16e25422fbc8ade1932b0c7244bc1bec36d` |
| `tokens.py` | `428a1fc987065afcfab7f6e4908f51efdb839ddf134d4d51c91a7a95d95c6cd1` |
| `ws.py` | `5c4f5c86b7e630103bef4b4bef30b675d817bff8d337304cdfc513df493d9363` |
