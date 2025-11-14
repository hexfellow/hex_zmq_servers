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
    HexRobotGelloClient,
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cfg", type=str, required=True)
    args = parser.parse_args()
    cfg = json.loads(args.cfg)

    try:
        net_config = cfg["net"]
    except KeyError as ke:
        missing_key = ke.args[0]
        raise ValueError(f"cfg is not valid, missing key: {missing_key}")

    client = HexRobotGelloClient(net_config=net_config)

    # wait for robot to work
    for i in range(5):
        hex_log(HEX_LOG_LEVEL["info"], f"waiting for robot to work: {i}s")
        working = client.is_working()
        if working is not None and working["cmd"] == "is_working_ok":
            client.seq_clear()
            break
        else:
            time.sleep(1.0)

    # get dofs
    dofs = client.get_dofs()[0]
    limits = client.get_limits()
    hex_log(HEX_LOG_LEVEL["info"], f"dofs: {dofs}")
    hex_log(HEX_LOG_LEVEL["info"], f"limits: {limits}")

    # get states and set cmds
    rate = HexRate(500)
    while True:
        states_hdr, states = client.get_states()
        if states_hdr is not None:
            curr_ts = hex_zmq_ts_now()
            hex_log(
                HEX_LOG_LEVEL["info"],
                f"states_ts: {states_hdr['ts']}; delay: {hex_zmq_ts_delta_ms(curr_ts, states_hdr['ts'])}ms"
            )
            hex_log(HEX_LOG_LEVEL["info"], f"states: {states}")

        rate.sleep()


if __name__ == '__main__':
    main()
