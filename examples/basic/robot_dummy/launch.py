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
NODE_PARAMS_DICT = {
    # cli
    "robot_dummy_cli": {
        "name": "robot_dummy_cli",
        "node_path":
        f"{HEX_ZMQ_SERVERS_DIR}/../examples/basic/robot_dummy/cli.py",
        "cfg_path":
        f"{HEX_ZMQ_SERVERS_DIR}/../examples/basic/robot_dummy/cli.json",
        "cfg": {
            "net": {
                "ip": "127.0.0.1",
                "port": 12345,
            },
        },
    },
    # srv
    "robot_dummy_srv": {
        "name": "robot_dummy_srv",
        "node_path": HEX_ZMQ_SERVERS_PATH_DICT["robot_dummy"],
        "cfg_path": HEX_ZMQ_CONFIGS_PATH_DICT["robot_dummy"],
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
