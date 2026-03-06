#!/usr/bin/env python3
# -*- coding:utf-8 -*-
################################################################
# Copyright 2025 Dong Zhaorui. All rights reserved.
# Author: Dong Zhaorui 847235539@qq.com
# Date  : 2025-09-17
################################################################

import os
import copy
import threading
import cv2
import numpy as np
from collections import deque

import mujoco
from mujoco import viewer

from ..mujoco_base import HexMujocoBase
from ...hex_launch import hex_log, HEX_LOG_LEVEL

from hex_robo_utils import (
    HexCtrlUtilMitJoint as CtrlUtil,
    HexRate,
    ns_now,
    hex_ts_delta_ms,
    hex_ts_now,
    ns_to_hex_ts,
)

MUJOCO_CONFIG = {
    "states_rate": 1000,
    "img_rate": 30,
    "tau_ctrl": False,
    "mit_kp": [200.0, 200.0, 200.0, 75.0, 15.0, 15.0, 20.0],
    "mit_kd": [12.5, 12.5, 12.5, 6.0, 0.31, 0.31, 1.0],
    "cam_type": ["empty", "empty", "empty"],
    "headless": False,
    "sens_ts": True,
}
CAMERA_CONFIG = {
    "empty": (False, False),
    "rgb": (True, False),
    "berxel": (True, True),
    "realsense": (True, True),
}


class HexMujocoE3Desktop(HexMujocoBase):

    def __init__(
        self,
        mujoco_config: dict = MUJOCO_CONFIG,
        realtime_mode: bool = False,
    ):
        HexMujocoBase.__init__(self, realtime_mode)

        try:
            self.__sim_rate = int(mujoco_config["control_hz"])
            states_rate = mujoco_config["states_rate"]
            img_rate = mujoco_config["img_rate"]
            self.__tau_ctrl = mujoco_config["tau_ctrl"]
            self.__mit_kp = mujoco_config["mit_kp"]
            self.__mit_kd = mujoco_config["mit_kd"]
            self.__cam_type = mujoco_config["cam_type"]
            self.__headless = mujoco_config["headless"]
            self.__sens_ts = mujoco_config["sens_ts"]
        except KeyError as ke:
            missing_key = ke.args[0]
            raise ValueError(
                f"mujoco_config is not valid, missing key: {missing_key}")

        # mujoco init
        model_path = os.path.join(os.path.dirname(__file__), "model/scene.xml")
        self.__model = mujoco.MjModel.from_xml_path(model_path)
        self.__data = mujoco.MjData(self.__model)
        self.__model.opt.timestep = 1.0 / self.__sim_rate
        mujoco.mj_resetData(self.__model, self.__data)

        # state init
        self.__state_idx = {
            "left_arm": [0, 1, 2, 3, 4, 5],
            "left_gripper": [6],
            "right_arm": [12, 13, 14, 15, 16, 17],
            "right_gripper": [18],
            "obj": [24, 25, 26, 27, 28, 29, 30],
        }
        self.__ctrl_idx = {
            "left_arm": [0, 1, 2, 3, 4, 5],
            "left_gripper": [6],
            "right_arm": [7, 8, 9, 10, 11, 12],
            "right_gripper": [13],
        }
        self.__limit_idx = {
            "left_arm":
            np.arange(len(self.__state_idx["left_arm"])).tolist(),
            "left_gripper": (np.arange(len(self.__state_idx["left_gripper"])) +
                             len(self.__state_idx["left_arm"])).tolist(),
            "right_arm": (np.arange(len(self.__state_idx["right_arm"])) +
                          len(self.__state_idx["left_arm"]) +
                          len(self.__state_idx["left_gripper"])).tolist(),
            "right_gripper":
            (np.arange(len(self.__state_idx["right_gripper"])) +
             len(self.__state_idx["left_arm"]) +
             len(self.__state_idx["left_gripper"]) +
             len(self.__state_idx["right_arm"])).tolist(),
        }
        self._limits = self.__model.jnt_range[np.concatenate([
            self.__state_idx["left_arm"], self.__state_idx["left_gripper"],
            self.__state_idx["right_arm"], self.__state_idx["right_gripper"]
        ]), :].copy().reshape(-1, 1, 2)
        if not self.__tau_ctrl:
            self.__mit_kp = np.ascontiguousarray(np.asarray(self.__mit_kp))
            self.__mit_kd = np.ascontiguousarray(np.asarray(self.__mit_kd))
            self.__mit_ctrl = CtrlUtil()
        self.__gripper_ratio = 1.33 / 1.52
        self._limits[self.__limit_idx["left_gripper"],
                     0, :] *= self.__gripper_ratio
        self._limits[self.__limit_idx["right_gripper"],
                     0, :] *= self.__gripper_ratio
        self._dofs = np.array([
            len(self.__state_idx["left_arm"]),
            len(self.__state_idx["left_gripper"]),
            len(self.__state_idx["right_arm"]),
            len(self.__state_idx["right_gripper"]),
        ])
        keyframe_id = mujoco.mj_name2id(
            self.__model,
            mujoco.mjtObj.mjOBJ_KEY,
            "home",
        )
        self.__state_init = {
            "qpos": self.__model.key_qpos[keyframe_id],
            "qvel": np.zeros_like(self.__data.qvel),
            "ctrl": np.zeros_like(self.__data.ctrl),
        }
        self.__data.qpos = self.__state_init["qpos"]
        self.__data.qvel = self.__state_init["qvel"]
        self.__data.ctrl = self.__state_init["ctrl"]
        self.__states_trig_thresh = int(self.__sim_rate / states_rate)

        # camera init
        self.__img_trig_thresh = int(self.__sim_rate / img_rate)
        self.__width, self.__height = (224, 224)
        head_fovy_rad = self.__model.cam_fovy[0] * np.pi / 180.0
        left_fovy_rad = self.__model.cam_fovy[1] * np.pi / 180.0
        right_fovy_rad = self.__model.cam_fovy[2] * np.pi / 180.0
        head_focal = 0.5 * self.__height / np.tan(head_fovy_rad / 2.0)
        left_focal = 0.5 * self.__height / np.tan(left_fovy_rad / 2.0)
        right_focal = 0.5 * self.__height / np.tan(right_fovy_rad / 2.0)
        self._intri = np.array([
            [head_focal, head_focal, self.__height / 2, self.__height / 2],
            [left_focal, left_focal, self.__height / 2, self.__height / 2],
            [right_focal, right_focal, self.__height / 2, self.__height / 2],
        ])
        self.__head_rgb, self.__head_depth = CAMERA_CONFIG.get(
            self.__cam_type[0], (False, False))
        self.__left_rgb, self.__left_depth = CAMERA_CONFIG.get(
            self.__cam_type[1], (False, False))
        self.__right_rgb, self.__right_depth = CAMERA_CONFIG.get(
            self.__cam_type[2], (False, False))
        self.__rgb_cam, self.__depth_cam = None, None
        has_rgb = self.__left_rgb or self.__right_rgb or self.__head_rgb
        has_depth = self.__left_depth or self.__right_depth or self.__head_depth
        if has_rgb:
            self.__rgb_cam = mujoco.Renderer(self.__model, self.__height,
                                             self.__width)
        if has_depth:
            self.__depth_cam = mujoco.Renderer(self.__model, self.__height,
                                               self.__width)
            self.__depth_cam.enable_depth_rendering()

        # viewer init
        mujoco.mj_forward(self.__model, self.__data)
        if not self.__headless:
            self.__viewer = viewer.launch_passive(self.__model, self.__data)

        # start work loop
        self._working.set()

    def __del__(self):
        HexMujocoBase.__del__(self)

    def reset(self) -> bool:
        self.__data.qpos = self.__state_init["qpos"]
        self.__data.qvel = self.__state_init["qvel"]
        self.__data.ctrl = self.__state_init["ctrl"]
        mujoco.mj_forward(self.__model, self.__data)
        if not self.__headless:
            self.__viewer.sync()
        return True

    def work_loop(self, hex_queues: list[deque | threading.Event]):
        states_left_queue = hex_queues[0]
        states_right_queue = hex_queues[1]
        states_obj_queue = hex_queues[2]
        cmds_left_queue = hex_queues[3]
        cmds_right_queue = hex_queues[4]
        head_rgb_queue = hex_queues[5]
        head_depth_queue = hex_queues[6]
        left_rgb_queue = hex_queues[7]
        left_depth_queue = hex_queues[8]
        right_rgb_queue = hex_queues[9]
        right_depth_queue = hex_queues[10]
        stop_event = hex_queues[11]

        last_states_ts = {"s": 0, "ns": 0}
        states_left_count = 0
        states_right_count = 0
        states_obj_count = 0
        last_cmds_left_seq = -1
        last_cmds_right_seq = -1
        head_rgb_count = 0
        head_depth_count = 0
        left_rgb_count = 0
        left_depth_count = 0
        right_rgb_count = 0
        right_depth_count = 0
        cmds_left = None
        cmds_right = None

        rate = HexRate(self.__sim_rate)
        states_trig_count = 0
        img_trig_count = 0
        self.__bias_ns = ns_now() - self.__data.time * 1_000_000_000
        init_ts = self.__mujoco_ts() if self.__sens_ts else hex_ts_now()
        head_rgb_queue.append((init_ts, 0,
                               np.zeros((self.__height, self.__width, 3),
                                        dtype=np.uint8)))
        head_depth_queue.append((init_ts, 0,
                                 np.zeros((self.__height, self.__width),
                                          dtype=np.uint16)))
        left_rgb_queue.append((init_ts, 0,
                               np.zeros((self.__height, self.__width, 3),
                                        dtype=np.uint8)))
        left_depth_queue.append((init_ts, 0,
                                 np.zeros((self.__height, self.__width),
                                          dtype=np.uint16)))
        right_rgb_queue.append((init_ts, 0,
                                np.zeros((self.__height, self.__width, 3),
                                         dtype=np.uint8)))
        right_depth_queue.append((init_ts, 0,
                                  np.zeros((self.__height, self.__width),
                                           dtype=np.uint16)))
        while self._working.is_set() and not stop_event.is_set():
            states_trig_count += 1
            if states_trig_count >= self.__states_trig_thresh:
                states_trig_count = 0

                # states
                ts, states_left, states_right, states_obj = self.__get_states()
                if states_left is not None:
                    if hex_ts_delta_ms(ts, last_states_ts) > 1e-6:
                        last_states_ts = ts
                        # states left
                        states_left_queue.append(
                            (ts, states_left_count, states_left))
                        states_left_count = (states_left_count +
                                             1) % self._max_seq_num
                        # states right
                        states_right_queue.append(
                            (ts, states_right_count, states_right))
                        states_right_count = (states_right_count +
                                              1) % self._max_seq_num
                        # states obj
                        states_obj_queue.append(
                            (ts, states_obj_count, states_obj))
                        states_obj_count = (states_obj_count +
                                            1) % self._max_seq_num

                # cmds
                cmds_left_pack = None
                try:
                    cmds_left_pack = cmds_left_queue[
                        -1] if self._realtime_mode else cmds_left_queue.popleft(
                        )
                except IndexError:
                    pass
                if cmds_left_pack is not None:
                    ts, seq, cmds_left = cmds_left_pack
                    if seq != last_cmds_left_seq:
                        last_cmds_left_seq = seq
                        if hex_ts_delta_ms(hex_ts_now(), ts) < 200.0:
                            cmds_left = cmds_left.copy()
                if cmds_left is not None:
                    self.__set_cmds(cmds_left, "left")

                cmds_right_pack = None
                try:
                    cmds_right_pack = cmds_right_queue[
                        -1] if self._realtime_mode else cmds_right_queue.popleft(
                        )
                except IndexError:
                    pass
                if cmds_right_pack is not None:
                    ts, seq, cmds_right_get = cmds_right_pack
                    if seq != last_cmds_right_seq:
                        last_cmds_right_seq = seq
                        if hex_ts_delta_ms(hex_ts_now(), ts) < 200.0:
                            cmds_right = cmds_right_get.copy()
                if cmds_right is not None:
                    self.__set_cmds(cmds_right, "right")

            img_trig_count += 1
            if img_trig_count >= self.__img_trig_thresh:
                img_trig_count = 0

                # head rgb
                if self.__head_rgb:
                    ts, rgb_img = self.__get_rgb("head_camera")
                    if rgb_img is not None:
                        head_rgb_queue.append((ts, head_rgb_count, rgb_img))
                        head_rgb_count = (head_rgb_count +
                                          1) % self._max_seq_num

                # head depth
                if self.__head_depth:
                    ts, depth_img = self.__get_depth("head_camera")
                    if depth_img is not None:
                        head_depth_queue.append(
                            (ts, head_depth_count, depth_img))
                        head_depth_count = (head_depth_count +
                                            1) % self._max_seq_num

                # left rgb
                if self.__left_rgb:
                    ts, rgb_img = self.__get_rgb("left_camera")
                    if rgb_img is not None:
                        left_rgb_queue.append((ts, left_rgb_count, rgb_img))
                        left_rgb_count = (left_rgb_count +
                                          1) % self._max_seq_num

                # left depth
                if self.__left_depth:
                    ts, depth_img = self.__get_depth("left_camera")
                    if depth_img is not None:
                        left_depth_queue.append(
                            (ts, left_depth_count, depth_img))
                        left_depth_count = (left_depth_count +
                                            1) % self._max_seq_num

                # right rgb
                if self.__right_rgb:
                    ts, rgb_img = self.__get_rgb("right_camera")
                    if rgb_img is not None:
                        right_rgb_queue.append((ts, right_rgb_count, rgb_img))
                        right_rgb_count = (right_rgb_count +
                                           1) % self._max_seq_num

                # right depth
                if self.__right_depth:
                    ts, depth_img = self.__get_depth("right_camera")
                    if depth_img is not None:
                        right_depth_queue.append(
                            (ts, right_depth_count, depth_img))
                        right_depth_count = (right_depth_count +
                                             1) % self._max_seq_num

            # mujoco step
            mujoco.mj_step(self.__model, self.__data)
            if not self.__headless:
                self.__viewer.sync()

            # sleep
            rate.sleep()

        # close
        self.close()

    def __get_states(self):
        pos = copy.deepcopy(self.__data.qpos)
        vel = copy.deepcopy(self.__data.qvel)
        eff = copy.deepcopy(self.__data.qfrc_actuator)
        pos[self.__state_idx["left_gripper"]] = pos[
            self.__state_idx["left_gripper"]] * self.__gripper_ratio
        pos[self.__state_idx["right_gripper"]] = pos[
            self.__state_idx["right_gripper"]] * self.__gripper_ratio
        return self.__mujoco_ts() if self.__sens_ts else hex_ts_now(
        ), np.array([
            pos[self.__state_idx["left_arm"] +
                self.__state_idx["left_gripper"]],
            vel[self.__state_idx["left_arm"] +
                self.__state_idx["left_gripper"]],
            eff[self.__state_idx["left_arm"] +
                self.__state_idx["left_gripper"]],
        ]).T, np.array([
            pos[self.__state_idx["right_arm"] +
                self.__state_idx["right_gripper"]],
            vel[self.__state_idx["right_arm"] +
                self.__state_idx["right_gripper"]],
            eff[self.__state_idx["right_arm"] +
                self.__state_idx["right_gripper"]],
        ]).T, self.__data.qpos[self.__state_idx["obj"]].copy()

    def __set_cmds(self, cmds: np.ndarray, robot_name: str):
        state_idx = None
        ctrl_idx = None
        limit_idx = None
        if robot_name == "left":
            ctrl_idx = self.__ctrl_idx["left_arm"] + self.__ctrl_idx[
                "left_gripper"]
            if not self.__tau_ctrl:
                state_idx = self.__state_idx["left_arm"] + self.__state_idx[
                    "left_gripper"]
                limit_idx = self.__limit_idx["left_arm"] + self.__limit_idx[
                    "left_gripper"]
        elif robot_name == "right":
            ctrl_idx = self.__ctrl_idx["right_arm"] + self.__ctrl_idx[
                "right_gripper"]
            if not self.__tau_ctrl:
                state_idx = self.__state_idx["right_arm"] + self.__state_idx[
                    "right_gripper"]
                limit_idx = self.__limit_idx["right_arm"] + self.__limit_idx[
                    "right_gripper"]
        else:
            raise ValueError(f"unknown robot name: {robot_name}")
        tau_cmds = None
        if not self.__tau_ctrl:
            cmd_pos = None
            tar_vel = np.zeros(cmds.shape[0])
            cmd_tor = np.zeros(cmds.shape[0])
            cmd_kp = self.__mit_kp.copy()
            cmd_kd = self.__mit_kd.copy()
            if len(cmds.shape) == 1:
                cmd_pos = cmds.copy()
            elif len(cmds.shape) == 2:
                if cmds.shape[1] == 2:
                    cmd_pos = cmds[:, 0].copy()
                    cmd_tor = cmds[:, 1].copy()
                elif cmds.shape[1] == 5:
                    cmd_pos = cmds[:, 0].copy()
                    tar_vel = cmds[:, 1].copy()
                    cmd_tor = cmds[:, 2].copy()
                    cmd_kp = cmds[:, 3].copy()
                    cmd_kd = cmds[:, 4].copy()
                else:
                    raise ValueError(
                        f"The shape of cmds is invalid: {cmds.shape}")
            else:
                raise ValueError(f"The shape of cmds is invalid: {cmds.shape}")
            tar_pos = self._apply_pos_limits(
                cmd_pos,
                self._limits[limit_idx, 0, 0],
                self._limits[limit_idx, 0, 1],
            )
            tar_pos[-1] /= self.__gripper_ratio
            tau_cmds = self.__mit_ctrl(
                cmd_kp,
                cmd_kd,
                tar_pos,
                tar_vel,
                self.__data.qpos[state_idx],
                self.__data.qvel[state_idx],
                cmd_tor,
            )
        else:
            tau_cmds = cmds.copy()
        self.__data.ctrl[ctrl_idx] = tau_cmds

    def __get_rgb(self, camera_name: str):
        self.__rgb_cam.update_scene(self.__data, camera_name)
        rgb_img = self.__rgb_cam.render()
        return self.__mujoco_ts() if self.__sens_ts else hex_ts_now(
        ), cv2.cvtColor(rgb_img, cv2.COLOR_RGB2BGR)

    def __get_depth(self, camera_name: str):
        self.__depth_cam.update_scene(self.__data, camera_name)
        depth_m = self.__depth_cam.render().astype(np.float32)
        depth_img = np.clip(depth_m * 1000.0, 0, 65535).astype(np.uint16)
        return self.__mujoco_ts() if self.__sens_ts else hex_ts_now(
        ), depth_img

    def __mujoco_ts(self):
        mujoco_ts = self.__data.time * 1_000_000_000 + self.__bias_ns
        return ns_to_hex_ts(mujoco_ts)

    def close(self):
        if not self._working.is_set():
            return
        self._working.clear()
        if self.__rgb_cam is not None:
            self.__rgb_cam.close()
        if self.__depth_cam is not None:
            self.__depth_cam.close()
        if not self.__headless:
            self.__viewer.close()
        hex_log(HEX_LOG_LEVEL["info"], "HexMujocoE3Desktop closed")
