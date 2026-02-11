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

END_POSE = [0.0, 0.0, 0.0, 0.7071068, 0.0, -0.7071068, 0.0]
INIT_POSE = [0.45, 0.0, 0.25, 0.9238795, 0.0, 0.0, 0.3826834]
ARM_TYPE = "archer_y6"
GRIPPER_TYPE = "gp100_p050"

# Mit config
MIT_CFG = {
    "joint_kp": [200.0, 200.0, 250.0, 150.0, 100.0, 100.0, 100.0],
    "joint_kd": [5.0, 5.0, 5.0, 5.0, 1.0, 1.0, 1.0],
    "se3_kp": [100.0, 100.0, 100.0, 50.0, 50.0, 50.0],
    "se3_kd": [10.0, 10.0, 10.0, 5.0, 5.0, 5.0]
    # "se3_kd": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
}

# node params
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HEX_ZMQ_SERVERS_DIR = f"{SCRIPT_DIR}/../../../hex_zmq_servers"
NODE_PARAMS_DICT = {
    # cli
    "work_impedance_sim_cli": {
        "name": "work_impedance_sim_cli",
        "node_path":
        f"{HEX_ZMQ_SERVERS_DIR}/../examples/adv/work_impedance_sim/cli.py",
        "cfg_path":
        f"{HEX_ZMQ_SERVERS_DIR}/../examples/adv/work_impedance_sim/cli.json",
        "cfg": {
            "model_path": HEXARM_URDF_PATH_DICT[f"{ARM_TYPE}_{GRIPPER_TYPE}"],
            "init_pose": INIT_POSE,
            "end_pose": END_POSE,
            "mit_cfg": MIT_CFG,
            "mujoco_net_cfg": {
                "ip": "127.0.0.1",
                "port": 12345,
            },
        },
    },
    # srv
    "mujoco_archer_y6_srv": {
        "name": "mujoco_archer_y6_srv",
        "node_path": HEX_ZMQ_SERVERS_PATH_DICT["mujoco_archer_y6"],
        "cfg_path": HEX_ZMQ_CONFIGS_PATH_DICT["mujoco_archer_y6"],
        "cfg": {
            "net": {
                "ip": "127.0.0.1",
                "port": 12345,
            },
            "params": {
                "control_hz": 500,
                "mit_kp":
                [150.0, 150.0, 150.0, 150.0, 150.0, 150.0, 150.0],
                "mit_kd": [20.0, 20.0, 20.0, 20.0, 20.0, 20.0, 20.0],
                "cam_type": "realsense",
                "headless": False,
            },
        },
    },
}


def get_node_cfgs(node_params_dict: dict = NODE_PARAMS_DICT,
                  launch_arg: dict | None = None):
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
