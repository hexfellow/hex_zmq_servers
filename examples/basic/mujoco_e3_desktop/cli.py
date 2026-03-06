#!/usr/bin/env python3
# -*- coding:utf-8 -*-
################################################################
# Copyright 2025 Dong Zhaorui. All rights reserved.
# Author: Dong Zhaorui 847235539@qq.com
# Date  : 2025-09-25
################################################################

import argparse, json
from hex_zmq_servers import (
    HEX_LOG_LEVEL,
    hex_log,
    HexMujocoE3DesktopClient,
)
from hex_robo_utils import (
    HexRate,
    hex_ts_delta_ms,
    hex_ts_now,
)

import cv2
import numpy as np


def depth_to_cmap(depth_img: np.ndarray):
    depth_values = depth_img.astype(np.float32)
    depth_norm = np.clip((depth_values - 70) / (1000 - 70), 0.0, 1.0)
    depth_u8 = (depth_norm * 255.0).astype(np.uint8)
    depth_cmap = cv2.applyColorMap(depth_u8, cv2.COLORMAP_JET)
    return depth_cmap


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cfg", type=str, required=True)
    args = parser.parse_args()
    cfg = json.loads(args.cfg)

    try:
        net_config = cfg["net"]
    except KeyError as ke:
        missing_key = ke.args[0]
        raise ValueError(
            f"e3_desktop_mujoco_config is not valid, missing key: {missing_key}"
        )

    # mujoco client
    client = HexMujocoE3DesktopClient(net_config=net_config)

    # get dofs, limits and intri
    dof_arr = client.get_dofs()
    dofs = {
        "left_arm": int(dof_arr[0]),
        "left_gripper": int(dof_arr[1]) if len(dof_arr) > 1 else None,
        "right_arm": int(dof_arr[2]),
        "right_gripper": int(dof_arr[3]) if len(dof_arr) > 3 else None,
        "left_sum": int(dof_arr[0]) + int(dof_arr[1]),
        "right_sum": int(dof_arr[2]) + int(dof_arr[3]),
    }
    limits = client.get_limits()
    _, intri = client.get_intri()
    assert limits.shape[0] == dof_arr.sum(
    ), "The number of limits must be equal to the number of dofs"
    hex_log(HEX_LOG_LEVEL["info"], f"dofs: {dofs}")
    hex_log(HEX_LOG_LEVEL["info"], f"limits: {limits.shape}")
    hex_log(HEX_LOG_LEVEL["info"], f"intri: {intri}")

    # get states, rgb and depth, and set cmds
    rate = HexRate(2e3)
    try:
        while True:
            left_states_hdr, left_states = client.get_states("left")
            if left_states_hdr is not None:
                curr_ts = hex_ts_now()
                hex_log(
                    HEX_LOG_LEVEL["info"],
                    f"left_states_seq: {left_states_hdr['args']}; delay: {hex_ts_delta_ms(curr_ts, left_states_hdr['ts'])}ms"
                )
                hex_log(HEX_LOG_LEVEL["info"],
                        f"left_states pos: {left_states[:, 0]}")
                hex_log(HEX_LOG_LEVEL["info"],
                        f"left_states vel: {left_states[:, 1]}")
                hex_log(HEX_LOG_LEVEL["info"],
                        f"left_states eff: {left_states[:, 2]}")

            right_states_hdr, right_states = client.get_states("right")
            if right_states_hdr is not None:
                curr_ts = hex_ts_now()
                hex_log(
                    HEX_LOG_LEVEL["info"],
                    f"right_states_seq: {right_states_hdr['args']}; delay: {hex_ts_delta_ms(curr_ts, right_states_hdr['ts'])}ms"
                )
                hex_log(HEX_LOG_LEVEL["info"],
                        f"right_states pos: {right_states[:, 0]}")
                hex_log(HEX_LOG_LEVEL["info"],
                        f"right_states vel: {right_states[:, 1]}")
                hex_log(HEX_LOG_LEVEL["info"],
                        f"right_states eff: {right_states[:, 2]}")

            obj_states_hdr, obj_states = client.get_states("obj")
            if obj_states_hdr is not None:
                curr_ts = hex_ts_now()
                hex_log(
                    HEX_LOG_LEVEL["info"],
                    f"obj_states_seq: {obj_states_hdr['args']}; delay: {hex_ts_delta_ms(curr_ts, obj_states_hdr['ts'])}ms"
                )
                hex_log(HEX_LOG_LEVEL["info"], f"obj_states: {obj_states}")

            cmds_left = np.array([0.0, -1.56, 3.0, 0.07, 0.0, 0.0, 0.5])
            cmds_right = np.array([0.0, -1.56, 3.0, 0.07, 0.0, 0.0, 0.5])

            # hex_log(HEX_LOG_LEVEL["info"], f"cmds: {cmds}")
            client.set_cmds(cmds_left, "left")
            client.set_cmds(cmds_right, "right")

            head_depth_hdr, head_depth_img = client.get_depth("head")
            if head_depth_hdr is not None:
                curr_ts = hex_ts_now()
                print(
                    f"head_depth_seq: {head_depth_hdr['args']}; delay: {hex_ts_delta_ms(curr_ts, head_depth_hdr['ts'])}ms"
                )
                head_depth_cmap = depth_to_cmap(head_depth_img)
                cv2.imshow("head_depth_cmap", head_depth_cmap)

            head_rgb_hdr, head_rgb_img = client.get_rgb("head")
            if head_rgb_hdr is not None:
                curr_ts = hex_ts_now()
                print(
                    f"head_rgb_seq: {head_rgb_hdr['args']}; delay: {hex_ts_delta_ms(curr_ts, head_rgb_hdr['ts'])}ms"
                )
                cv2.imshow("head_rgb_img", head_rgb_img)

            left_depth_hdr, left_depth_img = client.get_depth("left")
            if left_depth_hdr is not None:
                curr_ts = hex_ts_now()
                print(
                    f"left_depth_seq: {left_depth_hdr['args']}; delay: {hex_ts_delta_ms(curr_ts, left_depth_hdr['ts'])}ms"
                )
                left_depth_cmap = depth_to_cmap(left_depth_img)
                cv2.imshow("left_depth_cmap", left_depth_cmap)

            left_rgb_hdr, left_rgb_img = client.get_rgb("left")
            if left_rgb_hdr is not None:
                curr_ts = hex_ts_now()
                print(
                    f"left_rgb_seq: {left_rgb_hdr['args']}; delay: {hex_ts_delta_ms(curr_ts, left_rgb_hdr['ts'])}ms"
                )
                cv2.imshow("left_rgb_img", left_rgb_img)

            right_depth_hdr, right_depth_img = client.get_depth("right")
            if right_depth_hdr is not None:
                curr_ts = hex_ts_now()
                print(
                    f"right_depth_seq: {right_depth_hdr['args']}; delay: {hex_ts_delta_ms(curr_ts, right_depth_hdr['ts'])}ms"
                )
                right_depth_cmap = depth_to_cmap(right_depth_img)
                cv2.imshow("right_depth_cmap", right_depth_cmap)

            right_rgb_hdr, right_rgb_img = client.get_rgb("right")
            if right_rgb_hdr is not None:
                curr_ts = hex_ts_now()
                print(
                    f"right_rgb_seq: {right_rgb_hdr['args']}; delay: {hex_ts_delta_ms(curr_ts, right_rgb_hdr['ts'])}ms"
                )
                cv2.imshow("right_rgb_img", right_rgb_img)

            key = cv2.waitKey(1)
            if key == ord('q'):
                break

            rate.sleep()
    finally:
        cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
