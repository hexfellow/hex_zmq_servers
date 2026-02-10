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

# server ports
HEXARM_SRV_PORT = 12345

END_POSE = [0.0, 0.0, 0.0, 0.7071068, 0.0, -0.7071068, 0.0]
INIT_POSE = [0.45, 0.0, 0.25, 1.0, 0.0, 0.0, 0.0]
ARM_TYPE = "archer_y6"
GRIPPER_TYPE = "empty"

# device config
DEVICE_IP = "172.18.5.116"
HEXARM_DEVICE_PORT = 8439

# Mit config
MIT_CFG = {
    "joint_kp": [200.0, 200.0, 250.0, 150.0, 100.0, 100.0, 100.0],
    "joint_kd": [5.0, 5.0, 5.0, 5.0, 1.0, 1.0, 1.0],
    "se3_kp": [500.0, 500.0, 500.0, 100.0, 100.0, 100.0],
    "se3_kd": [10.0, 10.0, 10.0, 5.0, 5.0, 5.0]
}

# node params
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HEX_ZMQ_SERVERS_DIR = f"{SCRIPT_DIR}/../../../hex_zmq_servers"
NODE_PARAMS_DICT = {
    # cli
    "work_impedance_real_cli": {
        "name": "work_impedance_real_cli",
        "node_path":
        f"{HEX_ZMQ_SERVERS_DIR}/../examples/adv/work_impedance_real/cli.py",
        "cfg_path":
        f"{HEX_ZMQ_SERVERS_DIR}/../examples/adv/work_impedance_real/cli.json",
        "cfg": {
            "model_path": HEXARM_URDF_PATH_DICT[f"{ARM_TYPE}_{GRIPPER_TYPE}"],
            "init_pose": INIT_POSE,
            "end_pose": END_POSE,
            "mit_cfg": MIT_CFG,
            "hexarm_net_cfg": {
                "port": HEXARM_SRV_PORT,
            },
        },
    },
    # srv
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
                "mit_kp": [0.0] * 7,
                "mit_kd": [0.0] * 7,
                "sens_ts": True,
            }
        }
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
