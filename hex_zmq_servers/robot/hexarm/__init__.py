#!/usr/bin/env python3
# -*- coding:utf-8 -*-
################################################################
# Copyright 2025 Dong Zhaorui. All rights reserved.
# Author: Dong Zhaorui 847235539@qq.com
# Date  : 2025-09-12
################################################################

from .robot_hexarm import HexRobotHexarm
from .robot_hexarm_cli import HexRobotHexarmClient
from .robot_hexarm_srv import HexRobotHexarmServer

import os

urdf_dir = os.path.join(os.path.dirname(__file__), "urdf")
HEXARM_URDF_PATH_DICT = {
    "archer_y6_empty":
    f"{urdf_dir}/archer_y6/empty.urdf",
    "archer_y6_gp100":
    f"{urdf_dir}/archer_y6/gp100.urdf",
    "archer_y6_gp100_handle":
    f"{urdf_dir}/archer_y6/gp100_handle.urdf",
    "archer_y6_gp100_p050":
    f"{urdf_dir}/archer_y6/gp100_p050.urdf",
    "archer_y6_gp100_p050_handle":
    f"{urdf_dir}/archer_y6/gp100_p050_handle.urdf",
    "archer_l6y_empty":
    f"{urdf_dir}/archer_l6y/empty.urdf",
    "archer_l6y_gp100":
    f"{urdf_dir}/archer_l6y/gp100.urdf",
    "archer_l6y_gp100_handle":
    f"{urdf_dir}/archer_l6y/gp100_handle.urdf",
    "archer_l6y_gp100_p050":
    f"{urdf_dir}/archer_l6y/gp100_p050.urdf",
    "archer_l6y_gp100_p050_handle":
    f"{urdf_dir}/archer_l6y/gp100_p050_handle.urdf",
}

__all__ = [
    # path
    "HEXARM_URDF_PATH_DICT",

    # robot
    "HexRobotHexarm",
    "HexRobotHexarmClient",
    "HexRobotHexarmServer",
]
