#!/usr/bin/env python3
# -*- coding:utf-8 -*-
################################################################
# Copyright 2025 Dong Zhaorui. All rights reserved.
# Author: Dong Zhaorui 847235539@qq.com
# Date  : 2025-09-25
################################################################

import os
from hex_zmq_servers import HexLaunch, HexNodeConfig

# node params
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HEX_ZMQ_SERVERS_DIR = f"{SCRIPT_DIR}/../../../hex_zmq_servers"

LAUNCH_PATH_DICT = {
    "cam_berxel_0":
    f"{HEX_ZMQ_SERVERS_DIR}/../examples/basic/cam_berxel/launch.py",
    "cam_berxel_1":
    f"{HEX_ZMQ_SERVERS_DIR}/../examples/basic/cam_berxel/launch.py",
    "cam_berxel_2":
    f"{HEX_ZMQ_SERVERS_DIR}/../examples/basic/cam_berxel/launch.py",
}

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

LAUNCH_PARAMS_DICT = {
    "cam_berxel_0": {
        "cam_berxel_cli": {
            "name": "cam_berxel_cli_0",
            "cfg": {
                "depth_range": [70, 1000],
                "crop": [0, 400, 0, 640],
                "rotate_type": 0,
                "net": {
                    "port": CAM_0_PORT,
                },
            },
        },
        "cam_berxel_srv": {
            "name": "cam_berxel_srv_0",
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
    },
    "cam_berxel_1": {
        "cam_berxel_cli": {
            "name": "cam_berxel_cli_1",
            "cfg": {
                "depth_range": [70, 1000],
                "crop": [0, 400, 0, 640],
                "rotate_type": 0,
                "net": {
                    "port": CAM_1_PORT,
                },
            },
        },
        "cam_berxel_srv": {
            "name": "cam_berxel_srv_1",
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
    },
    "cam_berxel_2": {
        "cam_berxel_cli": {
            "name": "cam_berxel_cli_2",
            "cfg": {
                "depth_range": [70, 1000],
                "crop": [0, 400, 0, 640],
                "rotate_type": 0,
                "net": {
                    "port": CAM_2_PORT,
                },
            },
        },
        "cam_berxel_srv": {
            "name": "cam_berxel_srv_2",
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
    },
}


def get_node_cfgs(params_dict: dict = LAUNCH_PARAMS_DICT):
    return HexNodeConfig.get_launch_params_cfgs(
        launch_params_dict=params_dict,
        launch_default_params_dict=LAUNCH_PARAMS_DICT,
        launch_path_dict=LAUNCH_PATH_DICT,
    )


def main():
    node_cfgs = get_node_cfgs()
    launch = HexLaunch(node_cfgs)
    launch.run()


if __name__ == '__main__':
    main()
