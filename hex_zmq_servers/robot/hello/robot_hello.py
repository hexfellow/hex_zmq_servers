#!/usr/bin/env python3
# -*- coding:utf-8 -*-
################################################################
# Copyright 2025 Dong Zhaorui. All rights reserved.
# Author: Dong Zhaorui 847235539@qq.com
# Date  : 2025-09-14
################################################################

import time
import threading
import numpy as np
from collections import deque

from ..robot_base import HexRobotBase
from ...hex_launch import hex_log, HEX_LOG_LEVEL

from hex_robo_utils import (HexRate, hex_ts_delta_ms, hex_ts_now)
from hex_device import HexDeviceApi, Arm, Hands
from hex_device.motor_base import CommandType
import hex_device

ROBOT_CONFIG = {
    "device_ip": "172.18.8.161",
    "device_port": 8439,
    "control_hz": 250,
    "arm_type": "archer_y6",
    "sens_ts": True,
}

HELLO_DEVICE_TYPE_DICT = {
    # 6 dof
    "archer_y6": 26,
    "archer_d6y": 26,
    "archer_l6y": 26,
    "firefly_y6": 26,
}


class HexRobotHello(HexRobotBase):

    def __init__(
        self,
        robot_config: dict = ROBOT_CONFIG,
        realtime_mode: bool = False,
    ):
        HexRobotBase.__init__(self, realtime_mode)
        hex_device.set_log_level("ERROR")

        try:
            device_ip = robot_config["device_ip"]
            device_port = robot_config["device_port"]
            control_hz = robot_config["control_hz"]
            arm_type = HELLO_DEVICE_TYPE_DICT[robot_config["arm_type"]]
            self.__sens_ts = robot_config["sens_ts"]
        except KeyError as ke:
            missing_key = ke.args[0]
            raise ValueError(
                f"robot_config is not valid, missing key: {missing_key}")

        # variables
        # hex_arm variables
        self.__hex_api: HexDeviceApi | None = None
        self.__arm: Arm | None = None
        self.__gripper: Hands | None = None

        # buffer
        self.__arm_state_buffer: dict | None = None
        self.__gripper_state_buffer: dict | None = None

        # open device
        self.__hex_api = HexDeviceApi(
            ws_url=f"ws://{device_ip}:{device_port}",
            control_hz=control_hz,
        )

        # open arm
        while self.__hex_api.find_device_by_robot_type(arm_type) is None:
            print("\033[33mArm not found\033[0m")
            time.sleep(1)
        self.__arm = self.__hex_api.find_device_by_robot_type(arm_type)
        self.__arm.start()

        # try to open gripper
        self.__gripper = self.__hex_api.find_optional_device_by_id(1)
        if self.__gripper is None:
            print("\033[33mGripper not found\033[0m")
        self.__gripper.set_rgb_stripe_command([0] * 6, [255] * 6, [0] * 6)

        # variables init
        arm_dofs = len(self.__arm)
        self._dofs = [arm_dofs]
        self._limits = np.array(self.__arm.get_joint_limits()).reshape(
            -1, 3, 2)
        self.__motor_idx = {"robot_arm": np.arange(arm_dofs).tolist()}
        if self.__gripper is not None:
            gripper_dofs = len(self.__gripper)
            self._dofs.append(gripper_dofs)
            gripper_limits = np.array(
                self.__gripper.get_joint_limits()).reshape(-1, 3, 2)
            self._limits = np.concatenate([self._limits, gripper_limits],
                                          axis=0)
            self.__motor_idx["robot_gripper"] = (np.arange(gripper_dofs) +
                                                 arm_dofs).tolist()

        # modify variables
        self._dofs = np.array(self._dofs)
        self._dofs_sum = self._dofs.sum()
        self._limits = np.ascontiguousarray(np.asarray(self._limits)).reshape(
            self._dofs_sum, 3, 2)

        # start work loop
        self._working.set()

    def work_loop(self, hex_queues: list[deque | threading.Event]):
        states_queue = hex_queues[0]
        rgbs_queue = hex_queues[1]
        stop_event = hex_queues[2]

        last_states_ts = hex_ts_now()
        states_count = 0
        cmds_count = 0
        cmds = np.zeros((self._dofs_sum, 5))
        last_rgbs_seq = -1
        rate = HexRate(2000)
        while self._working.is_set() and not stop_event.is_set():
            # states
            ts, states = self.__get_states()
            if states is not None:
                if hex_ts_delta_ms(ts, last_states_ts) > 1e-6:
                    last_states_ts = ts
                    states_queue.append((ts, states_count, states))
                    states_count = (states_count + 1) % self._max_seq_num

            # cmds
            cmds_count += 1
            if cmds_count >= 1000:
                cmds_count = 0
                self.__set_cmds(cmds)

            # rgbs
            rgbs_pack = None
            try:
                rgbs_pack = rgbs_queue[
                    -1] if self._realtime_mode else rgbs_queue.popleft()
            except IndexError:
                pass
            if rgbs_pack is not None:
                ts, seq, rgbs = rgbs_pack
                if seq != last_rgbs_seq:
                    last_rgbs_seq = seq
                    if hex_ts_delta_ms(hex_ts_now(), ts) < 200.0:
                        self.__set_rgbs(rgbs)

            # sleep
            rate.sleep()

        # close
        self.close()

    def __get_states(self) -> tuple[np.ndarray | None, dict | None]:
        if self.__arm is None:
            return None, None

        # (arm_dofs, 3) # pos vel eff
        self.__arm_state_buffer = self.__arm.get_simple_motor_status()

        # (gripper_dofs, 3) # pos vel eff
        if self.__gripper is not None:
            self.__gripper_state_buffer = self.__gripper.get_simple_motor_status(
            )

        arm_ready = self.__arm_state_buffer is not None
        gripper_ready = self.__gripper is None or self.__gripper_state_buffer is not None
        if arm_ready and gripper_ready:
            arm_ts = self.__arm_state_buffer['ts']
            gripper_ts = self.__gripper_state_buffer[
                'ts'] if self.__gripper is not None else arm_ts

            delta_ms = hex_ts_delta_ms(arm_ts, gripper_ts)
            if np.fabs(delta_ms) < 1e-6:
                pos = self.__arm_state_buffer['pos']
                vel = self.__arm_state_buffer['vel']
                eff = self.__arm_state_buffer['eff']

                if self.__gripper is not None:
                    pos = np.concatenate(
                        [pos, self.__gripper_state_buffer['pos']])
                    vel = np.concatenate(
                        [vel, self.__gripper_state_buffer['vel']])
                    eff = np.concatenate(
                        [eff, self.__gripper_state_buffer['eff']])

                state = np.array([pos, vel, eff]).T
                self.__arm_state_buffer, self.__gripper_state_buffer = None, None
                return arm_ts if self.__sens_ts else hex_ts_now(), state
            elif delta_ms > 0.0:
                self.__gripper_state_buffer = None
                return None, None
            else:
                self.__arm_state_buffer = None
                return None, None

        return None, None

    def __set_cmds(self, cmds: np.ndarray) -> bool:
        # cmds: (n)
        # [pos_0, ..., pos_n]
        # cmds: (n, 2)
        # [[pos_0, tor_0], ..., [pos_n, tor_n]]
        # cmds: (n, 5)
        # [[pos_0, vel_0, tor_0, kp_0, kd_0], ..., [pos_n, vel_n, tor_n, kp_n, kd_n]]
        if self.__arm is None:
            print("\033[91mArm not found\033[0m")
            return False

        if cmds.shape[0] < self._dofs_sum:
            print(
                "\033[91mThe length of joint_angles must be greater than or equal to the number of motors\033[0m"
            )
            return False
        elif cmds.shape[0] > self._dofs_sum:
            print(
                f"\033[33mThe length of joint_angles is greater than the number of motors\033[0m"
            )
            cmds = cmds[:self._dofs_sum]

        cmd_pos = None
        tar_vel = np.zeros(self._dofs_sum)
        cmd_tor = np.zeros(self._dofs_sum)
        cmd_kp = np.zeros(self._dofs_sum)
        cmd_kd = np.zeros(self._dofs_sum)
        if len(cmds.shape) == 1:
            cmd_pos = cmds
        elif len(cmds.shape) == 2:
            if cmds.shape[1] == 2:
                cmd_pos = cmds[:, 0]
                cmd_tor = cmds[:, 1]
            elif cmds.shape[1] == 5:
                cmd_pos = cmds[:, 0]
                tar_vel = cmds[:, 1]
                cmd_tor = cmds[:, 2]
                cmd_kp = cmds[:, 3]
                cmd_kd = cmds[:, 4]
            else:
                raise ValueError(f"The shape of cmds is invalid: {cmds.shape}")
        else:
            raise ValueError(f"The shape of cmds is invalid: {cmds.shape}")
        tar_pos = self._apply_pos_limits(
            cmd_pos,
            self._limits[:, 0, 0],
            self._limits[:, 0, 1],
        )

        # arm
        arm_cmd = self.__arm.construct_mit_command(
            tar_pos[self.__motor_idx["robot_arm"]],
            tar_vel[self.__motor_idx["robot_arm"]],
            cmd_tor[self.__motor_idx["robot_arm"]],
            cmd_kp[self.__motor_idx["robot_arm"]],
            cmd_kd[self.__motor_idx["robot_arm"]],
        )
        self.__arm.motor_command(CommandType.MIT, arm_cmd)

        # gripper
        if self.__gripper is not None:
            gripper_cmd = self.__gripper.construct_mit_command(
                tar_pos[self.__motor_idx["robot_gripper"]],
                tar_vel[self.__motor_idx["robot_gripper"]],
                cmd_tor[self.__motor_idx["robot_gripper"]],
                cmd_kp[self.__motor_idx["robot_gripper"]],
                cmd_kd[self.__motor_idx["robot_gripper"]],
            )
            self.__gripper.motor_command(CommandType.MIT, gripper_cmd)

        return True

    def __set_rgbs(self, rgbs: np.ndarray) -> bool:
        if self.__gripper is None:
            print("\033[91mGripper not found\033[0m")
            return False

        rgbs_int = rgbs.astype(int)
        rgbs_shape = rgbs_int.shape
        rgbs_dim = len(rgbs_shape)
        if rgbs_dim == 1:
            if rgbs_shape[0] != 3:
                print("\033[91mThe shape of rgbs is invalid\033[0m")
                return False
            rgbs_int = rgbs_int.reshape(1, 3)
            rgbs_int = np.tile(rgbs_int, (6, 1))
        elif rgbs_dim == 2 and rgbs_shape[1] != 3:
            print("\033[91mThe shape of rgbs is invalid\033[0m")
            return False

        self.__gripper.set_rgb_stripe_command(
            rgbs_int[:, 0].tolist(),
            rgbs_int[:, 1].tolist(),
            rgbs_int[:, 2].tolist(),
        )
        return True

    def close(self):
        if not self._working.is_set():
            return
        self._working.clear()
        self.__gripper.set_rgb_stripe_command([255] * 6, [0] * 6, [0] * 6)
        time.sleep(0.2)
        self.__arm.stop()
        self.__hex_api.close()
        hex_log(HEX_LOG_LEVEL["info"], "HexRobotHello closed")
