#!/usr/bin/env python3
# -*- coding:utf-8 -*-
################################################################
# Copyright 2025 Dong Zhaorui. All rights reserved.
# Author: Dong Zhaorui 847235539@qq.com
# Date  : 2025-09-12
################################################################

import os
import subprocess
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
from dynamixel_sdk.group_sync_read import GroupSyncRead
from dynamixel_sdk.group_sync_write import GroupSyncWrite
from dynamixel_sdk.packet_handler import PacketHandler
from dynamixel_sdk.port_handler import PortHandler
from dynamixel_sdk.robotis_def import (
    COMM_SUCCESS,
    DXL_HIBYTE,
    DXL_HIWORD,
    DXL_LOBYTE,
    DXL_LOWORD,
)

DYNAMIXEL_TORQUE_ENABLE_ADDR = 64
DYNAMIXEL_TORQUE_ENABLE_VAL = 1
DYNAMIXEL_TORQUE_DISABLE_VAL = 0
DYNAMIXEL_GOAL_POSITION_ADDR = 116
DYNAMIXEL_GOAL_POSITION_LEN = 4
DYNAMIXEL_PRESENT_POSITION_ADDR = 132
DYNAMIXEL_PRESENT_POSITION_LEN = 4

ROBOT_CONFIG = {
    "idxs": [0, 1, 2, 3, 4, 5, 6],
    "invs": [1.0, -1.0, 1.0, 1.0, -1.0, -4.0],
    "limits": [[[-2.7, 2.7], [-1.57, 2.09], [0, 3.14], [-1.57, 1.57],
                [-1.57, 1.57], [-1.57, 1.57], [0.0, 1.0]]],
    "device":
    "/dev/ttyUSB0",
    "baudrate":
    115200,
    "max_retries":
    3,
    "torque_enabled":
    False,
    "sens_ts":
    True,
}


class HexRobotGello(HexRobotBase):

    def __init__(
        self,
        robot_config: dict = ROBOT_CONFIG,
    ):
        HexRobotBase.__init__(self)

        try:
            self.__idxs = np.array(robot_config["idxs"])
            self.__invs = np.array(robot_config["invs"])
            self._limits = np.array(robot_config["limits"])
            self.__device = robot_config["device"]
            self.__baudrate = robot_config["baudrate"]
            self.__max_retries = robot_config["max_retries"]
            self.__torque_enabled = robot_config["torque_enabled"]
            self.__sens_ts = robot_config["sens_ts"]
        except KeyError as ke:
            missing_key = ke.args[0]
            raise ValueError(
                f"robot_config is not valid, missing key: {missing_key}")

        # variables
        # gello variables
        self.__servo_to_rad = np.pi / 2048
        self.__port_handler = None
        self.__packet_handler = None
        self.__group_sync_read = None
        self.__group_sync_write = None
        self.__lock = threading.Lock()
        # robot variables
        self._dofs = [self.__idxs.shape[0]]

        # open device
        for attempt in range(self.__max_retries):
            print(
                f"Attempting to initialize Dynamixel driver (attempt {attempt + 1}/{self.__max_retries})"
            )
            if self.__try_open_device():
                break
            else:
                time.sleep(1.0)

        # start work loop
        self._working.set()

    def work_loop(self, hex_values: list[HexSafeValue | threading.Event]):
        states_value = hex_values[0]
        cmds_value = hex_values[1]
        stop_event = hex_values[2]

        states_count = 0
        last_cmds_seq = -1
        rate = HexRate(1000)
        while self._working.is_set() and not stop_event.is_set():
            # states
            ts, states = self.__get_states()
            if states is not None:
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

    def __get_states(self):
        with self.__lock:
            ts = hex_zmq_ts_now()
            servo_values = np.zeros(self._dofs, dtype=int)
            dxl_comm_result = self.__group_sync_read.txRxPacket()
            if dxl_comm_result != COMM_SUCCESS:
                print(f"warning, comm failed: {dxl_comm_result}")
                return None, None
            for i, dxl_id in enumerate(self.__idxs):
                if self.__group_sync_read.isAvailable(
                        dxl_id, DYNAMIXEL_PRESENT_POSITION_ADDR,
                        DYNAMIXEL_PRESENT_POSITION_LEN):
                    servo_value = self.__group_sync_read.getData(
                        dxl_id, DYNAMIXEL_PRESENT_POSITION_ADDR,
                        DYNAMIXEL_PRESENT_POSITION_LEN)
                    servo_value = np.int32(np.uint32(servo_value))
                    servo_values[i] = servo_value
                else:
                    raise RuntimeError(
                        f"Failed to get joint angles for Dynamixel with ID {dxl_id}"
                    )

            rads = self._apply_pos_limits(
                servo_values * self.__servo_to_rad * self.__invs,
                self._limits[:, 0],
                self._limits[:, 1],
            )
            return ts if self.__sens_ts else hex_zmq_ts_now(), rads

    def __set_cmds(self, cmds: np.ndarray):
        if len(cmds) != len(self.__idxs):
            print(
                "\033[91mThe length of joint_angles must match the number of servos\033[0m"
            )
            return False
        if not self.__torque_enabled:
            print("\033[91mTorque must be enabled to set joint angles\033[0m")
            return False

        for dxl_id, cmd_rad in zip(self.__idxs, cmds):
            # Convert the angle to the appropriate value for the servo
            position_value = int(cmd_rad / self.__servo_to_rad)

            # Allocate goal position value into byte array
            param_goal_position = [
                DXL_LOBYTE(DXL_LOWORD(position_value)),
                DXL_HIBYTE(DXL_LOWORD(position_value)),
                DXL_LOBYTE(DXL_HIWORD(position_value)),
                DXL_HIBYTE(DXL_HIWORD(position_value)),
            ]

            # Add goal position value to the Syncwrite parameter storage
            dxl_addparam_result = self.__group_sync_write.addParam(
                dxl_id, param_goal_position)
            if not dxl_addparam_result:
                print(
                    f"\033[91mFailed to set joint angle for Dynamixel with ID {dxl_id}\033[0m"
                )
                return False

        # Syncwrite goal position
        dxl_comm_result = self.__group_sync_write.txPacket()
        if dxl_comm_result != COMM_SUCCESS:
            print(f"\033[91mFailed to syncwrite goal position\033[0m")
            return False

        # Clear syncwrite parameter storage
        self.__group_sync_write.clearParam()

        return True

    def __try_open_device(self):
        if not self.__check_device_availability():
            print("Port is busy, attempting to free it...")
            if not self.__kill_processes_using_device():
                print("Failed to free device, trying to fix permissions...")
                self.__fix_device_permissions()
            time.sleep(2)

        try:
            self.__initialize_hardware()
            print(
                f"Successfully initialized Dynamixel driver on {self.__device}"
            )
            return True
        except Exception as e:
            print(f"Failed to initialize Dynamixel driver: {e}")
            if "Permission denied" in str(e):
                print(
                    "Please add permission to the device. For more details, please refer to the \033[0;31mhttps://docs.hexfellow.com\033[0m"
                )
                return False
            return False

    def __check_device_availability(self):
        try:
            # Check if port exists
            if not os.path.exists(self.__device):
                print(f"Device {self.__device} does not exist")
                return False

            # Check for processes using the port
            result = subprocess.run(["lsof", self.__device],
                                    capture_output=True,
                                    text=True)

            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                if len(lines) > 1:  # Header + processes
                    print(
                        f"Device {self.__device} is being used by other processes:"
                    )
                    for line in lines[1:]:
                        print(f"  {line}")
                    return False
            return True
        except Exception as e:
            print(f"Error checking device availability: {e}")
            return False

    def __kill_processes_using_device(self):
        try:
            result = subprocess.run(
                ["fuser", "-k", self.__device],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                print(f"Killed processes using {self.__device}")
                time.sleep(1)
                return True
            return False
        except Exception as e:
            print(f"Error killing processes: {e}")
            return False

    def __fix_device_permissions(self):
        try:
            result = subprocess.run(["sudo", "chmod", "666", self.__device],
                                    capture_output=True,
                                    text=True)
            if result.returncode == 0:
                print(f"Fixed permissions for {self.__device}")
                return True
            return False
        except Exception as e:
            print(f"Error fixing device permissions: {e}")
            return False

    def __initialize_hardware(self):
        # Check and prepare port before connection
        self.__prepare_device()

        # Initialize the port handler, packet handler, and group sync read/write
        self.__port_handler = PortHandler(self.__device)
        self.__packet_handler = PacketHandler(2.0)
        self.__group_sync_read = GroupSyncRead(
            self.__port_handler,
            self.__packet_handler,
            DYNAMIXEL_PRESENT_POSITION_ADDR,
            DYNAMIXEL_PRESENT_POSITION_LEN,
        )
        self.__group_sync_write = GroupSyncWrite(
            self.__port_handler,
            self.__packet_handler,
            DYNAMIXEL_GOAL_POSITION_ADDR,
            DYNAMIXEL_GOAL_POSITION_LEN,
        )

        # Open the port and set the baudrate
        if not self.__port_handler.openPort():
            raise RuntimeError("Failed to open the port")

        if not self.__port_handler.setBaudRate(self.__baudrate):
            raise RuntimeError(
                f"Failed to change the baudrate, {self.__baudrate}")

        # Add parameters for each Dynamixel servo to the group sync read
        for dxl_id in self.__idxs:
            if not self.__group_sync_read.addParam(dxl_id):
                raise RuntimeError(
                    f"Failed to add parameter for Dynamixel with ID {dxl_id}")

        # Disable torque for each Dynamixel servo
        if self.__torque_enabled:
            try:
                self.__hardware_set_torque_mode(self.__torque_enabled)
            except Exception as e:
                print(f"device: {self.__device}, {e}")

    def __prepare_device(self):
        if not self.__check_device_availability():
            print(
                f"Device {self.__device} is not available, attempting to fix..."
            )
            self.__kill_processes_using_device()
            self.__fix_device_permissions()

            # Check again after fixing
            if not self.__check_device_availability():
                print(f"Warning: Device {self.__device} may still have issues")

    def __hardware_set_torque_mode(self, enable: bool):
        torque_value = DYNAMIXEL_TORQUE_ENABLE_VAL if enable else DYNAMIXEL_TORQUE_DISABLE_VAL
        with self.__lock:
            for dxl_id in self.__idxs:
                dxl_comm_result, dxl_error = self.__packet_handler.write1ByteTxRx(
                    self.__port_handler, dxl_id, DYNAMIXEL_TORQUE_ENABLE_ADDR,
                    torque_value)
                if dxl_comm_result != COMM_SUCCESS or dxl_error != 0:
                    print(dxl_comm_result)
                    print(dxl_error)
                    raise RuntimeError(
                        f"Failed to set torque mode for Dynamixel with ID {dxl_id}"
                    )

        self.__torque_enabled = enable

    def close(self):
        if not self._working.is_set():
            return
        self._working.clear()
        self.__port_handler.closePort()
        hex_log(HEX_LOG_LEVEL["info"], "HexRobotGello closed")
