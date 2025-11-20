#!/usr/bin/env python3
# -*- coding:utf-8 -*-
################################################################
# Copyright 2025 Dong Zhaorui. All rights reserved.
# Author: Dong Zhaorui 847235539@qq.com
# Date  : 2025-09-12
################################################################

from ..mujoco_base import HexMujocoClientBase

NET_CONFIG = {
    "ip": "127.0.0.1",
    "port": 12345,
    "client_timeout_ms": 200,
    "server_timeout_ms": 1_000,
    "server_num_workers": 4,
}


class HexMujocoArcherY6Client(HexMujocoClientBase):

    def __init__(
        self,
        net_config: dict = NET_CONFIG,
    ):
        HexMujocoClientBase.__init__(self, net_config)
