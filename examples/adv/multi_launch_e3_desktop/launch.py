#!/usr/bin/env python3
# -*- coding:utf-8 -*-
################################################################
# Copyright 2025 Dong Zhaorui. All rights reserved.
# Author: Dong Zhaorui 847235539@qq.com
# Date  : 2025-09-25
################################################################

import os
from hex_zmq_servers import HexLaunch, HexNodeConfig
from hex_zmq_servers import HEXARM_URDF_PATH_DICT

# node params
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HEX_ZMQ_SERVERS_DIR = f"{SCRIPT_DIR}/../../../hex_zmq_servers"

LAUNCH_PATH_DICT = {
    "cam_berxel_0":
    (f"{HEX_ZMQ_SERVERS_DIR}/../examples/basic/cam_berxel/launch.py", None),
    "cam_berxel_1":
    (f"{HEX_ZMQ_SERVERS_DIR}/../examples/basic/cam_berxel/launch.py", None),
    "cam_berxel_2":
    (f"{HEX_ZMQ_SERVERS_DIR}/../examples/basic/cam_berxel/launch.py", None),
    "zero_gravity_0":
    (f"{HEX_ZMQ_SERVERS_DIR}/../examples/adv/zero_gravity/launch.py", None),
    "zero_gravity_1":
    (f"{HEX_ZMQ_SERVERS_DIR}/../examples/adv/zero_gravity/launch.py", None),
}

# robot model config
ARM_TYPE = "archer_y6"
GRIPPER_TYPE = "gp80_p008_handle"

# device config
FRAME_RATE = 30
## P100
# cam 0
CAM_0_PORT = 12345
CAM_0_SERIAL_NUMBER = "HK100RB5425M2B024"
CAM_0_EXPOSURE = 10000
CAM_0_SENS_TS = True
## P008
# cam 1
CAM_1_PORT = 12346
CAM_1_SERIAL_NUMBER = "P008GYX5728E1B010"
CAM_1_EXPOSURE = 10000
CAM_1_SENS_TS = True
# cam 2
CAM_2_PORT = 12347
CAM_2_SERIAL_NUMBER = "P008GYX5728E1B011"
CAM_2_EXPOSURE = 10000
CAM_2_SENS_TS = True
## arm
# zero gravity 0
ZERO_GRAVITY_0_SRV_PORT = 12348
ZERO_GRAVITY_0_DEVICE_IP = "192.168.3.2"
ZERO_GRAVITY_0_DEVICE_PORT = 8439
# zero gravity 1
ZERO_GRAVITY_1_SRV_PORT = 12349
ZERO_GRAVITY_1_DEVICE_IP = "192.168.3.2"
ZERO_GRAVITY_1_DEVICE_PORT = 9439

LAUNCH_PARAMS_DICT = {
    "cam_berxel_0": {
        "cam_berxel_cli": {
            "name": "cam_berxel_cli_0",
            "cfg": {
                "depth_range": [70, 1000],
                "crop": [0, 400, 0, 640],
                "rotate_type": 0,
                "net": {
                    "port": CAM_0_PORT,
                },
            },
        },
        "cam_berxel_srv": {
            "name": "cam_berxel_srv_0",
            "cfg": {
                "net": {
                    "port": CAM_0_PORT,
                },
                "params": {
                    "serial_number": CAM_0_SERIAL_NUMBER,
                    "exposure": CAM_0_EXPOSURE,
                    "frame_rate": FRAME_RATE,
                    "sens_ts": CAM_0_SENS_TS,
                },
            },
        },
    },
    "cam_berxel_1": {
        "cam_berxel_cli": {
            "name": "cam_berxel_cli_1",
            "cfg": {
                "depth_range": [70, 1000],
                "crop": [0, 400, 0, 640],
                "rotate_type": 0,
                "net": {
                    "port": CAM_1_PORT,
                },
            },
        },
        "cam_berxel_srv": {
            "name": "cam_berxel_srv_1",
            "cfg": {
                "net": {
                    "port": CAM_1_PORT,
                },
                "params": {
                    "serial_number": CAM_1_SERIAL_NUMBER,
                    "exposure": CAM_1_EXPOSURE,
                    "frame_rate": FRAME_RATE,
                    "sens_ts": CAM_1_SENS_TS,
                },
            },
        },
    },
    "cam_berxel_2": {
        "cam_berxel_cli": {
            "name": "cam_berxel_cli_2",
            "cfg": {
                "depth_range": [70, 1000],
                "crop": [0, 400, 0, 640],
                "rotate_type": 0,
                "net": {
                    "port": CAM_2_PORT,
                },
            },
        },
        "cam_berxel_srv": {
            "name": "cam_berxel_srv_2",
            "cfg": {
                "net": {
                    "port": CAM_2_PORT,
                },
                "params": {
                    "serial_number": CAM_2_SERIAL_NUMBER,
                    "exposure": CAM_2_EXPOSURE,
                    "frame_rate": FRAME_RATE,
                    "sens_ts": CAM_2_SENS_TS,
                },
            },
        },
    },
    "zero_gravity_0": {
        "zero_gravity_cli": {
            "name": "zero_gravity_cli_0",
            "cfg": {
                "model_path":
                HEXARM_URDF_PATH_DICT[f"{ARM_TYPE}_{GRIPPER_TYPE}"],
                "last_link": "link_6",
                "hexarm_net_cfg": {
                    "port": ZERO_GRAVITY_0_SRV_PORT,
                },
            },
        },
        "robot_hexarm_srv": {
            "name": "robot_hexarm_srv_0",
            "cfg": {
                "net": {
                    "port": ZERO_GRAVITY_0_SRV_PORT,
                },
                "params": {
                    "device_ip": ZERO_GRAVITY_0_DEVICE_IP,
                    "device_port": ZERO_GRAVITY_0_DEVICE_PORT,
                    "control_hz": 500,
                    "arm_type": ARM_TYPE,
                    "mit_kp": [0.0] * 7,
                    "mit_kd": [0.0] * 7,
                    "sens_ts": True,
                }
            }
        },
    },
    "zero_gravity_1": {
        "zero_gravity_cli": {
            "name": "zero_gravity_cli_1",
            "cfg": {
                "model_path":
                HEXARM_URDF_PATH_DICT[f"{ARM_TYPE}_{GRIPPER_TYPE}"],
                "last_link": "link_6",
                "hexarm_net_cfg": {
                    "port": ZERO_GRAVITY_1_SRV_PORT,
                },
            },
        },
        "robot_hexarm_srv": {
            "name": "robot_hexarm_srv_1",
            "cfg": {
                "net": {
                    "port": ZERO_GRAVITY_1_SRV_PORT,
                },
                "params": {
                    "device_ip": ZERO_GRAVITY_1_DEVICE_IP,
                    "device_port": ZERO_GRAVITY_1_DEVICE_PORT,
                    "control_hz": 500,
                    "arm_type": ARM_TYPE,
                    "mit_kp": [0.0] * 7,
                    "mit_kd": [0.0] * 7,
                    "sens_ts": True,
                }
            }
        },
    },
}


def get_node_cfgs(params_dict: dict = LAUNCH_PARAMS_DICT,
                  launch_arg: dict | None = None):
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
