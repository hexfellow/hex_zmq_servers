#!/usr/bin/env python3
# -*- coding:utf-8 -*-
################################################################
# Copyright 2025 Dong Zhaorui. All rights reserved.
# Author: Dong Zhaorui 847235539@qq.com
# Date  : 2025-09-15
################################################################

from .hex_launch import HexLaunch, HexNodeConfig, HEX_LOG_LEVEL, hex_dict_str, hex_log, hex_err

from .device_base import HexDeviceBase
from .zmq_base import HexRate, hex_zmq_ts_now, hex_zmq_ts_delta_ms
from .zmq_base import HexSafeValue, HexZMQClientBase, HexZMQServerBase, hex_server_helper
from .zmq_base import HexZMQDummyClient, HexZMQDummyServer

from .robot import HexRobotBase, HexRobotClientBase, HexRobotServerBase
from .robot import HexRobotDummy, HexRobotDummyClient, HexRobotDummyServer
from .robot import HexRobotGello, HexRobotGelloClient, HexRobotGelloServer
from .robot import HexRobotHexarm, HexRobotHexarmClient, HexRobotHexarmServer, HEXARM_URDF_PATH_DICT

import os

file_dir = os.path.dirname(os.path.abspath(__file__))
HEX_ZMQ_SERVERS_PATH_DICT = {
    "zmq_dummy": f"{file_dir}/zmq_base.py",
    "robot_dummy": f"{file_dir}/robot/dummy/robot_dummy_srv.py",
    "robot_gello": f"{file_dir}/robot/gello/robot_gello_srv.py",
    "robot_hexarm": f"{file_dir}/robot/hexarm/robot_hexarm_srv.py",
}
HEX_ZMQ_CONFIGS_PATH_DICT = {
    "zmq_dummy": f"{file_dir}/config/zmq_dummy.json",
    "robot_dummy": f"{file_dir}/config/robot_dummy.json",
    "robot_gello": f"{file_dir}/config/robot_gello.json",
    "robot_hexarm": f"{file_dir}/config/robot_hexarm.json",
}

__all__ = [
    # version
    "__version__",

    # path
    "HEX_ZMQ_SERVERS_PATH_DICT",
    "HEX_ZMQ_CONFIGS_PATH_DICT",
    "HEXARM_URDF_PATH_DICT",

    # launch
    "HexLaunch",
    "HexNodeConfig",
    "HEX_LOG_LEVEL",
    "hex_dict_str",
    "hex_log",
    "hex_err",

    # base
    "HexDeviceBase",
    "HexRate",
    "hex_zmq_ts_now",
    "hex_zmq_ts_delta_ms",
    "HexSafeValue",
    "HexZMQClientBase",
    "HexZMQServerBase",
    "hex_server_helper",
    "HexZMQDummyClient",
    "HexZMQDummyServer",

    # robot
    "HexRobotBase",
    "HexRobotClientBase",
    "HexRobotServerBase",
    "HexRobotDummy",
    "HexRobotDummyClient",
    "HexRobotDummyServer",
    "HexRobotGello",
    "HexRobotGelloClient",
    "HexRobotGelloServer",
    "HexRobotHexarm",
    "HexRobotHexarmClient",
    "HexRobotHexarmServer",
]

# Check optional dependencies availability
from importlib.util import find_spec

_HAS_OPENCV = find_spec("cv2") is not None
_HAS_BERXEL = find_spec("berxel_py_wrapper") is not None
_HAS_MUJOCO = find_spec("mujoco") is not None

# Optional: camera
if _HAS_OPENCV and _HAS_BERXEL:
    from .cam import HexCamBase, HexCamClientBase, HexCamServerBase
    from .cam import HexCamDummy, HexCamDummyClient, HexCamDummyServer
    from .cam import HexCamBerxel, HexCamBerxelClient, HexCamBerxelServer
    HEX_ZMQ_SERVERS_PATH_DICT.update({
        "cam_dummy":
        f"{file_dir}/cam/dummy/cam_dummy_srv.py",
        "cam_berxel":
        f"{file_dir}/cam/berxel/cam_berxel_srv.py",
    })
    HEX_ZMQ_CONFIGS_PATH_DICT.update({
        "cam_dummy":
        f"{file_dir}/config/cam_dummy.json",
        "cam_berxel":
        f"{file_dir}/config/cam_berxel.json",
    })
    __all__.extend([
        # camera
        "HexCamBase",
        "HexCamClientBase",
        "HexCamServerBase",
        "HexCamDummy",
        "HexCamDummyClient",
        "HexCamDummyServer",
        "HexCamBerxel",
        "HexCamBerxelClient",
        "HexCamBerxelServer",
    ])

# Optional: mujoco
if _HAS_OPENCV and _HAS_MUJOCO:
    from .mujoco import HexMujocoBase, HexMujocoClientBase, HexMujocoServerBase
    from .mujoco import HexMujocoArcherY6, HexMujocoArcherY6Client, HexMujocoArcherY6Server
    from .mujoco import HexMujocoE3Desktop, HexMujocoE3DesktopClient, HexMujocoE3DesktopServer
    HEX_ZMQ_SERVERS_PATH_DICT.update({
        "mujoco_archer_y6":
        f"{file_dir}/mujoco/archer_y6/mujoco_archer_y6_srv.py",
        "mujoco_e3_desktop":
        f"{file_dir}/mujoco/e3_desktop/mujoco_e3_desktop_srv.py",
    })
    HEX_ZMQ_CONFIGS_PATH_DICT.update({
        "mujoco_archer_y6":
        f"{file_dir}/config/mujoco_archer_y6.json",
        "mujoco_e3_desktop":
        f"{file_dir}/config/mujoco_e3_desktop.json",
    })
    __all__.extend([
        # mujoco
        "HexMujocoBase",
        "HexMujocoClientBase",
        "HexMujocoServerBase",
        "HexMujocoArcherY6",
        "HexMujocoArcherY6Client",
        "HexMujocoArcherY6Server",
        "HexMujocoE3Desktop",
        "HexMujocoE3DesktopClient",
        "HexMujocoE3DesktopServer",
    ])

# print("#### Thanks for using hex_zmq_servers :D ####")
