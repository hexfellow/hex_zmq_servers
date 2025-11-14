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
from ..zmq_base import (
    hex_zmq_ts_now,
    HexSafeValue,
    HexZMQClientBase,
    HexZMQServerBase,
)

NET_CONFIG = {
    "ip": "127.0.0.1",
    "port": 12345,
    "client_timeout_ms": 200,
    "server_timeout_ms": 1_000,
    "server_num_workers": 4,
}

TAU = 2 * np.pi


class HexMujocoBase(HexDeviceBase):

    def __init__(self):
        HexDeviceBase.__init__(self)
        self._dofs = None
        self._limits = None
        self._intri = None

    def __del__(self):
        HexDeviceBase.__del__(self)

    def is_working(self) -> bool:
        return self._working.is_set()

    def get_dofs(self) -> np.ndarray:
        self._wait_for_working()
        return np.array(self._dofs, dtype=np.uint8)

    def get_limits(self) -> np.ndarray:
        self._wait_for_working()
        return self._limits

    def get_intri(self) -> np.ndarray:
        self._wait_for_working()
        return self._intri

    @staticmethod
    def _rads_normalize(rads: np.ndarray) -> np.ndarray:
        return (rads + np.pi) % TAU - np.pi

    @staticmethod
    def _apply_pos_limits(
        rads: np.ndarray,
        lower_bound: np.ndarray,
        upper_bound: np.ndarray,
    ) -> np.ndarray:
        normed_rads = HexMujocoBase._rads_normalize(rads)
        outside = (normed_rads < lower_bound) | (normed_rads > upper_bound)
        if not np.any(outside):
            return normed_rads

        lower_dist = np.fabs(
            HexMujocoBase._rads_normalize(
                (normed_rads - lower_bound)[outside]))
        upper_dist = np.fabs(
            HexMujocoBase._rads_normalize(
                (normed_rads - upper_bound)[outside]))
        choose_lower = lower_dist < upper_dist
        choose_upper = ~choose_lower

        outside_full = np.flatnonzero(outside)
        outside_lower = outside_full[choose_lower]
        outside_upper = outside_full[choose_upper]
        normed_rads[outside_lower] = lower_bound[outside_lower]
        normed_rads[outside_upper] = upper_bound[outside_upper]

        return normed_rads

    @abstractmethod
    def work_loop(self, hex_values: list[HexSafeValue | threading.Event]):
        raise NotImplementedError(
            "`work_loop` should be implemented by the child class")

    @abstractmethod
    def close(self):
        raise NotImplementedError(
            "`close` should be implemented by the child class")


class HexMujocoClientBase(HexZMQClientBase):

    def __init__(self, net_config: dict = NET_CONFIG):
        HexZMQClientBase.__init__(self, net_config)
        self._states_seq = 0
        self._obj_pose_seq = 0
        self._cmds_seq = 0
        self._rgb_seq = 0
        self._depth_seq = 0

    def __del__(self):
        HexZMQClientBase.__del__(self)

    def reset(self):
        self._states_seq = 0
        self._obj_pose_seq = 0
        self._cmds_seq = 0
        self._rgb_seq = 0
        self._depth_seq = 0

        hdr, _ = self.request({"cmd": "reset"})
        return hdr

    def seq_clear(self):
        clear_hdr, _ = self.request({"cmd": "seq_clear"})
        return clear_hdr

    def get_dofs(self):
        _, dofs = self.request({"cmd": "get_dofs"})
        return dofs

    def get_limits(self):
        _, limits = self.request({"cmd": "get_limits"})
        return limits

    def get_states(self, robot_name: str | None = None):
        req_cmd = "get_states"
        if robot_name is not None:
            req_cmd += f"_{robot_name}"
        hdr, states = self.request({
            "cmd":
            req_cmd,
            "args": (1 + self._states_seq) % self._max_seq_num,
        })
        try:
            cmd = hdr["cmd"]
            if cmd == f"{req_cmd}_ok":
                self._states_seq = hdr["args"]
                return hdr, states
            else:
                return None, None
        except KeyError:
            print(f"\033[91m{hdr['cmd']} requires `cmd`\033[0m")
            return None, None
        except Exception as e:
            print(f"\033[91m{req_cmd} failed: {e}\033[0m")
            return None, None

    def get_obj_pose(self):
        hdr, obj_pose = self.request({
            "cmd":
            "get_obj_pose",
            "args": (1 + self._obj_pose_seq) % self._max_seq_num,
        })
        try:
            cmd = hdr["cmd"]
            if cmd == "get_obj_pose_ok":
                self._obj_pose_seq = hdr["args"]
                return hdr, obj_pose
            else:
                return None, None
        except KeyError:
            print(f"\033[91m{hdr['cmd']} requires `cmd`\033[0m")
            return None, None
        except Exception as e:
            print(f"\033[91mget_obj_pose failed: {e}\033[0m")
            return None, None

    def set_cmds(
        self,
        cmds: np.ndarray,
        robot_name: str | None = None,
    ) -> bool:
        req_cmd = "set_cmds"
        if robot_name is not None:
            req_cmd += f"_{robot_name}"
        hdr, _ = self.request(
            {
                "cmd": req_cmd,
                "ts": hex_zmq_ts_now(),
                "args": self._cmds_seq,
            },
            cmds,
        )
        # print(f"{req_cmd} seq: {self._cmds_seq}")
        try:
            cmd = hdr["cmd"]
            if cmd == f"{req_cmd}_ok":
                self._cmds_seq = (self._cmds_seq + 1) % self._max_seq_num
                return True
            else:
                return False
        except KeyError:
            print(f"\033[91m{hdr['cmd']} requires `cmd`\033[0m")
            return False
        except Exception as e:
            print(f"\033[91m{req_cmd} failed: {e}\033[0m")
            return False

    def get_intri(self):
        intri_hdr, intri = self.request({"cmd": "get_intri"})
        return intri_hdr, intri

    def get_rgb(self, camera_name: str | None = None):
        return self._process_frame(camera_name, False)

    def get_depth(self, camera_name: str | None = None):
        return self._process_frame(camera_name, True)

    def _process_frame(
        self,
        camera_name: str | None = None,
        depth_flag: bool = False,
    ):
        req_cmd = f"get_{'depth' if depth_flag else 'rgb'}"
        if camera_name is not None:
            req_cmd += f"_{camera_name}"

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


class HexMujocoServerBase(HexZMQServerBase):

    def __init__(self, net_config: dict = NET_CONFIG):
        HexZMQServerBase.__init__(self, net_config)
        self._device: HexDeviceBase = None
        self._states_value = HexSafeValue()
        self._obj_pose_value = HexSafeValue()
        self._cmds_value = HexSafeValue()
        self._cmds_seq = -1
        self._rgb_value = HexSafeValue()
        self._depth_value = HexSafeValue()
        self._seq_clear_flag = False

    def work_loop(self):
        try:
            self._device.work_loop([
                self._states_value,
                self._obj_pose_value,
                self._cmds_value,
                self._rgb_value,
                self._depth_value,
                self._stop_event,
            ])
        finally:
            self._device.close()

    def _seq_clear(self):
        self._seq_clear_flag = True
        return True

    def _get_states(self, recv_hdr: dict):
        try:
            seq = recv_hdr["args"]
        except KeyError:
            print(f"\033[91m{recv_hdr['cmd']} requires `args`\033[0m")
            return {"cmd": f"{recv_hdr['cmd']}_failed"}, None

        try:
            ts, count, states = self._states_value.get()
        except Exception as e:
            print(f"\033[91m{recv_hdr['cmd']} failed: {e}\033[0m")
            return {"cmd": f"{recv_hdr['cmd']}_failed"}, None

        delta = (count - seq) % self._max_seq_num
        if delta >= 0 and delta < 1e6:
            return {
                "cmd": f"{recv_hdr['cmd']}_ok",
                "ts": ts,
                "args": count
            }, states
        else:
            return {"cmd": f"{recv_hdr['cmd']}_failed"}, None

    def _set_cmds(self, recv_hdr: dict, recv_buf: np.ndarray):
        seq = recv_hdr.get("args", None)
        if self._seq_clear_flag:
            self._seq_clear_flag = False
            self._cmds_seq = -1
            return self.no_ts_hdr(recv_hdr, False), None

        if seq is not None and seq > self._cmds_seq:
            delta = (seq - self._cmds_seq) % self._max_seq_num
            if delta >= 0 and delta < 1e6:
                self._cmds_seq = seq
                self._cmds_value.set((recv_hdr["ts"], seq, recv_buf))
                return self.no_ts_hdr(recv_hdr, True), None
            else:
                return self.no_ts_hdr(recv_hdr, False), None
        else:
            return self.no_ts_hdr(recv_hdr, False), None

    def _get_frame(self, recv_hdr: dict):
        try:
            seq = recv_hdr["args"]
        except KeyError:
            print(f"\033[91m{recv_hdr['cmd']} requires `args`\033[0m")
            return {"cmd": f"{recv_hdr['cmd']}_failed"}, None

        # get camera config
        split_cmd = recv_hdr["cmd"].split("_")
        depth_flag = split_cmd[1] == "depth"
        if depth_flag:
            value = self._depth_value
        else:
            value = self._rgb_value

        try:
            ts, count, img = value.get()
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
