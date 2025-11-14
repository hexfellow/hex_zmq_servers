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
    HexRobotHexarmClient,
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


def deadzone(var, deadzone):
    res = var.copy()
    zero_mask = np.fabs(res) < deadzone
    res[zero_mask] = 0.0
    res[~zero_mask] -= np.sign(res[~zero_mask]) * deadzone[~zero_mask]
    return res


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cfg", type=str, required=True)
    args = parser.parse_args()
    cfg = json.loads(args.cfg)

    try:
        model_path = cfg["model_path"]
        last_link = cfg["last_link"]
        use_gripper = cfg["use_gripper"]
        hexarm_master_net_cfg = cfg["hexarm_master_net_cfg"]
        hexarm_slave_net_cfg = cfg["hexarm_slave_net_cfg"]
    except KeyError as ke:
        missing_key = ke.args[0]
        raise ValueError(f"cfg is not valid, missing key: {missing_key}")

    hexarm_master_client = HexRobotHexarmClient(
        net_config=hexarm_master_net_cfg)
    hexarm_slave_client = HexRobotHexarmClient(net_config=hexarm_slave_net_cfg)
    dyn_util = DynUtil(model_path, last_link)
    comp_weight = np.array([0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5])
    comp_deadzone = np.array([7.0, 7.0, 7.0, 3.0, 2.0, 2.0, 2.0])
    if not use_gripper:
        comp_weight = comp_weight[:-1]
        comp_deadzone = comp_deadzone[:-1]

    # wait servers to work
    if not wait_client_working(hexarm_master_client):
        hex_log(HEX_LOG_LEVEL["err"], "hexarm master server is not working")
        return
    if not wait_client_working(hexarm_slave_client):
        hex_log(HEX_LOG_LEVEL["err"], "hexarm slave server is not working")
        return

    # work loop
    rate = HexRate(500)
    res_comp = False
    master_q = None
    slave_res_q = np.zeros(len(comp_weight))
    slave_res_eff = np.zeros(len(comp_weight))
    while True:
        # master
        master_states_hdr, master_states = hexarm_master_client.get_states()
        if master_states_hdr is not None:
            # get states
            master_q = master_states[:, 0]
            master_dq = master_states[:, 1]

            # calculate tau_comp
            master_arm_q = master_q[:-1] if use_gripper else master_q
            master_arm_dq = master_dq[:-1] if use_gripper else master_dq
            _, c_mat, g_vec, _, _ = dyn_util.dynamic_params(
                master_arm_q, master_arm_dq)
            master_tau_comp = c_mat @ master_arm_dq + g_vec
            if use_gripper:
                master_tau_comp = np.concatenate(
                    (master_tau_comp, np.zeros(1)), axis=0)
            if res_comp:
                master_tau_comp -= deadzone(
                    slave_res_eff,
                    comp_deadzone,
                ) * comp_weight

            # set cmds to master
            cmds = np.concatenate(
                (master_q.reshape(-1, 1), master_tau_comp.reshape(-1, 1)),
                axis=1,
            )
            _ = hexarm_master_client.set_cmds(cmds)

        # slave
        slave_states_hdr, slave_states = hexarm_slave_client.get_states()
        if slave_states_hdr is not None:
            # get states
            slave_q = slave_states[:, 0]
            slave_dq = slave_states[:, 1]
            slave_eff = slave_states[:, 2]

            # calculate slave res vars
            slave_arm_q = slave_q[:-1] if use_gripper else slave_q
            slave_arm_dq = slave_dq[:-1] if use_gripper else slave_dq
            _, c_mat, g_vec, _, _ = dyn_util.dynamic_params(
                slave_arm_q, slave_arm_dq)
            slave_tau_comp = c_mat @ slave_arm_dq + g_vec
            if use_gripper:
                slave_tau_comp = np.concatenate((slave_tau_comp, np.zeros(1)),
                                                axis=0)
            slave_res_eff = slave_eff.copy()
            slave_res_eff -= slave_tau_comp

            if master_q is not None:
                slave_res_q = slave_q - master_q
                if np.fabs(slave_res_q).max() < 0.5 and not res_comp:
                    res_comp = True

                # set cmds
                cmds = np.concatenate(
                    (master_q.reshape(-1, 1), slave_tau_comp.reshape(-1, 1)),
                    axis=1,
                )
                _ = hexarm_slave_client.set_cmds(cmds)

        rate.sleep()


if __name__ == '__main__':
    main()
