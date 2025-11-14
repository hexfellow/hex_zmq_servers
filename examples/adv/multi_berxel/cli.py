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


def process_depth_img(
    depth_hdr,
    depth_img,
    depth_range,
    crop,
    rotate_type,
    index,
):
    if depth_hdr is not None:
        curr_ts = hex_zmq_ts_now()
        hex_log(
            HEX_LOG_LEVEL["info"],
            f"cam_{index}: depth_seq: {depth_hdr['args']}; delay: {hex_zmq_ts_delta_ms(curr_ts, depth_hdr['ts'])}ms"
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
        cv2.imshow(f"depth_cmap_{index}", depth_cmap)


def process_rgb_img(
    rgb_hdr,
    rgb_img,
    crop,
    rotate_type,
    index,
):
    if rgb_hdr is not None:
        curr_ts = hex_zmq_ts_now()
        hex_log(
            HEX_LOG_LEVEL["info"],
            f"cam_{index}: rgb_seq: {rgb_hdr['args']}; delay: {hex_zmq_ts_delta_ms(curr_ts, rgb_hdr['ts'])}ms"
        )
        rgb_crop = rgb_img[crop[0]:crop[1], crop[2]:crop[3]]
        if rotate_type is not None:
            rgb_crop = cv2.rotate(rgb_crop, rotate_type)
        cv2.imshow(f"rgb_img_{index}", rgb_crop)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cfg", type=str, required=True)
    args = parser.parse_args()
    cfg = json.loads(args.cfg)

    try:
        depth_range = cfg["depth_range"]
        crop = cfg["crop"]
        rotate_type = ROTATE_TYPE[cfg["rotate_type"]]
        berxel_0_net_cfg = cfg["berxel_0_net_cfg"]
        berxel_1_net_cfg = cfg["berxel_1_net_cfg"]
        berxel_2_net_cfg = cfg["berxel_2_net_cfg"]
    except KeyError as ke:
        missing_key = ke.args[0]
        raise ValueError(
            f"berxel_cam_config is not valid, missing key: {missing_key}")

    client_0 = HexCamBerxelClient(net_config=berxel_0_net_cfg)
    client_1 = HexCamBerxelClient(net_config=berxel_1_net_cfg)
    client_2 = HexCamBerxelClient(net_config=berxel_2_net_cfg)

    # wait servers to work
    if not wait_client_working(client_0):
        hex_log(HEX_LOG_LEVEL["err"], "berxel_0 is not working")
        return
    if not wait_client_working(client_1):
        hex_log(HEX_LOG_LEVEL["err"], "berxel_1 is not working")
        return
    if not wait_client_working(client_2):
        hex_log(HEX_LOG_LEVEL["err"], "berxel_2 is not working")
        return

    # get intrinsic params
    intri_0 = client_0.get_intri()
    intri_1 = client_1.get_intri()
    intri_2 = client_2.get_intri()
    hex_log(HEX_LOG_LEVEL["info"], f"intri_0: {intri_0}")
    hex_log(HEX_LOG_LEVEL["info"], f"intri_1: {intri_1}")
    hex_log(HEX_LOG_LEVEL["info"], f"intri_2: {intri_2}")

    # get rgb and depth
    rate = HexRate(200)
    try:
        while True:
            depth_hdr_0, depth_img_0 = client_0.get_depth()
            process_depth_img(depth_hdr_0, depth_img_0, depth_range, crop,
                              rotate_type, 0)
            rgb_hdr_0, rgb_img_0 = client_0.get_rgb()
            process_rgb_img(rgb_hdr_0, rgb_img_0, crop, rotate_type, 0)

            depth_hdr_1, depth_img_1 = client_1.get_depth()
            process_depth_img(depth_hdr_1, depth_img_1, depth_range, crop,
                              rotate_type, 1)
            rgb_hdr_1, rgb_img_1 = client_1.get_rgb()
            process_rgb_img(rgb_hdr_1, rgb_img_1, crop, rotate_type, 1)

            depth_hdr_2, depth_img_2 = client_2.get_depth()
            process_depth_img(depth_hdr_2, depth_img_2, depth_range, crop,
                              rotate_type, 2)
            rgb_hdr_2, rgb_img_2 = client_2.get_rgb()
            process_rgb_img(rgb_hdr_2, rgb_img_2, crop, rotate_type, 2)

            key = cv2.waitKey(1)
            if key == ord('q'):
                break

            rate.sleep()
    finally:
        cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
