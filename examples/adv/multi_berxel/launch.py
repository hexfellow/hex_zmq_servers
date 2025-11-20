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
## P100
# cam 0
CAM_0_PORT = 12345
CAM_0_SERIAL_NUMBER = "P100RYB4C03M2B322"
CAM_0_EXPOSURE = 10000
CAM_0_SENS_TS = True
# ## P008
# # cam 1
# CAM_1_PORT = 12346
# CAM_1_SERIAL_NUMBER = "P008GYX5728E1B010"
# CAM_1_EXPOSURE = 10000
# CAM_1_SENS_TS = True
# # cam 2
# CAM_2_PORT = 12347
# CAM_2_SERIAL_NUMBER = "P008GYX5728E1B011"
# CAM_2_EXPOSURE = 10000
# CAM_2_SENS_TS = True
## P050
# cam 1
CAM_1_PORT = 12346
CAM_1_SERIAL_NUMBER = "P050HYX5410E1A001"
CAM_1_EXPOSURE = 10000
CAM_1_SENS_TS = True
# cam 2
CAM_2_PORT = 12347
CAM_2_SERIAL_NUMBER = "P050HYX5421E2A004"
CAM_2_EXPOSURE = 10000
CAM_2_SENS_TS = True

# node params
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HEX_ZMQ_SERVERS_DIR = f"{SCRIPT_DIR}/../../../hex_zmq_servers"
NODE_PARAMS_DICT = {
    "multi_berxel_cli": {
        "name": "multi_berxel_cli",
        "node_path":
        f"{HEX_ZMQ_SERVERS_DIR}/../examples/adv/multi_berxel/cli.py",
        "cfg_path":
        f"{HEX_ZMQ_SERVERS_DIR}/../examples/adv/multi_berxel/cli.json",
        "cfg": {
            "depth_range": [70, 1000],
            "crop": [0, 400, 0, 640],
            "rotate_type": 0,
            "berxel_0_net_cfg": {
                "port": CAM_0_PORT,
            },
            "berxel_1_net_cfg": {
                "port": CAM_1_PORT,
            },
            "berxel_2_net_cfg": {
                "port": CAM_2_PORT,
            }
        },
    },
    "cam_berxel_0_srv": {
        "name": "cam_berxel_0_srv",
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
    "cam_berxel_1_srv": {
        "name": "cam_berxel_1_srv",
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
    "cam_berxel_2_srv": {
        "name": "cam_berxel_2_srv",
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
