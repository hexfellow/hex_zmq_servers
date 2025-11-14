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

from ..robot_base import HexRobotBase
from ...zmq_base import (
    hex_zmq_ts_now,
    hex_zmq_ts_delta_ms,
    HexRate,
    HexSafeValue,
)
from ...hex_launch import hex_log, HEX_LOG_LEVEL
from hex_device import HexDeviceApi, MotorBase
from hex_device.motor_base import CommandType

ROBOT_CONFIG = {
    "device_ip": "172.18.8.161",
    "device_port": 8439,
    "control_hz": 250,
    "arm_type": "archer_d6y",
    "use_gripper": True,
    "mit_kp": [200.0, 200.0, 200.0, 75.0, 15.0, 15.0, 20.0],
    "mit_kd": [12.5, 12.5, 12.5, 6.0, 0.31, 0.31, 1.0],
    "sens_ts": True,
}

HEX_DEVICE_TYPE_DICT = {
    "archer_d6y": 16,
    "archer_l6y": 17,
}


class HexRobotHexarm(HexRobotBase):

    def __init__(
        self,
        robot_config: dict = ROBOT_CONFIG,
    ):
        HexRobotBase.__init__(self)

        try:
            device_ip = robot_config["device_ip"]
            device_port = robot_config["device_port"]
            control_hz = robot_config["control_hz"]
            arm_type = HEX_DEVICE_TYPE_DICT[robot_config["arm_type"]]
            use_gripper = robot_config["use_gripper"]
            self.__sens_ts = robot_config["sens_ts"]
        except KeyError as ke:
            missing_key = ke.args[0]
            raise ValueError(
                f"robot_config is not valid, missing key: {missing_key}")

        self.__mit_kp = robot_config.get(
            "mit_kp",
            [200.0, 200.0, 200.0, 75.0, 15.0, 15.0, 20.0],
        )
        self.__mit_kd = robot_config.get(
            "mit_kd",
            [12.5, 12.5, 12.5, 6.0, 0.31, 0.31, 1.0],
        )

        # variables
        # hex_arm variables
        self.__hex_api: HexDeviceApi | None = None
        self.__arm_archer: MotorBase | None = None
        self.__gripper: MotorBase | None = None

        # open device
        self.__hex_api = HexDeviceApi(
            ws_url=f"ws://{device_ip}:{device_port}",
            control_hz=control_hz,
        )

        # open arm
        while self.__hex_api.find_device_by_robot_type(arm_type) is None:
            print("\033[33mArm not found\033[0m")
            time.sleep(1)
        self.__arm_archer = self.__hex_api.find_device_by_robot_type(arm_type)
        self.__arm_archer.start()
        self.__arm_archer.command_timeout_check(False)
        self.__arm_dofs = len(self.__arm_archer)
        self._limits = self.__arm_archer.get_joint_limits()

        # try to open gripper
        self.__gripper_dofs = 0
        self.__gripper = None
        if use_gripper:
            self.__gripper = self.__hex_api.find_optional_device_by_id(1)
            if self.__gripper is not None:
                self.__gripper_dofs = len(self.__gripper)
                self._limits += [self.__gripper.get_joint_limits()]
            else:
                print("\033[33mGripper not found\033[0m")

        # modify variables
        self._dofs = [self.__arm_dofs + self.__gripper_dofs]
        self._limits = np.ascontiguousarray(np.asarray(self._limits)).reshape(
            self._dofs[0], 3, 2)
        self.__mit_kp = np.ascontiguousarray(np.asarray(self.__mit_kp))
        self.__mit_kd = np.ascontiguousarray(np.asarray(self.__mit_kd))
        if self.__mit_kp.shape[0] < self._dofs[0] or self.__mit_kd.shape[
                0] < self._dofs[0]:
            raise ValueError(
                "The length of mit_kp and mit_kd must be greater than or equal to the number of motors"
            )
        elif self.__mit_kp.shape[0] > self._dofs[0] or self.__mit_kd.shape[
                0] > self._dofs[0]:
            print(
                f"\033[33mThe length of mit_kp and mit_kd is greater than the number of motors\033[0m"
            )
            self.__mit_kp = self.__mit_kp[:self._dofs[0]]
            self.__mit_kd = self.__mit_kd[:self._dofs[0]]

        # start work loop
        self._working.set()

    def work_loop(self, hex_values: list[HexSafeValue | threading.Event]):
        states_value = hex_values[0]
        cmds_value = hex_values[1]
        stop_event = hex_values[2]

        last_states_ts = hex_zmq_ts_now()
        states_count = 0
        last_cmds_seq = -1
        rate = HexRate(1000)
        while self._working.is_set() and not stop_event.is_set():
            # states
            ts, states = self.__get_states()
            if states is not None:
                if hex_zmq_ts_delta_ms(ts, last_states_ts) > 1.0:
                    last_states_ts = ts
                    states_value.set((ts, states_count, states))
                    states_count = (states_count + 1) % self._max_seq_num

            # cmds
            cmds_pack = cmds_value.get(timeout_s=-1.0)
            if cmds_pack is not None:
                ts, seq, cmds = cmds_pack
                if seq != last_cmds_seq:
                    last_cmds_seq = seq
                    if hex_zmq_ts_delta_ms(hex_zmq_ts_now(), ts) < 200.0:
                        self.__set_cmds(cmds)

            # sleep
            rate.sleep()

        # close
        self.close()

    def __get_states(self) -> tuple[np.ndarray | None, dict | None]:
        if self.__arm_archer is None:
            return None, None

        # (arm_dofs, 3) # pos vel eff
        arm_states_dict = self.__arm_archer.get_simple_motor_status()
        pos = arm_states_dict['pos']
        vel = arm_states_dict['vel']
        eff = arm_states_dict['eff']
        ts = arm_states_dict['ts']

        # (gripper_dofs, 3) # pos vel eff
        if self.__gripper is not None:
            gripper_states_dict = self.__gripper.get_simple_motor_status()
            pos += gripper_states_dict['pos']
            vel += gripper_states_dict['vel']
            eff += gripper_states_dict['eff']

        pos, vel, eff = np.asarray(pos), np.asarray(vel), np.asarray(eff)
        return ts if self.__sens_ts else hex_zmq_ts_now(), np.array(
            [pos, vel, eff]).T

    def __set_cmds(self, cmds: np.ndarray) -> bool:
        # cmds: (n)
        # [pos_0, ..., pos_n]
        # cmds: (n, 2)
        # [[pos_0, tor_0], ..., [pos_n, tor_n]]
        # cmds: (n, 5)
        # [[pos_0, vel_0, tor_0, kp_0, kd_0], ..., [pos_n, vel_n, tor_n, kp_n, kd_n]]
        if self.__arm_archer is None:
            print("\033[91mArm not found\033[0m")
            return False

        if cmds.shape[0] < self._dofs[0]:
            print(
                "\033[91mThe length of joint_angles must be greater than or equal to the number of motors\033[0m"
            )
            return False
        elif cmds.shape[0] > self._dofs[0]:
            print(
                f"\033[33mThe length of joint_angles is greater than the number of motors\033[0m"
            )
            cmds = cmds[:self._dofs[0]]

        cmd_pos = None
        tar_vel = np.zeros(self._dofs[0])
        cmd_tor = np.zeros(self._dofs[0])
        cmd_kp = self.__mit_kp.copy()
        cmd_kd = self.__mit_kd.copy()
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
        mit_cmd = self.__arm_archer.construct_mit_command(
            tar_pos[:self.__arm_dofs],
            tar_vel[:self.__arm_dofs],
            cmd_tor[:self.__arm_dofs],
            cmd_kp[:self.__arm_dofs],
            cmd_kd[:self.__arm_dofs],
        )
        self.__arm_archer.motor_command(CommandType.MIT, mit_cmd)

        # gripper
        if self.__gripper is not None:
            mit_cmd = self.__gripper.construct_mit_command(
                tar_pos[self.__arm_dofs:],
                tar_vel[self.__arm_dofs:],
                cmd_tor[self.__arm_dofs:],
                cmd_kp[self.__arm_dofs:],
                cmd_kd[self.__arm_dofs:],
            )
            self.__gripper.motor_command(CommandType.MIT, mit_cmd)

        return True

    def close(self):
        if not self._working.is_set():
            return
        self._working.clear()
        self.__arm_archer.stop()
        self.__hex_api.close()
        hex_log(HEX_LOG_LEVEL["info"], "HexRobotHexarm closed")
