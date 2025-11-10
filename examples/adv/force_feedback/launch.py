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

from hex_zmq_servers import (
    HexLaunch,
    HEX_ZMQ_SERVERS_PATH_DICT,
    HEX_ZMQ_CONFIGS_PATH_DICT,
    HEXARM_URDF_PATH_DICT,
)

# robot model config
ARM_TYPE = "archer_d6y"
GRIPPER_TYPE = "empty"
if GRIPPER_TYPE == "empty":
    USE_GRIPPER = False
else:
    USE_GRIPPER = True

# server ports
MASTER_SRV_PORT = 12345
SLAVE_SRV_PORT = 12346

# device config
DEVICE_IP = "192.168.1.111"
MASTER_DEVICE_PORT = 8439
SLAVE_DEVICE_PORT = 9439

# node configs
NODE_CFGS = [
    {
        "name": "force_feedback_cli",
        "venv": f"{HEX_ZMQ_SERVERS_DIR}/../.venv",
        "node_path":
        f"{HEX_ZMQ_SERVERS_DIR}/../examples/adv/force_feedback/cli.py",
        "cfg_path":
        f"{HEX_ZMQ_SERVERS_DIR}/../examples/adv/force_feedback/cli.json",
        "cfg": {
            "model_path": HEXARM_URDF_PATH_DICT[f"{ARM_TYPE}_{GRIPPER_TYPE}"],
            "last_link": "link_6",
            "use_gripper": USE_GRIPPER,
            "hexarm_master_net_cfg": {
                "port": MASTER_SRV_PORT,
            },
            "hexarm_slave_net_cfg": {
                "port": SLAVE_SRV_PORT,
            },
        },
    },
    {
        "name": "robot_hexarm_master_srv",
        "venv": f"{HEX_ZMQ_SERVERS_DIR}/../.venv",
        "node_path": HEX_ZMQ_SERVERS_PATH_DICT["robot_hexarm"],
        "cfg_path": HEX_ZMQ_CONFIGS_PATH_DICT["robot_hexarm"],
        "cfg": {
            "net": {
                "port": MASTER_SRV_PORT,
            },
            "params": {
                "device_ip": DEVICE_IP,
                "device_port": MASTER_DEVICE_PORT,
                "control_hz": 500,
                "arm_type": ARM_TYPE,
                "use_gripper": USE_GRIPPER,
                "mit_kp": [0.0] * 7,
                "mit_kd": [0.0] * 7,
                "sens_ts": True,
            }
        }
    },
    {
        "name": "robot_hexarm_slave_srv",
        "venv": f"{HEX_ZMQ_SERVERS_DIR}/../.venv",
        "node_path": HEX_ZMQ_SERVERS_PATH_DICT["robot_hexarm"],
        "cfg_path": HEX_ZMQ_CONFIGS_PATH_DICT["robot_hexarm"],
        "cfg": {
            "net": {
                "port": SLAVE_SRV_PORT,
            },
            "params": {
                "device_ip": DEVICE_IP,
                "device_port": SLAVE_DEVICE_PORT,
                "control_hz": 500,
                "arm_type": ARM_TYPE,
                "use_gripper": USE_GRIPPER,
                "mit_kp": [200.0, 200.0, 200.0, 75.0, 15.0, 15.0, 20.0],
                "mit_kd": [10.0, 10.0, 10.0, 6.0, 0.31, 0.31, 1.0],
                "sens_ts": True,
            }
        }
    },
]


def main():
    launch = HexLaunch(NODE_CFGS)
    launch.run()


if __name__ == '__main__':
    main()
