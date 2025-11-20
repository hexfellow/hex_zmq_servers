#!/usr/bin/env python3
# -*- coding:utf-8 -*-
################################################################
# Copyright 2025 Dong Zhaorui. All rights reserved.
# Author: Dong Zhaorui 847235539@qq.com
# Date  : 2025-09-12
################################################################

import threading
import numpy as np

from ..cam_base import HexCamBase
from ...zmq_base import (
    hex_zmq_ts_now,
    HexRate,
    HexSafeValue,
)
from ...hex_launch import hex_log, HEX_LOG_LEVEL


class HexCamDummy(HexCamBase):

    def __init__(self, params_config: dict = {}):
        HexCamBase.__init__(self)
        self._working.set()

    def __del__(self):
        HexCamBase.__del__(self)

    def work_loop(self, hex_values: list[HexSafeValue | threading.Event]):
        rgb_value = hex_values[0]
        depth_value = hex_values[1]
        stop_event = hex_values[2]

        rgb_count = 0
        depth_count = 0
        rate = HexRate(60)
        while self._working.is_set() and not stop_event.is_set():
            # rgb
            rgb_img = np.random.randint(
                0,
                255,
                (480, 640, 3),
                dtype=np.uint8,
            )
            rgb_value.set((hex_zmq_ts_now(), rgb_count, rgb_img))
            rgb_count = (rgb_count + 1) % self._max_seq_num

            # depth
            depth_img = np.random.randint(
                0,
                65535,
                (480, 640),
                dtype=np.uint16,
            )
            depth_value.set((hex_zmq_ts_now(), depth_count, depth_img))
            depth_count = (depth_count + 1) % self._max_seq_num

            # sleep
            rate.sleep()

        # close
        self.close()

    def close(self):
        if not self._working.is_set():
            return
        self._working.clear()
        hex_log(HEX_LOG_LEVEL["info"], "HexCamDummy closed")
