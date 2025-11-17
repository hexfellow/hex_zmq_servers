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

# robot model config
ARM_TYPE = "archer_l6y"
GRIPPER_TYPE = "gp100"
if GRIPPER_TYPE == "empty":
    USE_GRIPPER = False
else:
    USE_GRIPPER = True

# device config
DEVICE_IP = "192.168.1.101"
HEXARM_DEVICE_PORT = 8439

# node params
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HEX_ZMQ_SERVERS_DIR = f"{SCRIPT_DIR}/../../hex_zmq_servers"
NODE_PARAMS_DICT = {
    # cli
    "robot_hexarm_cli": {
        "name": "robot_hexarm_cli",
        "node_path":
        f"{HEX_ZMQ_SERVERS_DIR}/../examples/basic/robot_hexarm/cli.py",
        "cfg_path":
        f"{HEX_ZMQ_SERVERS_DIR}/../examples/basic/robot_hexarm/cli.json",
        "cfg": {
            "net": {
                "ip": "127.0.0.1",
                "port": 12345,
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
                "ip": "127.0.0.1",
                "port": 12345,
            },
            "params": {
                "device_ip": DEVICE_IP,
                "device_port": HEXARM_DEVICE_PORT,
                "control_hz": 500,
                "arm_type": ARM_TYPE,
                "use_gripper": USE_GRIPPER,
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
