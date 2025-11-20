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
    "robot_dummy_0":
    f"{HEX_ZMQ_SERVERS_DIR}/../examples/basic/robot_dummy/launch.py",
    "robot_dummy_1":
    f"{HEX_ZMQ_SERVERS_DIR}/../examples/basic/robot_dummy/launch.py",
    "robot_dummy_2":
    f"{HEX_ZMQ_SERVERS_DIR}/../examples/basic/robot_dummy/launch.py",
}

LAUNCH_PARAMS_DICT = {
    "robot_dummy_0": {
        # cli
        "robot_dummy_cli": {
            "name": "robot_dummy_cli_0",
            "cfg": {
                "net": {
                    "ip": "127.0.0.1",
                    "port": 12345,
                },
            },
        },
        # srv
        "robot_dummy_srv": {
            "name": "robot_dummy_srv_0",
            "cfg": {
                "net": {
                    "ip": "127.0.0.1",
                    "port": 12345,
                },
                "params": {
                    "dofs": [7],
                    "limits": [[[-1.0, 1.0]] * 3] * 7,
                    "states_init": [[0.0, 0.0, 0.0]] * 7,
                },
            },
        },
    },
    "robot_dummy_1": {
        # cli
        "robot_dummy_cli": {
            "name": "robot_dummy_cli_1",
            "cfg": {
                "net": {
                    "ip": "127.0.0.1",
                    "port": 12346,
                },
            },
        },
        # srv
        "robot_dummy_srv": {
            "name": "robot_dummy_srv_1",
            "cfg": {
                "net": {
                    "ip": "127.0.0.1",
                    "port": 12346,
                },
                "params": {
                    "dofs": [7],
                    "limits": [[[-1.0, 1.0]] * 3] * 7,
                    "states_init": [[0.0, 0.0, 0.0]] * 7,
                },
            },
        },
    },
    "robot_dummy_2": {
        # cli
        "robot_dummy_cli": {
            "name": "robot_dummy_cli_2",
            "cfg": {
                "net": {
                    "ip": "127.0.0.1",
                    "port": 12347,
                },
            },
        },
        # srv
        "robot_dummy_srv": {
            "name": "robot_dummy_srv_2",
            "cfg": {
                "net": {
                    "ip": "127.0.0.1",
                    "port": 12347,
                },
                "params": {
                    "dofs": [7],
                    "limits": [[[-1.0, 1.0]] * 3] * 7,
                    "states_init": [[0.0, 0.0, 0.0]] * 7,
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
