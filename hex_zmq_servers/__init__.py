#!/usr/bin/env python3
# -*- coding:utf-8 -*-
################################################################
# Copyright 2025 Dong Zhaorui. All rights reserved.
# Author: Dong Zhaorui 847235539@qq.com
# Date  : 2025-09-15
################################################################

from .hex_launch import HexLaunch, HEX_LOG_LEVEL, hex_log, hex_err

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
    "HEX_LOG_LEVEL",
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

# Optional: camera
try:
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
except ImportError:
    # berxel_py_wrapper not installed
    # Install with: pip install hex_zmq_servers[berxel] or pip install hex_zmq_servers[all]
    pass

# Optional: mujoco
try:
    from .mujoco import HexMujocoBase, HexMujocoClientBase, HexMujocoServerBase
    from .mujoco import HexMujocoArcherD6y, HexMujocoArcherD6yClient, HexMujocoArcherD6yServer
    from .mujoco import HexMujocoE3Desktop, HexMujocoE3DesktopClient, HexMujocoE3DesktopServer
    HEX_ZMQ_SERVERS_PATH_DICT.update({
        "mujoco_archer_d6y":
        f"{file_dir}/mujoco/archer_d6y/mujoco_archer_d6y_srv.py",
        "mujoco_e3_desktop":
        f"{file_dir}/mujoco/e3_desktop/mujoco_e3_desktop_srv.py",
    })
    HEX_ZMQ_CONFIGS_PATH_DICT.update({
        "mujoco_archer_d6y":
        f"{file_dir}/config/mujoco_archer_d6y.json",
        "mujoco_e3_desktop":
        f"{file_dir}/config/mujoco_e3_desktop.json",
    })
    __all__.extend([
        # mujoco
        "HexMujocoBase",
        "HexMujocoClientBase",
        "HexMujocoServerBase",
        "HexMujocoArcherD6y",
        "HexMujocoArcherD6yClient",
        "HexMujocoArcherD6yServer",
        "HexMujocoE3Desktop",
        "HexMujocoE3DesktopClient",
        "HexMujocoE3DesktopServer",
    ])
except ImportError:
    # mujoco not installed
    # Install with: pip install hex_zmq_servers[mujoco] or pip install hex_zmq_servers[all]
    pass

# print("#### Thanks for using hex_zmq_servers :D ####")
