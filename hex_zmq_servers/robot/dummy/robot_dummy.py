#!/usr/bin/env python3
# -*- coding:utf-8 -*-
################################################################
# Copyright 2025 Dong Zhaorui. All rights reserved.
# Author: Dong Zhaorui 847235539@qq.com
# Date  : 2025-09-12
################################################################

import threading
import numpy as np

from ..robot_base import HexRobotBase
from ...zmq_base import (
    hex_zmq_ts_now,
    hex_zmq_ts_delta_ms,
    HexRate,
    HexSafeValue,
)
from ...hex_launch import hex_log, HEX_LOG_LEVEL

ROBOT_CONFIG = {
    "dofs": [7],
    "limits": [[[-1.0, 1.0]] * 3] * 7,
    "states_init": [[0.0, 0.0, 0.0]] * 7,
}


class HexRobotDummy(HexRobotBase):

    def __init__(
        self,
        robot_config: dict = ROBOT_CONFIG,
    ):
        HexRobotBase.__init__(self)

        try:
            self._dofs = robot_config["dofs"]
            self._limits = np.array(robot_config["limits"])
        except KeyError as ke:
            missing_key = ke.args[0]
            raise ValueError(
                f"robot_config is not valid, missing key: {missing_key}")

        # start work loop
        self._working.set()

    def __del__(self):
        HexRobotBase.__del__(self)

    def work_loop(self, hex_values: list[HexSafeValue | threading.Event]):
        states_value = hex_values[0]
        cmds_value = hex_values[1]
        stop_event = hex_values[2]

        dummy_states = np.zeros((self._dofs[0], 3))
        states_count = 0
        last_cmds_seq = -1
        rate = HexRate(1000)
        while self._working.is_set() and not stop_event.is_set():
            # states
            states_value.set((hex_zmq_ts_now(), states_count, dummy_states))
            states_count = (states_count + 1) % self._max_seq_num

            # cmds
            cmds_pack = cmds_value.get(timeout_s=-1.0)
            if cmds_pack is not None:
                ts, seq, cmds = cmds_pack
                if seq != last_cmds_seq:
                    last_cmds_seq = seq
                    if hex_zmq_ts_delta_ms(hex_zmq_ts_now(), ts) < 200.0:
                        cmds = np.clip(
                            cmds,
                            self._limits[:, :, 0],
                            self._limits[:, :, 1],
                        )
                        dummy_states = cmds.copy()

            # sleep
            rate.sleep()

        # close
        self.close()

    def close(self):
        if not self._working.is_set():
            return
        self._working.clear()
        hex_log(HEX_LOG_LEVEL["info"], "HexRobotDummy closed")
