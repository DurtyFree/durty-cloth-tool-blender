# SPDX-License-Identifier: MIT
# Copyright (c) Schmid Software Solutions (https://schmid-software.de)
"""dct_link: the Creator Link client shared by the Durty Cloth Tool Python host plugins.

Standard library only, Python 3.10 or later. Modules:

* :mod:`dct_link.protocol` wire format, validation and frame codecs
* :mod:`dct_link.ws` loopback WebSocket client (polling or blocking)
* :mod:`dct_link.session` the link session (pairing, sign-in, live textures, models)
* :mod:`dct_link.auth` gta.clothing device sign-in and token refresh
* :mod:`dct_link.tokens` secret storage (DPAPI, Keychain, libsecret, file fallback)
* :mod:`dct_link.es256` and :mod:`dct_link.manifest` signed update manifests
* :mod:`dct_link.updater` and :mod:`dct_link.loader` versioned self-update with rollback
"""

__version__ = "0.1.0"

from .protocol import ProtocolError  # noqa: E402
from .session import LinkError, LinkSession, LiveSurface, ModelBundle, PluginInfo  # noqa: E402

__all__ = ["__version__", "LinkSession", "LinkError", "LiveSurface", "ModelBundle", "PluginInfo", "ProtocolError"]
