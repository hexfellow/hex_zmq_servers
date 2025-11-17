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
from hex_zmq_servers import HEXARM_URDF_PATH_DICT

# robot model config
ARM_TYPE = "archer_l6y"
GRIPPER_TYPE = "gp100"
if GRIPPER_TYPE == "empty":
    USE_GRIPPER = False
else:
    USE_GRIPPER = True

# server ports
GELLO_SRV_PORT = 12345
HEXARM_SRV_PORT = 12346

# device config
GELLO_DEVICE = "/dev/ttyUSB0"
DEVICE_IP = "192.168.1.101"
HEXARM_DEVICE_PORT = 8439

# node params
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HEX_ZMQ_SERVERS_DIR = f"{SCRIPT_DIR}/../../../hex_zmq_servers"
NODE_PARAMS_DICT = {
    "gello_real_cli": {
        "name": "gello_real_cli",
        "node_path":
        f"{HEX_ZMQ_SERVERS_DIR}/../examples/adv/gello_real/cli.py",
        "cfg_path":
        f"{HEX_ZMQ_SERVERS_DIR}/../examples/adv/gello_real/cli.json",
        "cfg": {
            "model_path": HEXARM_URDF_PATH_DICT[f"{ARM_TYPE}_{GRIPPER_TYPE}"],
            "last_link": "link_6",
            "use_gripper": USE_GRIPPER,
            "gello_net_cfg": {
                "port": GELLO_SRV_PORT,
            },
            "hexarm_net_cfg": {
                "port": HEXARM_SRV_PORT,
            },
        },
    },
    "robot_gello_srv": {
        "name": "robot_gello_srv",
        "node_path": HEX_ZMQ_SERVERS_PATH_DICT["robot_gello"],
        "cfg_path": HEX_ZMQ_CONFIGS_PATH_DICT["robot_gello"],
        "cfg": {
            "net": {
                "port": GELLO_SRV_PORT,
            },
            "params": {
                "idxs": [0, 1, 2, 3, 4, 5, 6],
                "invs": [1.0, -1.0, 1.0, 1.0, -1.0, 1.0, -3.5],
                "limits": [
                    [-2.7, 2.7],
                    [-1.57, 2.09],
                    [0, 3.14],
                    [-1.57, 1.57],
                    [-1.57, 1.57],
                    [-1.57, 1.57],
                    [0.0, 1.33],
                ],
                "device":
                GELLO_DEVICE,
                "baudrate":
                115200,
                "max_retries":
                3,
                "sens_ts":
                True,
            },
        },
    },
    "robot_hexarm_srv": {
        "name": "robot_hexarm_srv",
        "node_path": HEX_ZMQ_SERVERS_PATH_DICT["robot_hexarm"],
        "cfg_path": HEX_ZMQ_CONFIGS_PATH_DICT["robot_hexarm"],
        "cfg": {
            "net": {
                "port": HEXARM_SRV_PORT,
            },
            "params": {
                "device_ip": DEVICE_IP,
                "device_port": HEXARM_DEVICE_PORT,
                "control_hz": 500,
                "arm_type": ARM_TYPE,
                "use_gripper": USE_GRIPPER,
                "mit_kp": [200.0, 200.0, 200.0, 75.0, 15.0, 15.0, 20.0],
                "mit_kd": [10.0, 10.0, 10.0, 6.0, 0.31, 0.31, 1.0],
                "sens_ts": True,
            }
        }
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
