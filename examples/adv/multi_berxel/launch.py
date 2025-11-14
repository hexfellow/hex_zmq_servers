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

# device config
# cam 0
CAM_0_PORT = 12345
CAM_0_SERIAL_NUMBER = "P050HYX5421E2A026"
CAM_0_EXPOSURE = 16000
CAM_0_SENS_TS = True
# cam 1
CAM_1_PORT = 12346
CAM_1_SERIAL_NUMBER = "P050HYX5421E2A006"
CAM_1_EXPOSURE = 16000
CAM_1_SENS_TS = True
# cam 2
CAM_2_PORT = 12347
CAM_2_SERIAL_NUMBER = "P100RYB5516M2B066"
CAM_2_EXPOSURE = 10000
CAM_2_SENS_TS = True

NODE_CFGS = [
    {
        "name": "multi_berxel_cli",
        "venv": f"{HEX_ZMQ_SERVERS_DIR}/../.venv",
        "node_path":
        f"{HEX_ZMQ_SERVERS_DIR}/../examples/adv/multi_berxel/cli.py",
        "cfg_path":
        f"{HEX_ZMQ_SERVERS_DIR}/../examples/adv/multi_berxel/cli.json",
    },
    {
        "name": "cam_berxel_0_srv",
        "venv": f"{HEX_ZMQ_SERVERS_DIR}/../.venv",
        "node_path": HEX_ZMQ_SERVERS_PATH_DICT["cam_berxel"],
        "cfg_path": HEX_ZMQ_CONFIGS_PATH_DICT["cam_berxel"],
        "cfg": {
            "net": {
                "port": CAM_0_PORT,
            },
            "params": {
                "serial_number": CAM_0_SERIAL_NUMBER,
                "exposure": CAM_0_EXPOSURE,
                "sens_ts": CAM_0_SENS_TS,
            },
        },
    },
    {
        "name": "cam_berxel_1_srv",
        "venv": f"{HEX_ZMQ_SERVERS_DIR}/../.venv",
        "node_path": HEX_ZMQ_SERVERS_PATH_DICT["cam_berxel"],
        "cfg_path": HEX_ZMQ_CONFIGS_PATH_DICT["cam_berxel"],
        "cfg": {
            "net": {
                "port": CAM_1_PORT,
            },
            "params": {
                "serial_number": CAM_1_SERIAL_NUMBER,
                "exposure": CAM_1_EXPOSURE,
                "sens_ts": CAM_1_SENS_TS,
            },
        },
    },
    {
        "name": "cam_berxel_2_srv",
        "venv": f"{HEX_ZMQ_SERVERS_DIR}/../.venv",
        "node_path": HEX_ZMQ_SERVERS_PATH_DICT["cam_berxel"],
        "cfg_path": HEX_ZMQ_CONFIGS_PATH_DICT["cam_berxel"],
        "cfg": {
            "net": {
                "port": CAM_2_PORT,
            },
            "params": {
                "serial_number": CAM_2_SERIAL_NUMBER,
                "exposure": CAM_2_EXPOSURE,
                "sens_ts": CAM_2_SENS_TS,
            },
        },
    },
]


def main():
    launch = HexLaunch(NODE_CFGS)
    launch.run()


if __name__ == '__main__':
    main()
