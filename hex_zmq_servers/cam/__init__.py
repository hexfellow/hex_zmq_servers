#!/usr/bin/env python3
# -*- coding:utf-8 -*-
################################################################
# Copyright 2025 Dong Zhaorui. All rights reserved.
# Author: Dong Zhaorui 847235539@qq.com
# Date  : 2025-09-12
################################################################

from .cam_base import HexCamBase, HexCamClientBase, HexCamServerBase
from .dummy import HexCamDummy, HexCamDummyClient, HexCamDummyServer

__all__ = [
    # base
    "HexCamBase",
    "HexCamClientBase",
    "HexCamServerBase",

    # dummy
    "HexCamDummy",
    "HexCamDummyClient",
    "HexCamDummyServer",
]

# Optional: berxel (requires berxel_py_wrapper)
try:
    from .berxel import HexCamBerxel, HexCamBerxelClient, HexCamBerxelServer
    __all__.extend([
        "HexCamBerxel",
        "HexCamBerxelClient",
        "HexCamBerxelServer",
    ])
except ImportError:
    # berxel_py_wrapper not installed
    # Install with: pip install hex_zmq_servers[berxel]
    pass
