#!/usr/bin/env python3
# -*- coding:utf-8 -*-
################################################################
# Copyright 2025 Dong Zhaorui. All rights reserved.
# Author: Dong Zhaorui 847235539@qq.com
# Date  : 2025-09-16
################################################################

import threading
import numpy as np
from abc import abstractmethod

from ..device_base import HexDeviceBase
from ..zmq_base import HexSafeValue, HexZMQClientBase, HexZMQServerBase

NET_CONFIG = {
    "ip": "127.0.0.1",
    "port": 12345,
    "client_timeout_ms": 200,
    "server_timeout_ms": 1_000,
    "server_num_workers": 4,
}


class HexCamBase(HexDeviceBase):

    def __init__(self):
        HexDeviceBase.__init__(self)

    def __del__(self):
        HexDeviceBase.__del__(self)

    @abstractmethod
    def work_loop(self, hex_values: list[HexSafeValue | threading.Event]):
        raise NotImplementedError(
            "`work_loop` should be implemented by the child class")

    @abstractmethod
    def close(self):
        raise NotImplementedError(
            "`close` should be implemented by the child class")


class HexCamClientBase(HexZMQClientBase):

    def __init__(self, net_config: dict = NET_CONFIG):
        HexZMQClientBase.__init__(self, net_config)
        self._rgb_seq = 0
        self._depth_seq = 0

    def __del__(self):
        HexZMQClientBase.__del__(self)

    def get_rgb(self):
        return self._process_frame(False)

    def get_depth(self):
        return self._process_frame(True)

    def _process_frame(self, depth_flag: bool):
        req_cmd = f"get_{'depth' if depth_flag else 'rgb'}"
        hdr, img = self.request({
            "cmd":
            req_cmd,
            "args": (1 + (self._depth_seq if depth_flag else self._rgb_seq)) %
            self._max_seq_num,
        })

        try:
            cmd = hdr["cmd"]
            if cmd == f"{req_cmd}_ok":
                if depth_flag:
                    self._depth_seq = hdr["args"]
                else:
                    self._rgb_seq = hdr["args"]
                return hdr, img
            else:
                return None, None
        except KeyError:
            print(f"\033[91m{hdr['cmd']} requires `cmd`\033[0m")
            return None, None
        except Exception as e:
            print(f"\033[91m__process_frame failed: {e}\033[0m")
            return None, None


class HexCamServerBase(HexZMQServerBase):

    def __init__(self, net_config: dict = NET_CONFIG):
        HexZMQServerBase.__init__(self, net_config)
        self._device: HexDeviceBase = None
        self._rgb_value = HexSafeValue()
        self._depth_value = HexSafeValue()

    def __del__(self):
        HexZMQServerBase.__del__(self)
        self._device.close()

    def work_loop(self):
        try:
            self._device.work_loop([
                self._rgb_value,
                self._depth_value,
                self._stop_event,
            ])
        finally:
            self._device.close()

    def _get_frame(self, recv_hdr: dict, depth_flag: bool):
        try:
            seq = recv_hdr["args"]
        except KeyError:
            print(f"\033[91m{recv_hdr['cmd']} requires `args`\033[0m")
            return {"cmd": f"{recv_hdr['cmd']}_failed"}, None

        try:
            if depth_flag:
                ts, count, img = self._depth_value.get()
            else:
                ts, count, img = self._rgb_value.get()
        except Exception as e:
            print(f"\033[91m{recv_hdr['cmd']} failed: {e}\033[0m")
            return {"cmd": f"{recv_hdr['cmd']}_failed"}, None

        delta = (count - seq) % self._max_seq_num
        if delta >= 0 and delta < 1e6:
            return {
                "cmd": f"{recv_hdr['cmd']}_ok",
                "ts": ts,
                "args": count
            }, img
        else:
            return {"cmd": f"{recv_hdr['cmd']}_failed"}, None

    @abstractmethod
    def _process_request(self, recv_hdr: dict, recv_buf: np.ndarray):
        raise NotImplementedError(
            "`_process_request` should be implemented by the child class")
