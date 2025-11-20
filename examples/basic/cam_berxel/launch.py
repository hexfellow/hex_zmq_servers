#!/usr/bin/env python3
# -*- coding:utf-8 -*-
################################################################
# Copyright 2025 Dong Zhaorui. All rights reserved.
# Author: Dong Zhaorui 847235539@qq.com
# Date  : 2025-09-25
################################################################

import os
from hex_zmq_servers import HexLaunch, HexNodeConfig
from hex_zmq_servers import HEX_ZMQ_SERVERS_PATH_DICT, HEX_ZMQ_CONFIGS_PATH_DICT

# device config
# # cam 0
# SERIAL_NUMBER = "P008GYX5728E1B010"
# SERVER_PORT = 12345
# EXPOSURE = 10000
# SENS_TS = True
# # cam 1
# SERIAL_NUMBER = "P008GYX5728E1B011"
# SERVER_PORT = 12346
# EXPOSURE = 10000
# SENS_TS = True
# cam 2
SERIAL_NUMBER = "P100RYB4C03M2B322"
SERVER_PORT = 12347
EXPOSURE = 10000
SENS_TS = True
# # cam 3
# SERIAL_NUMBER = "P050HYX5410E1A001"
# SERVER_PORT = 12348
# EXPOSURE = 10000
# SENS_TS = True

# node params
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HEX_ZMQ_SERVERS_DIR = f"{SCRIPT_DIR}/../../../hex_zmq_servers"
NODE_PARAMS_DICT = {
    # cli
    "cam_berxel_cli": {
        "name": "cam_berxel_cli",
        "node_path":
        f"{HEX_ZMQ_SERVERS_DIR}/../examples/basic/cam_berxel/cli.py",
        "cfg_path":
        f"{HEX_ZMQ_SERVERS_DIR}/../examples/basic/cam_berxel/cli.json",
        "cfg": {
            "depth_range": [70, 1000],
            "crop": [0, 400, 0, 640],
            "rotate_type": 0,
            "net": {
                "ip": "127.0.0.1",
                "port": SERVER_PORT,
            },
        }
    },
    # srv
    "cam_berxel_srv": {
        "name": "cam_berxel_srv",
        "node_path": HEX_ZMQ_SERVERS_PATH_DICT["cam_berxel"],
        "cfg_path": HEX_ZMQ_CONFIGS_PATH_DICT["cam_berxel"],
        "cfg": {
            "net": {
                "ip": "127.0.0.1",
                "port": SERVER_PORT,
            },
            "params": {
                "serial_number": SERIAL_NUMBER,
                "exposure": EXPOSURE,
                "sens_ts": SENS_TS,
            },
        },
    },
}


def get_node_cfgs(node_params_dict: dict = NODE_PARAMS_DICT):
    return HexNodeConfig.parse_node_params_dict(
        node_params_dict,
        NODE_PARAMS_DICT,
    )


def main():
    node_cfgs = get_node_cfgs()
    launch = HexLaunch(node_cfgs)
    launch.run()


if __name__ == '__main__':
    main()
