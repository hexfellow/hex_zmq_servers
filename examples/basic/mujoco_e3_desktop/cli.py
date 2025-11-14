#!/usr/bin/env python3
# -*- coding:utf-8 -*-
################################################################
# Copyright 2025 Dong Zhaorui. All rights reserved.
# Author: Dong Zhaorui 847235539@qq.com
# Date  : 2025-09-25
################################################################

import argparse, json, time
from hex_zmq_servers import (
    HexRate,
    HEX_LOG_LEVEL,
    hex_log,
    HexMujocoE3DesktopClient,
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

    client = HexMujocoE3DesktopClient(net_config=net_config)

    # wait for mujoco to work
    for i in range(10):
        hex_log(HEX_LOG_LEVEL["info"],
                f"waiting for mujoco to work: {i * 0.5}s")
        working = client.is_working()
        if working is not None and working["cmd"] == "is_working_ok":
            client.seq_clear()
            break
        else:
            time.sleep(0.5)

    # get dofs, limits and intri
    dofs = client.get_dofs()
    limits = client.get_limits()
    intri = client.get_intri()
    hex_log(HEX_LOG_LEVEL["info"], f"dofs: {dofs}")
    hex_log(HEX_LOG_LEVEL["info"], f"limits: {limits}")
    hex_log(HEX_LOG_LEVEL["info"], f"intri: {intri}")

    # get states, rgb and depth, and set cmds
    rate = HexRate(250)
    try:
        while True:
            left_states_hdr, left_states = client.get_states("left")
            if left_states_hdr is not None:
                hex_log(
                    HEX_LOG_LEVEL["info"],
                    f"left_states_seq: {left_states_hdr['args']}; left_states_ts: {left_states_hdr['ts']}"
                )
                hex_log(HEX_LOG_LEVEL["info"],
                        f"left_states pos: {left_states[:, 0]}")
                hex_log(HEX_LOG_LEVEL["info"],
                        f"left_states vel: {left_states[:, 1]}")
                hex_log(HEX_LOG_LEVEL["info"],
                        f"left_states eff: {left_states[:, 2]}")

            right_states_hdr, right_states = client.get_states("right")
            if right_states_hdr is not None:
                hex_log(
                    HEX_LOG_LEVEL["info"],
                    f"right_states_seq: {right_states_hdr['args']}; right_states_ts: {right_states_hdr['ts']}"
                )
                hex_log(HEX_LOG_LEVEL["info"],
                        f"right_states pos: {right_states[:, 0]}")
                hex_log(HEX_LOG_LEVEL["info"],
                        f"right_states vel: {right_states[:, 1]}")
                hex_log(HEX_LOG_LEVEL["info"],
                        f"right_states eff: {right_states[:, 2]}")

            obj_states_hdr, obj_states = client.get_states("obj")
            if obj_states_hdr is not None:
                hex_log(
                    HEX_LOG_LEVEL["info"],
                    f"obj_states_seq: {obj_states_hdr['args']}; obj_states_ts: {obj_states_hdr['ts']}"
                )
                hex_log(HEX_LOG_LEVEL["info"], f"obj_states: {obj_states}")

            cmds_left = np.array([
                0.0,
                -0.0205679922,
                2.57081467,
                -0.978840246,
                0.0,
                0.0,
                0.5,
            ])
            cmds_right = np.array([
                0.0,
                -0.0205679922,
                2.57081467,
                -0.978840246,
                0.0,
                0.0,
                0.5,
            ])

            # hex_log(HEX_LOG_LEVEL["info"], f"cmds: {cmds}")
            _ = client.set_cmds(cmds_left, "left")
            _ = client.set_cmds(cmds_right, "right")

            head_depth_hdr, head_depth_img = client.get_depth("head")
            if head_depth_hdr is not None:
                print(
                    f"head_depth_seq: {head_depth_hdr['args']}; head_depth_ts: {head_depth_hdr['ts']}"
                )
                head_depth_cmap = depth_to_cmap(head_depth_img)
                cv2.imshow("head_depth_cmap", head_depth_cmap)

            head_rgb_hdr, head_rgb_img = client.get_rgb("head")
            if head_rgb_hdr is not None:
                print(
                    f"head_rgb_seq: {head_rgb_hdr['args']}; head_rgb_ts: {head_rgb_hdr['ts']}"
                )
                cv2.imshow("head_rgb_img", head_rgb_img)

            left_depth_hdr, left_depth_img = client.get_depth("left")
            if left_depth_hdr is not None:
                print(
                    f"left_depth_seq: {left_depth_hdr['args']}; left_depth_ts: {left_depth_hdr['ts']}"
                )
                left_depth_cmap = depth_to_cmap(left_depth_img)
                cv2.imshow("left_depth_cmap", left_depth_cmap)

            left_rgb_hdr, left_rgb_img = client.get_rgb("left")
            if left_rgb_hdr is not None:
                print(
                    f"left_rgb_seq: {left_rgb_hdr['args']}; left_rgb_ts: {left_rgb_hdr['ts']}"
                )
                cv2.imshow("left_rgb_img", left_rgb_img)

            right_depth_hdr, right_depth_img = client.get_depth("right")
            if right_depth_hdr is not None:
                print(
                    f"right_depth_seq: {right_depth_hdr['args']}; right_depth_ts: {right_depth_hdr['ts']}"
                )
                right_depth_cmap = depth_to_cmap(right_depth_img)
                cv2.imshow("right_depth_cmap", right_depth_cmap)

            right_rgb_hdr, right_rgb_img = client.get_rgb("right")
            if right_rgb_hdr is not None:
                print(
                    f"right_rgb_seq: {right_rgb_hdr['args']}; right_rgb_ts: {right_rgb_hdr['ts']}"
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
