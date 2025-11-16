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

# node params
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HEX_ZMQ_SERVERS_DIR = f"{SCRIPT_DIR}/../../../hex_zmq_servers"

LAUNCH_PATH_DICT = {
    "zmq_dummy":
    f"{HEX_ZMQ_SERVERS_DIR}/../examples/basic/zmq_dummy/launch.py",
    "robot_dummy":
    f"{HEX_ZMQ_SERVERS_DIR}/../examples/basic/robot_dummy/launch.py",
}

LAUNCH_NODE_PARAMS_DICT = {
    "zmq_dummy": {
        # cli
        "zmq_dummy_cli": {
            "name": "zmq_dummy_cli_multi_launch",
            "net": {
                "ip": "127.0.0.1",
                "port": 12345,
            },
        },
        # srv
        "zmq_dummy_srv": {
            "name": "zmq_dummy_srv_multi_launch",
            "net": {
                "ip": "127.0.0.1",
                "port": 12345,
            },
        },
    },
    "robot_dummy": {
        # cli
        "robot_dummy_cli": {
            "name": "robot_dummy_cli_multi_launch",
            "net": {
                "ip": "127.0.0.1",
                "port": 12346,
            },
        },
        # srv
        "robot_dummy_srv": {
            "name": "robot_dummy_srv_multi_launch",
            "net": {
                "ip": "127.0.0.1",
                "port": 12346,
            },
            "params": {
                "dofs": [7],
                "limits": [[[-1.0, 1.0]] * 3] * 7,
                "states_init": [[0.0, 0.0, 0.0]] * 7,
            },
        }
    },
}


def get_node_cfgs(node_params_dict: dict = LAUNCH_NODE_PARAMS_DICT):
    zmq_dummy_params = node_params_dict.get(
        'zmq_dummy',
        LAUNCH_NODE_PARAMS_DICT['zmq_dummy'],
    )
    robot_dummy_params = node_params_dict.get(
        'robot_dummy',
        LAUNCH_NODE_PARAMS_DICT['robot_dummy'],
    )

    zmq_dummy_cfgs = HexNodeConfig.get_node_cfgs(
        LAUNCH_PATH_DICT['zmq_dummy'],
        zmq_dummy_params,
    )
    print(f"zmq_dummy_cfgs: {zmq_dummy_cfgs}")
    robot_dummy_cfgs = HexNodeConfig.get_node_cfgs(
        LAUNCH_PATH_DICT['robot_dummy'],
        robot_dummy_params,
    )
    print(f"robot_dummy_cfgs: {robot_dummy_cfgs}")

    node_cfgs = HexNodeConfig()
    node_cfgs.add_cfgs(zmq_dummy_cfgs)
    node_cfgs.add_cfgs(robot_dummy_cfgs)
    print(f"node_cfgs: {node_cfgs}")
    return node_cfgs


def main():
    node_cfgs = get_node_cfgs()
    launch = HexLaunch(node_cfgs)
    launch.run()


if __name__ == '__main__':
    main()
