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
    HexCamDummyClient,
)

import cv2


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
            f"dummy_cam_config is not valid, missing key: {missing_key}")

    # wait for camera to work
    client = HexCamDummyClient(net_config=net_config)
    for i in range(3):
        hex_log(HEX_LOG_LEVEL["info"],
                f"waiting for camera to work: {i * 0.5}s")
        working = client.is_working()
        if working is not None and working["cmd"] == "is_working_ok":
            break
        else:
            time.sleep(0.5)

    rate = HexRate(100)
    try:
        while True:
            rgb_hdr, rgb_img = client.get_rgb()
            if rgb_hdr is not None:
                curr_ts = hex_zmq_ts_now()
                hex_log(
                    HEX_LOG_LEVEL["info"],
                    f"rgb_seq: {rgb_hdr['args']}; delay: {hex_zmq_ts_delta_ms(curr_ts, rgb_hdr['ts'])}ms"
                )
                cv2.imshow("rgb_img", rgb_img)

            depth_hdr, depth_img = client.get_depth()
            if depth_hdr is not None:
                curr_ts = hex_zmq_ts_now()
                hex_log(
                    HEX_LOG_LEVEL["info"],
                    f"depth_seq: {depth_hdr['args']}; delay: {hex_zmq_ts_delta_ms(curr_ts, depth_hdr['ts'])}ms"
                )
                cv2.imshow("depth_img", depth_img)

            key = cv2.waitKey(1)
            if key == ord('q'):
                break

            rate.sleep()
    finally:
        cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
