#!/usr/bin/env python3
# -*- coding:utf-8 -*-
################################################################
# Copyright 2025 Dong Zhaorui. All rights reserved.
# Author: Dong Zhaorui 847235539@qq.com
# Date  : 2025-09-16
################################################################

import threading
from abc import ABC, abstractmethod

from .zmq_base import MAX_SEQ_NUM, HexSafeValue


class HexDeviceBase(ABC):

    def __init__(self):
        # variables
        self._max_seq_num = MAX_SEQ_NUM
        # thread
        self._working = threading.Event()

    def __del__(self):
        self.close()

    def is_working(self) -> bool:
        return self._working.is_set()

    def _wait_for_working(self):
        while not self._working.is_set():
            print("waiting for device to work")
            self._working.wait(0.1)

    @abstractmethod
    def work_loop(self, hex_values: list[HexSafeValue | threading.Event]):
        raise NotImplementedError(
            "`work_loop` should be implemented by the child class")

    @abstractmethod
    def close(self):
        raise NotImplementedError(
            "`close` should be implemented by the child class")
