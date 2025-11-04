#!/usr/bin/env python3
# -*- coding:utf-8 -*-
################################################################
# Copyright 2025 Dong Zhaorui. All rights reserved.
# Author: Dong Zhaorui 847235539@qq.com
# Date  : 2025-09-12
################################################################

import numpy as np
from ...zmq_base import hex_zmq_ts_now
from ..mujoco_base import HexMujocoClientBase

NET_CONFIG = {
    "ip": "127.0.0.1",
    "port": 12345,
    "client_timeout_ms": 200,
    "server_timeout_ms": 1_000,
    "server_num_workers": 4,
}


class HexMujocoE3DesktopClient(HexMujocoClientBase):

    def __init__(
        self,
        net_config: dict = NET_CONFIG,
    ):
        HexMujocoClientBase.__init__(self, net_config)
        self._cmds_seq = {
            "left": 0,
            "right": 0,
        }
        self._camera_seq = {
            "head_rgb": 0,
            "head_depth": 0,
            "left_rgb": 0,
            "left_depth": 0,
            "right_rgb": 0,
            "right_depth": 0,
        }

    def set_cmds(
        self,
        cmds: np.ndarray,
        robot_name: str | None = None,
    ) -> bool:
        req_cmd = "set_cmds"
        if robot_name is not None:
            req_cmd += f"_{robot_name}"
        hdr, _ = self.request(
            {
                "cmd": req_cmd,
                "ts": hex_zmq_ts_now(),
                "args": self._cmds_seq[robot_name],
            },
            cmds,
        )
        # print(f"{req_cmd} seq: {self._cmds_seq[robot_name]}")
        try:
            cmd = hdr["cmd"]
            if cmd == f"{req_cmd}_ok":
                self._cmds_seq[robot_name] = (self._cmds_seq[robot_name] +
                                              1) % self._max_seq_num
                return True
            else:
                return False
        except KeyError:
            print(f"\033[91m{hdr['cmd']} requires `cmd`\033[0m")
            return False
        except Exception as e:
            print(f"\033[91m{req_cmd} failed: {e}\033[0m")
            return False

    def reset(self):
        HexMujocoClientBase.reset(self)
        self._cmds_seq = {
            "left": 0,
            "right": 0,
        }
        self._camera_seq = {
            "head_rgb": 0,
            "head_depth": 0,
            "left_rgb": 0,
            "left_depth": 0,
            "right_rgb": 0,
            "right_depth": 0,
        }

    def _process_frame(
        self,
        camera_name: str | None = None,
        depth_flag: bool = False,
    ):
        if camera_name is None:
            raise ValueError("camera_name is required")

        req_cmd = f"get_{'depth' if depth_flag else 'rgb'}_{camera_name}"
        seq_key = f"{camera_name}_{'depth' if depth_flag else 'rgb'}"

        hdr, img = self.request({
            "cmd":
            req_cmd,
            "args": (1 + self._camera_seq[seq_key]) % self._max_seq_num,
        })

        try:
            cmd = hdr["cmd"]
            if cmd == f"{req_cmd}_ok":
                self._camera_seq[seq_key] = hdr["args"]
                return hdr, img
            else:
                return None, None
        except KeyError:
            print(f"\033[91m{hdr['cmd']} requires `cmd`\033[0m")
            return None, None
        except Exception as e:
            print(f"\033[91m__process_frame failed: {e}\033[0m")
            return None, None
