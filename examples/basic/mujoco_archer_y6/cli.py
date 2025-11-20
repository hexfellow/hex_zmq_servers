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
    HexMujocoArcherY6Client,
)

import cv2
import numpy as np


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
            f"archer_y6_mujoco_config is not valid, missing key: {missing_key}"
        )

    client = HexMujocoArcherY6Client(net_config=net_config)

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
            robot_states_hdr, robot_states = client.get_states("robot")
            if robot_states_hdr is not None:
                hex_log(
                    HEX_LOG_LEVEL["info"],
                    f"robot_states_seq: {robot_states_hdr['args']}; robot_states_ts: {robot_states_hdr['ts']}"
                )
                hex_log(HEX_LOG_LEVEL["info"],
                        f"robot_states pos: {robot_states[:, 0]}")
                hex_log(HEX_LOG_LEVEL["info"],
                        f"robot_states vel: {robot_states[:, 1]}")
                hex_log(HEX_LOG_LEVEL["info"],
                        f"robot_states eff: {robot_states[:, 2]}")

            obj_states_hdr, obj_states = client.get_states("obj")
            if obj_states_hdr is not None:
                hex_log(
                    HEX_LOG_LEVEL["info"],
                    f"obj_states_seq: {obj_states_hdr['args']}; obj_states_ts: {obj_states_hdr['ts']}"
                )
                hex_log(HEX_LOG_LEVEL["info"], f"obj_states: {obj_states}")

            cmds = np.array([
                0.0,
                -0.0205679922,
                2.57081467,
                -0.978840246,
                0.0,
                0.0,
                0.5,
            ])
            # hex_log(HEX_LOG_LEVEL["info"], f"cmds: {cmds}")
            _ = client.set_cmds(cmds)

            depth_hdr, depth_img = client.get_depth()
            if depth_hdr is not None:
                hex_log(
                    HEX_LOG_LEVEL["info"],
                    f"depth_seq: {depth_hdr['args']}; depth_ts: {depth_hdr['ts']}"
                )
                depth_values = depth_img.astype(np.float32)
                depth_norm = np.clip((depth_values - 70) / (1000 - 70), 0.0,
                                     1.0)
                depth_u8 = (depth_norm * 255.0).astype(np.uint8)
                depth_cmap = cv2.applyColorMap(depth_u8, cv2.COLORMAP_JET)
                cv2.imshow("depth_cmap", depth_cmap)

            rgb_hdr, rgb_img = client.get_rgb()
            if rgb_hdr is not None:
                hex_log(
                    HEX_LOG_LEVEL["info"],
                    f"rgb_seq: {rgb_hdr['args']}; rgb_ts: {rgb_hdr['ts']}")
                cv2.imshow("rgb_img", rgb_img)

            key = cv2.waitKey(1)
            if key == ord('q'):
                break

            rate.sleep()
    finally:
        cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
