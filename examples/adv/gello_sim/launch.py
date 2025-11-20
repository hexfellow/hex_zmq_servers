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
ARM_TYPE = "archer_y6"
GRIPPER_TYPE = "gp100_p050"

# server ports
GELLO_SRV_PORT = 12345
MUJOCO_SRV_PORT = 12346

# device config
GELLO_DEVICE = "/dev/ttyUSB0"

# node params
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HEX_ZMQ_SERVERS_DIR = f"{SCRIPT_DIR}/../../../hex_zmq_servers"
NODE_PARAMS_DICT = {
    "gello_sim_cli": {
        "name": "gello_sim_cli",
        "node_path": f"{HEX_ZMQ_SERVERS_DIR}/../examples/adv/gello_sim/cli.py",
        "cfg_path":
        f"{HEX_ZMQ_SERVERS_DIR}/../examples/adv/gello_sim/cli.json",
        "cfg": {
            "model_path": HEXARM_URDF_PATH_DICT[f"{ARM_TYPE}_{GRIPPER_TYPE}"],
            "last_link": "link_6",
            "gello_net_cfg": {
                "port": GELLO_SRV_PORT,
            },
            "mujoco_net_cfg": {
                "port": MUJOCO_SRV_PORT,
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
                "invs": [1.0, -1.0, 1.0, 1.0, -1.0, 1.0, -2.0],
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
    "mujoco_archer_y6_srv": {
        "name": "mujoco_archer_y6_srv",
        "node_path": HEX_ZMQ_SERVERS_PATH_DICT["mujoco_archer_y6"],
        "cfg_path": HEX_ZMQ_CONFIGS_PATH_DICT["mujoco_archer_y6"],
        "cfg": {
            "net": {
                "port": MUJOCO_SRV_PORT,
            },
            "params": {
                "states_rate": 500,
                "img_rate": 30,
                "tau_ctrl": False,
                "mit_kp": [200.0, 200.0, 200.0, 75.0, 15.0, 15.0, 20.0],
                "mit_kd": [12.5, 12.5, 12.5, 6.0, 0.31, 0.31, 1.0],
                "headless": False,
                "sens_ts": True,
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
