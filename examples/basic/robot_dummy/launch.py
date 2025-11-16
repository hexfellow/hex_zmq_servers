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
        "net": {
            "ip": "127.0.0.1",
            "port": 12345,
        },
    },
    # srv
    "robot_dummy_srv": {
        "name": "robot_dummy_srv",
        "net": {
            "ip": "127.0.0.1",
            "port": 12345,
        },
        "params": {
            "dofs": [7],
            "limits": [[[-1.0, 1.0]] * 3] * 7,
            "states_init": [[0.0, 0.0, 0.0]] * 7,
        },
    }
}


def get_node_cfgs(node_params_dict: dict = NODE_PARAMS_DICT):
    node_srv = node_params_dict.get(
        'robot_dummy_srv',
        NODE_PARAMS_DICT['robot_dummy_srv'],
    )
    node_cli = node_params_dict.get(
        'robot_dummy_cli',
        NODE_PARAMS_DICT['robot_dummy_cli'],
    )
    return HexNodeConfig([
        {
            "name":
            node_cli['name'] if 'name' in node_cli else "robot_dummy_cli",
            "node_path":
            f"{HEX_ZMQ_SERVERS_DIR}/../examples/basic/robot_dummy/cli.py",
            "cfg_path":
            f"{HEX_ZMQ_SERVERS_DIR}/../examples/basic/robot_dummy/cli.json",
            "cfg": {
                **({
                    'net': node_cli['net']
                } if 'net' in node_cli else {}),
            },
        },
        {
            "name":
            node_srv['name'] if 'name' in node_srv else "robot_dummy_srv",
            "node_path": HEX_ZMQ_SERVERS_PATH_DICT["robot_dummy"],
            "cfg_path": HEX_ZMQ_CONFIGS_PATH_DICT["robot_dummy"],
            "cfg": {
                **({
                    'net': node_srv['net']
                } if 'net' in node_srv else {}),
                **({
                    'params': node_srv['params']
                } if 'params' in node_srv else {}),
            },
        },
    ])


def main():
    node_cfgs = get_node_cfgs()
    launch = HexLaunch(node_cfgs)
    launch.run()


if __name__ == '__main__':
    main()
