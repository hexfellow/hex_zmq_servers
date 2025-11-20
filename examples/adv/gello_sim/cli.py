#!/usr/bin/env python3
# -*- coding:utf-8 -*-
################################################################
# Copyright 2025 Dong Zhaorui. All rights reserved.
# Author: Dong Zhaorui 847235539@qq.com
# Date  : 2025-09-25
################################################################

import argparse, json, time
import cv2
import numpy as np
from hex_zmq_servers import (
    HexRate,
    HEX_LOG_LEVEL,
    hex_log,
    HexRobotGelloClient,
    HexMujocoArcherY6Client,
)
from hex_robo_utils import HexDynUtil as DynUtil


def wait_client_working(client, timeout: float = 5.0) -> bool:
    for _ in range(int(timeout * 10)):
        working = client.is_working()
        if working is not None and working["cmd"] == "is_working_ok":
            if hasattr(client, "seq_clear"):
                client.seq_clear()
            return True
        else:
            time.sleep(0.1)
    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cfg", type=str, required=True)
    args = parser.parse_args()
    cfg = json.loads(args.cfg)

    try:
        model_path = cfg["model_path"]
        last_link = cfg["last_link"]
        gello_net_cfg = cfg["gello_net_cfg"]
        mujoco_net_cfg = cfg["mujoco_net_cfg"]
    except KeyError as ke:
        missing_key = ke.args[0]
        raise ValueError(f"cfg is not valid, missing key: {missing_key}")

    gello_client = HexRobotGelloClient(net_config=gello_net_cfg)
    mujoco_client = HexMujocoArcherY6Client(net_config=mujoco_net_cfg)
    dyn_util = DynUtil(model_path, last_link)

    # wait servers to work
    if not wait_client_working(gello_client):
        hex_log(HEX_LOG_LEVEL["err"], "gello server is not working")
        return
    if not wait_client_working(mujoco_client):
        hex_log(HEX_LOG_LEVEL["err"], "mujoco server is not working")
        return

    # work loop
    rate = HexRate(250)
    gello_cmds = None
    try:
        while True:
            # gello
            gello_states_hdr, gello_states = gello_client.get_states()
            if gello_states_hdr is not None:
                gello_cmds = gello_states.copy()

            # robot
            robot_states_hdr, robot_states = mujoco_client.get_states("robot")
            if robot_states_hdr is not None:
                arm_q = robot_states[:, 0]
                arm_dq = robot_states[:, 1]
                _, c_mat, g_vec, _, _ = dyn_util.dynamic_params(arm_q, arm_dq)
                tau_comp = c_mat @ arm_dq + g_vec
                if gello_cmds is not None:
                    cmds = np.concatenate(
                        (gello_cmds.reshape(-1, 1), tau_comp.reshape(-1, 1)),
                        axis=1)
                    _ = mujoco_client.set_cmds(cmds)

            # rgb
            rgb_hdr, rgb = mujoco_client.get_rgb()
            if rgb_hdr is not None:
                cv2.imshow("rgb_img", rgb)

            # depth
            depth_hdr, depth = mujoco_client.get_depth()
            if depth_hdr is not None:
                depth_values = depth.astype(np.float32)
                depth_norm = np.clip((depth_values - 70) / (1000 - 70), 0.0,
                                     1.0)
                depth_u8 = (depth_norm * 255.0).astype(np.uint8)
                depth_cmap = cv2.applyColorMap(depth_u8, cv2.COLORMAP_JET)
                cv2.imshow("depth_cmap", depth_cmap)

            key = cv2.waitKey(1)
            if key == ord('q'):
                break

            rate.sleep()
    finally:
        cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
