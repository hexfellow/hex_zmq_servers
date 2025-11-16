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

# device config
GELLO_DEVICE = "/dev/ttyUSB0"

# node params
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HEX_ZMQ_SERVERS_DIR = f"{SCRIPT_DIR}/../../../hex_zmq_servers"
NODE_PARAMS_DICT = {
    # cli
    "robot_gello_cli": {
        "name": "robot_gello_cli",
        "net": {
            "ip": "127.0.0.1",
            "port": 12345,
        },
    },
    # srv
    "robot_gello_srv": {
        "name": "robot_gello_srv",
        "net": {
            "ip": "127.0.0.1",
            "port": 12345,
        },
        "params": {
            "idxs": [0, 1, 2, 3, 4, 5, 6],
            "invs": [1.0, -1.0, 1.0, 1.0, -1.0, 1.0, -3.5],
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
}


def get_node_cfgs(node_params_dict: dict = NODE_PARAMS_DICT):
    node_srv = node_params_dict.get(
        'robot_gello_srv',
        NODE_PARAMS_DICT['robot_gello_srv'],
    )
    node_cli = node_params_dict.get(
        'robot_gello_cli',
        NODE_PARAMS_DICT['robot_gello_cli'],
    )
    return HexNodeConfig([
        {
            "name":
            node_cli['name'] if 'name' in node_cli else "robot_gello_cli",
            "node_path":
            f"{HEX_ZMQ_SERVERS_DIR}/../examples/basic/robot_gello/cli.py",
            "cfg_path":
            f"{HEX_ZMQ_SERVERS_DIR}/../examples/basic/robot_gello/cli.json",
            "cfg": {
                **({
                    'net': node_cli['net']
                } if 'net' in node_cli else {}),
            },
        },
        {
            "name":
            node_srv['name'] if 'name' in node_srv else "robot_gello_srv",
            "node_path": HEX_ZMQ_SERVERS_PATH_DICT["robot_gello"],
            "cfg_path": HEX_ZMQ_CONFIGS_PATH_DICT["robot_gello"],
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
