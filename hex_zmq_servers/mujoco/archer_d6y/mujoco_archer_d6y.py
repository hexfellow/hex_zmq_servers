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


class HexMujocoArcherD6y(HexMujocoBase):

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
        self.__state_robot_idx = [0, 1, 2, 3, 4, 5, 6]
        self.__state_obj_idx = [12, 13, 14, 15, 16, 17, 18]
        self.__ctrl_robot_idx = [0, 1, 2, 3, 4, 5, 6]
        self.__ctrl_obj_idx = [0, 1, 2, 3, 4, 5, 6]
        self._limits = np.stack(
            [self.__model.jnt_range[self.__state_robot_idx, :]],
            axis=0,
        )
        if not self.__tau_ctrl:
            self.__mit_kp = np.ascontiguousarray(np.asarray(self.__mit_kp))
            self.__mit_kd = np.ascontiguousarray(np.asarray(self.__mit_kd))
            self.__mit_ctrl = CtrlUtil()
        self.__gripper_ratio = 1.33 / 1.52
        self._limits[0, -1] *= self.__gripper_ratio
        self._dofs = np.array([len(self.__state_robot_idx)])
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
        fovy_rad = self.__model.cam_fovy[0] * np.pi / 180.0
        focal = 0.5 * height / np.tan(fovy_rad / 2.0)
        self._intri = np.array([focal, focal, height / 2, height / 2])
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
        states_robot_value = hex_values[0]
        states_obj_value = hex_values[1]
        cmds_robot_value = hex_values[2]
        rgb_value = hex_values[3]
        depth_value = hex_values[4]
        stop_event = hex_values[5]

        last_states_ts = {"s": 0, "ns": 0}
        states_robot_count = 0
        states_obj_count = 0
        last_cmds_robot_seq = -1
        rgb_count = 0
        depth_count = 0

        rate = HexRate(self.__sim_rate)
        states_trig_count = 0
        img_trig_count = 0

        while self._working.is_set() and not stop_event.is_set():
            states_trig_count += 1
            if states_trig_count >= self.__states_trig_thresh:
                states_trig_count = 0

                # states
                ts, states_robot, states_obj = self.__get_states()
                if states_robot is not None:
                    if hex_zmq_ts_delta_ms(ts, last_states_ts) > 1.0:
                        last_states_ts = ts

                        # states robot
                        states_robot_value.set(
                            (ts, states_robot_count, states_robot))
                        states_robot_count = (states_robot_count +
                                              1) % self._max_seq_num

                        # states obj
                        states_obj_value.set(
                            (ts, states_obj_count, states_obj))
                        states_obj_count = (states_obj_count +
                                            1) % self._max_seq_num

                # cmds
                cmds_robot_pack = cmds_robot_value.get(timeout_s=-1.0)
                if cmds_robot_pack is not None:
                    ts, seq, cmds = cmds_robot_pack
                    if seq != last_cmds_robot_seq:
                        last_cmds_robot_seq = seq
                        if hex_zmq_ts_delta_ms(hex_zmq_ts_now(), ts) < 200.0:
                            self.__set_cmds(cmds)

            img_trig_count += 1
            if img_trig_count >= self.__img_trig_thresh:
                img_trig_count = 0

                # rgb
                ts, rgb_img = self.__get_rgb()
                if rgb_img is not None:
                    rgb_value.set((ts, rgb_count, rgb_img))
                    rgb_count = (rgb_count + 1) % self._max_seq_num

                # depth
                ts, depth_img = self.__get_depth()
                if depth_img is not None:
                    depth_value.set((ts, depth_count, depth_img))
                    depth_count = (depth_count + 1) % self._max_seq_num

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
        pos[self.__state_robot_idx[-1]] = pos[
            self.__state_robot_idx[-1]] * self.__gripper_ratio
        return self.__mujoco_ts() if self.__sens_ts else hex_zmq_ts_now(
        ), np.array([
            pos[self.__state_robot_idx],
            vel[self.__state_robot_idx],
            eff[self.__state_robot_idx],
        ]).T, self.__data.qpos[self.__state_obj_idx].copy()

    def __set_cmds(self, cmds: np.ndarray):
        tau_cmds = None
        if not self.__tau_ctrl:
            cmd_pos = None
            tar_vel = np.zeros_like(cmds)
            cmd_tor = np.zeros_like(cmds)
            cmd_kp = self.__mit_kp.copy()
            cmd_kd = self.__mit_kd.copy()
            if len(cmds.shape) == 1:
                cmd_pos = cmds
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
                    raise ValueError(f"The shape of cmds is invalid: {cmds.shape}")
            else:
                raise ValueError(f"The shape of cmds is invalid: {cmds.shape}")
            tar_pos = self._apply_pos_limits(
                cmd_pos,
                self._limits[0, :, 0],
                self._limits[0, :, 1],
            )
            tar_pos[-1] /= self.__gripper_ratio
            tau_cmds = self.__mit_ctrl(
                cmd_kp,
                cmd_kd,
                tar_pos,
                tar_vel,
                self.__data.qpos[self.__state_robot_idx],
                self.__data.qvel[self.__state_robot_idx],
                cmd_tor,
            )
        else:
            tau_cmds = cmds.copy()
        self.__data.ctrl[self.__ctrl_robot_idx] = tau_cmds

    def __get_rgb(self):
        self.__rgb_cam.update_scene(self.__data, "end_camera")
        rgb_img = self.__rgb_cam.render()
        return self.__mujoco_ts() if self.__sens_ts else hex_zmq_ts_now(
        ), cv2.cvtColor(rgb_img, cv2.COLOR_RGB2BGR)

    def __get_depth(self):
        self.__depth_cam.update_scene(self.__data, "end_camera")
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
        hex_log(HEX_LOG_LEVEL["info"], "HexMujocoArcherD6y closed")
