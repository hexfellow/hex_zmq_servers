#!/usr/bin/env python3
# -*- coding:utf-8 -*-
################################################################
# Copyright 2025 Dong Zhaorui. All rights reserved.
# Author: Dong Zhaorui 847235539@qq.com
# Date  : 2025-09-25
################################################################

import argparse, json, time
import numpy as np
from hex_zmq_servers import (
    HexRate,
    HEX_LOG_LEVEL,
    hex_log,
    HexRobotGelloClient,
    HexRobotHexarmClient,
)
from hex_robo_utils import HexDynUtil as DynUtil


def wait_client_working(client, timeout: float = 5.0) -> bool:
    for _ in range(int(timeout * 10)):
        working = client.is_working()
        if working is not None and working["cmd"] == "is_working_ok":
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
        use_gripper = cfg["use_gripper"]
        gello_net_cfg = cfg["gello_net_cfg"]
        hexarm_net_cfg = cfg["hexarm_net_cfg"]
    except KeyError as ke:
        missing_key = ke.args[0]
        raise ValueError(f"cfg is not valid, missing key: {missing_key}")

    gello_client = HexRobotGelloClient(net_config=gello_net_cfg)
    hexarm_client = HexRobotHexarmClient(net_config=hexarm_net_cfg)
    dyn_util = DynUtil(model_path, last_link)

    # wait servers to work
    if not wait_client_working(gello_client):
        hex_log(HEX_LOG_LEVEL["error"], "gello server is not working")
        return
    if not wait_client_working(hexarm_client):
        hex_log(HEX_LOG_LEVEL["error"], "hexarm server is not working")
        return

    # work loop
    rate = HexRate(500)
    gello_cmds = None
    while True:
        # gello
        gello_states_hdr, gello_states = gello_client.get_states()
        if gello_states_hdr is not None:
            gello_cmds = gello_states if use_gripper else gello_states[:-1]

        # hexarm
        hexarm_states_hdr, hexarm_states = hexarm_client.get_states()
        if hexarm_states_hdr is not None:
            arm_q = hexarm_states[:,
                                  0][:-1] if use_gripper else hexarm_states[:,
                                                                            0]
            arm_dq = hexarm_states[:,
                                   1][:-1] if use_gripper else hexarm_states[:,
                                                                             1]
            _, c_mat, g_vec, _, _ = dyn_util.dynamic_params(arm_q, arm_dq)
            tau_comp = c_mat @ arm_dq + g_vec
            if use_gripper:
                tau_comp = np.concatenate((tau_comp, np.zeros(1)), axis=0)
            if gello_cmds is not None:
                cmds = np.concatenate(
                    (gello_cmds.reshape(-1, 1), tau_comp.reshape(-1, 1)),
                    axis=1)
                _ = hexarm_client.set_cmds(cmds)

        rate.sleep()


if __name__ == '__main__':
    main()
