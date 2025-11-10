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
    hex_zmq_ts_now,
    hex_zmq_ts_delta_ms,
    HEX_LOG_LEVEL,
    hex_log,
    HexCamBerxelClient,
)

import cv2
import numpy as np

ROTATE_TYPE = [
    None,
    cv2.ROTATE_90_CLOCKWISE,
    cv2.ROTATE_180,
    cv2.ROTATE_90_COUNTERCLOCKWISE,
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cfg", type=str, required=True)
    args = parser.parse_args()
    cfg = json.loads(args.cfg)

    try:
        net_config = cfg["net"]
        depth_range = cfg["depth_range"]
        crop = cfg["crop"]
        rotate_type = ROTATE_TYPE[cfg["rotate_type"]]
    except KeyError as ke:
        missing_key = ke.args[0]
        raise ValueError(
            f"berxel_cam_config is not valid, missing key: {missing_key}")

    # wait for camera to work
    client = HexCamBerxelClient(net_config=net_config)
    for i in range(30):
        hex_log(HEX_LOG_LEVEL["info"],
                f"waiting for camera to work: {i * 0.5}s")
        working = client.is_working()
        if working is not None and working["cmd"] == "is_working_ok":
            break
        else:
            time.sleep(0.5)

    # get intrinsic params
    intri = client.get_intri()
    hex_log(HEX_LOG_LEVEL["info"], f"intri: {intri}")

    # get rgb and depth
    rate = HexRate(100)
    try:
        while True:
            depth_hdr, depth_img = client.get_depth()
            if depth_hdr is not None:
                curr_ts = hex_zmq_ts_now()
                hex_log(
                    HEX_LOG_LEVEL["info"],
                    f"depth_seq: {depth_hdr['args']}; delay: {hex_zmq_ts_delta_ms(curr_ts, depth_hdr['ts'])}ms"
                )
                # if rotate_type is not None:
                #     depth_img = cv2.rotate(depth_img, rotate_type)
                # cv2.imshow("depth_img", depth_img)
                depth_crop = depth_img[crop[0]:crop[1], crop[2]:crop[3]]
                depth_values = depth_crop.astype(np.float32)
                depth_norm = np.clip(
                    (depth_values - depth_range[0]) /
                    (depth_range[1] - depth_range[0]),
                    0.0,
                    1.0,
                )
                depth_u8 = (depth_norm * 255.0).astype(np.uint8)
                depth_cmap = cv2.applyColorMap(depth_u8, cv2.COLORMAP_JET)
                if rotate_type is not None:
                    depth_cmap = cv2.rotate(depth_cmap, rotate_type)
                cv2.imshow("depth_cmap", depth_cmap)

            rgb_hdr, rgb_img = client.get_rgb()
            if rgb_hdr is not None:
                curr_ts = hex_zmq_ts_now()
                hex_log(
                    HEX_LOG_LEVEL["info"],
                    f"rgb_seq: {rgb_hdr['args']}; delay: {hex_zmq_ts_delta_ms(curr_ts, rgb_hdr['ts'])}ms"
                )
                if rotate_type is not None:
                    rgb_img = cv2.rotate(rgb_img, rotate_type)
                cv2.imshow("rgb_img", rgb_img)

            key = cv2.waitKey(1)
            if key == ord('q'):
                break

            rate.sleep()
    finally:
        cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
