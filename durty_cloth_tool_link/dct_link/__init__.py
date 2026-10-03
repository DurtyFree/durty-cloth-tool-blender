# SPDX-License-Identifier: MIT
# Copyright (c) Schmid Software Solutions (https://schmid-software.de)
"""dct_link: the Creator Link client shared by the Durty Cloth Tool Python host plugins.

Standard library only, Python 3.10 or later. The link client is ``protocol`` (wire format, validation and frame
codecs), ``ws`` (loopback WebSocket client), ``session`` (connecting, sign-in, live textures, models), ``auth``
(gta.clothing sign-in) and ``tokens`` (secret storage); none of them imports anything else from this package.
The full package adds modules for self-updating hosts (signed update manifests and a versioned updater with a
stable loader); a host that vendors only the link client leaves them out.
"""

__version__ = "0.1.0"

from .protocol import ProtocolError  # noqa: E402
from .session import LinkError, LinkSession, LiveSurface, ModelBundle, PluginInfo  # noqa: E402

__all__ = ["__version__", "LinkSession", "LinkError", "LiveSurface", "ModelBundle", "PluginInfo", "ProtocolError"]
