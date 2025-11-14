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

import mujoco
from mujoco import viewer

from ..mujoco_base import HexMujocoBase
from ...zmq_base import (
    hex_zmq_ts_now,
    hex_zmq_ts_delta_ms,
    HexRate,
    HexSafeValue,
)
from ...hex_launch import hex_log, HEX_LOG_LEVEL
from hex_robo_utils import HexCtrlUtilMitJoint as CtrlUtil

MUJOCO_CONFIG = {
    "states_rate": 500,
    "img_rate": 30,
    "tau_ctrl": False,
    "mit_kp": [200.0, 200.0, 200.0, 75.0, 15.0, 15.0, 20.0],
    "mit_kd": [12.5, 12.5, 12.5, 6.0, 0.31, 0.31, 1.0],
    "headless": False,
    "sens_ts": True,
}


class HexMujocoE3Desktop(HexMujocoBase):

    def __init__(
        self,
        mujoco_config: dict = MUJOCO_CONFIG,
    ):
        HexMujocoBase.__init__(self)

        try:
            states_rate = mujoco_config["states_rate"]
            img_rate = mujoco_config["img_rate"]
            self.__tau_ctrl = mujoco_config["tau_ctrl"]
            self.__mit_kp = mujoco_config["mit_kp"]
            self.__mit_kd = mujoco_config["mit_kd"]
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
        self.__sim_rate = int(1.0 / self.__model.opt.timestep)

        # state init
        self.__state_left_idx = [0, 1, 2, 3, 4, 5, 6]
        self.__state_right_idx = [12, 13, 14, 15, 16, 17, 18]
        self.__obj_pose_idx = [24, 25, 26, 27, 28, 29, 30]
        self.__ctrl_left_idx = [0, 1, 2, 3, 4, 5, 6]
        self.__ctrl_right_idx = [7, 8, 9, 10, 11, 12, 13]
        self._limits = np.stack(
            [
                self.__model.jnt_range[self.__state_left_idx, :],
                self.__model.jnt_range[self.__state_right_idx, :]
            ],
            axis=0,
        )
        if not self.__tau_ctrl:
            self.__mit_kp = np.ascontiguousarray(np.asarray(self.__mit_kp))
            self.__mit_kd = np.ascontiguousarray(np.asarray(self.__mit_kd))
            self.__mit_ctrl = CtrlUtil()
        self.__gripper_ratio = 1.33 / 1.52
        self._limits[0, -1] *= self.__gripper_ratio
        self._limits[1, -1] *= self.__gripper_ratio
        self._dofs = np.array([
            len(self.__state_left_idx),
            len(self.__state_right_idx),
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
        width, height = 640, 400
        head_fovy_rad = self.__model.cam_fovy[0] * np.pi / 180.0
        left_fovy_rad = self.__model.cam_fovy[1] * np.pi / 180.0
        right_fovy_rad = self.__model.cam_fovy[2] * np.pi / 180.0
        head_focal = 0.5 * height / np.tan(head_fovy_rad / 2.0)
        left_focal = 0.5 * height / np.tan(left_fovy_rad / 2.0)
        right_focal = 0.5 * height / np.tan(right_fovy_rad / 2.0)
        self._intri = np.array([
            [head_focal, head_focal, height / 2, height / 2],
            [left_focal, left_focal, height / 2, height / 2],
            [right_focal, right_focal, height / 2, height / 2],
        ])
        self.__rgb_cam = mujoco.Renderer(self.__model, height, width)
        self.__depth_cam = mujoco.Renderer(self.__model, height, width)
        self.__depth_cam.enable_depth_rendering()
        self.__img_trig_thresh = int(self.__sim_rate / img_rate)

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

    def work_loop(self, hex_values: list[HexSafeValue | threading.Event]):
        states_left_value = hex_values[0]
        states_right_value = hex_values[1]
        states_obj_value = hex_values[2]
        cmds_left_value = hex_values[3]
        cmds_right_value = hex_values[4]
        head_rgb_value = hex_values[5]
        head_depth_value = hex_values[6]
        left_rgb_value = hex_values[7]
        left_depth_value = hex_values[8]
        right_rgb_value = hex_values[9]
        right_depth_value = hex_values[10]
        stop_event = hex_values[11]

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

        rate = HexRate(self.__sim_rate)
        states_trig_count = 0
        img_trig_count = 0
        while self._working.is_set() and not stop_event.is_set():
            states_trig_count += 1
            if states_trig_count >= self.__states_trig_thresh:
                states_trig_count = 0

                # states
                ts, states_left, states_right, states_obj = self.__get_states()
                if states_left is not None:
                    if hex_zmq_ts_delta_ms(ts, last_states_ts) > 1.0:
                        last_states_ts = ts
                        # states left
                        states_left_value.set(
                            (ts, states_left_count, states_left))
                        states_left_count = (states_left_count +
                                             1) % self._max_seq_num
                        # states right
                        states_right_value.set(
                            (ts, states_right_count, states_right))
                        states_right_count = (states_right_count +
                                              1) % self._max_seq_num
                        # states obj
                        states_obj_value.set(
                            (ts, states_obj_count, states_obj))
                        states_obj_count = (states_obj_count +
                                            1) % self._max_seq_num

                # cmds
                cmds_left_pack = cmds_left_value.get(timeout_s=-1.0)
                if cmds_left_pack is not None:
                    ts, seq, cmds_left = cmds_left_pack
                    if seq != last_cmds_left_seq:
                        last_cmds_left_seq = seq
                        if hex_zmq_ts_delta_ms(hex_zmq_ts_now(), ts) < 200.0:
                            self.__set_cmds(cmds_left, "left")

                cmds_right_pack = cmds_right_value.get(timeout_s=-1.0)
                if cmds_right_pack is not None:
                    ts, seq, cmds_right = cmds_right_pack
                    if seq != last_cmds_right_seq:
                        last_cmds_right_seq = seq
                        if hex_zmq_ts_delta_ms(hex_zmq_ts_now(), ts) < 200.0:
                            self.__set_cmds(cmds_right, "right")

            img_trig_count += 1
            if img_trig_count >= self.__img_trig_thresh:
                img_trig_count = 0

                # head rgb
                ts, rgb_img = self.__get_rgb("head_camera")
                if rgb_img is not None:
                    head_rgb_value.set((ts, head_rgb_count, rgb_img))
                    head_rgb_count = (head_rgb_count + 1) % self._max_seq_num

                # head depth
                ts, depth_img = self.__get_depth("head_camera")
                if depth_img is not None:
                    head_depth_value.set((ts, head_depth_count, depth_img))
                    head_depth_count = (head_depth_count +
                                        1) % self._max_seq_num

                # left rgb
                ts, rgb_img = self.__get_rgb("left_camera")
                if rgb_img is not None:
                    left_rgb_value.set((ts, left_rgb_count, rgb_img))
                    left_rgb_count = (left_rgb_count + 1) % self._max_seq_num

                # left depth
                ts, depth_img = self.__get_depth("left_camera")
                if depth_img is not None:
                    left_depth_value.set((ts, left_depth_count, depth_img))
                    left_depth_count = (left_depth_count +
                                        1) % self._max_seq_num

                # right rgb
                ts, rgb_img = self.__get_rgb("right_camera")
                if rgb_img is not None:
                    right_rgb_value.set((ts, right_rgb_count, rgb_img))
                    right_rgb_count = (right_rgb_count + 1) % self._max_seq_num

                # right depth
                ts, depth_img = self.__get_depth("right_camera")
                if depth_img is not None:
                    right_depth_value.set((ts, right_depth_count, depth_img))
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
        pos[self.__state_left_idx[-1]] = pos[
            self.__state_left_idx[-1]] * self.__gripper_ratio
        pos[self.__state_right_idx[-1]] = pos[
            self.__state_right_idx[-1]] * self.__gripper_ratio
        return self.__mujoco_ts() if self.__sens_ts else hex_zmq_ts_now(
        ), np.array([
            pos[self.__state_left_idx],
            vel[self.__state_left_idx],
            eff[self.__state_left_idx],
        ]).T, np.array([
            pos[self.__state_right_idx],
            vel[self.__state_right_idx],
            eff[self.__state_right_idx],
        ]).T, self.__data.qpos[self.__obj_pose_idx].copy()

    def __set_cmds(self, cmds: np.ndarray, robot_name: str):
        ctrl_idx = []
        state_idx = []
        limit_idx = None
        if robot_name == "left":
            ctrl_idx = self.__ctrl_left_idx
            if not self.__tau_ctrl:
                state_idx = self.__state_left_idx
                limit_idx = 0
        elif robot_name == "right":
            ctrl_idx = self.__ctrl_right_idx
            if not self.__tau_ctrl:
                state_idx = self.__state_right_idx
                limit_idx = 1
        else:
            raise ValueError(f"unknown robot name: {robot_name}")
        tau_cmds = None
        if not self.__tau_ctrl:
            cmd_pos = None
            tar_vel = np.zeros_like(cmds)
            cmd_tor = np.zeros_like(cmds)
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
                self._limits[limit_idx, :, 0],
                self._limits[limit_idx, :, 1],
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
        return self.__mujoco_ts() if self.__sens_ts else hex_zmq_ts_now(
        ), cv2.cvtColor(rgb_img, cv2.COLOR_RGB2BGR)

    def __get_depth(self, camera_name: str):
        self.__depth_cam.update_scene(self.__data, camera_name)
        depth_m = self.__depth_cam.render().astype(np.float32)
        depth_img = np.clip(depth_m * 1000.0, 0, 65535).astype(np.uint16)
        return self.__mujoco_ts() if self.__sens_ts else hex_zmq_ts_now(
        ), depth_img

    def __mujoco_ts(self):
        mujoco_ts = self.__data.time
        return {
            "s": int(mujoco_ts // 1),
            "ns": int((mujoco_ts % 1) * 1_000_000_000),
        }

    def close(self):
        if not self._working.is_set():
            return
        self._working.clear()
        self.__rgb_cam.close()
        self.__depth_cam.close()
        if not self.__headless:
            self.__viewer.close()
        hex_log(HEX_LOG_LEVEL["info"], "HexMujocoE3Desktop closed")
