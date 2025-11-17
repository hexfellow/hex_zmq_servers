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
# SERIAL_NUMBER = "P050HYX5410E1A001"
# EXPOSURE = 16000
# # cam 1
# SERIAL_NUMBER = "P050HYX5421E2A004"
# EXPOSURE = 16000
# cam 2
SERIAL_NUMBER = "P100RYB4C03M2B322"
EXPOSURE = 10000

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
            "net": {
                "ip": "127.0.0.1",
                "port": 12345,
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
                "port": 12345,
            },
            "params": {
                "serial_number": SERIAL_NUMBER,
                "exposure": EXPOSURE,
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
