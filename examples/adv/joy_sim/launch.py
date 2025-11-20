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
MUJOCO_SRV_PORT = 12345

# node params
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HEX_ZMQ_SERVERS_DIR = f"{SCRIPT_DIR}/../../../hex_zmq_servers"
NODE_PARAMS_DICT = {
    "joy_sim_cli": {
        "name": "joy_sim_cli",
        "node_path": f"{HEX_ZMQ_SERVERS_DIR}/../examples/adv/joy_sim/cli.py",
        "cfg_path": f"{HEX_ZMQ_SERVERS_DIR}/../examples/adv/joy_sim/cli.json",
        "cfg": {
            "model_path": HEXARM_URDF_PATH_DICT[f"{ARM_TYPE}_{GRIPPER_TYPE}"],
            "last_link": "link_6",
            "mujoco_net_cfg": {
                "port": MUJOCO_SRV_PORT,
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
                "mit_kp":
                [1500.0, 1500.0, 1500.0, 1500.0, 1500.0, 1500.0, 1500.0],
                "mit_kd": [20.0, 20.0, 20.0, 20.0, 20.0, 20.0, 20.0],
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
