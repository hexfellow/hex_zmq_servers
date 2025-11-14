#!/usr/bin/env python3
# -*- coding:utf-8 -*-
################################################################
# Copyright 2025 Dong Zhaorui. All rights reserved.
# Author: Dong Zhaorui 847235539@qq.com
# Date  : 2025-09-25
################################################################

import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HEX_ZMQ_SERVERS_DIR = f"{SCRIPT_DIR}/../../../hex_zmq_servers"

from hex_zmq_servers import HexLaunch, HEX_ZMQ_SERVERS_PATH_DICT, HEX_ZMQ_CONFIGS_PATH_DICT

NODE_CFGS = [
    {
        "name":
        "mujoco_archer_d6y_cli",
        "venv":
        f"{HEX_ZMQ_SERVERS_DIR}/../.venv",
        "node_path":
        f"{HEX_ZMQ_SERVERS_DIR}/../examples/basic/mujoco_archer_d6y/cli.py",
        "cfg_path":
        f"{HEX_ZMQ_SERVERS_DIR}/../examples/basic/mujoco_archer_d6y/cli.json",
    },
    # {
    #     "name": "mujoco_archer_d6y_srv",
    #     "venv": f"{HEX_ZMQ_SERVERS_DIR}/../.venv",
    #     "node_path": HEX_ZMQ_SERVERS_PATH_DICT["mujoco_archer_d6y"],
    #     "cfg_path": HEX_ZMQ_CONFIGS_PATH_DICT["mujoco_archer_d6y"],
    #     "cfg": {
    #         "params": {
    #             "mit_kp":
    #             [1500.0, 1500.0, 1500.0, 1500.0, 1500.0, 1500.0, 1500.0],
    #             "mit_kd": [20.0, 20.0, 20.0, 20.0, 20.0, 20.0, 20.0],
    #         },
    #     },
    # },
]


def main():
    launch = HexLaunch(NODE_CFGS)
    launch.run()


if __name__ == '__main__':
    main()
