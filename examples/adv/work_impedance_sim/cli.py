#!/usr/bin/env python3
# -*- coding:utf-8 -*-
################################################################
# Copyright 2025 Dong Zhaorui. All rights reserved.
# Author: Dong Zhaorui 847235539@qq.com
# Date  : 2025-09-25
################################################################

import argparse, json
from hex_zmq_servers import (
    HexRate,
    hex_zmq_ts_now,
    hex_zmq_ts_delta_ms,
    HEX_LOG_LEVEL,
    hex_log,
    HexMujocoArcherY6Client,
)

import cv2
import numpy as np
import os, sys, argparse, json, time
from hex_robo_utils import HexDynUtil as DynUtil
from hex_robo_utils import HexCtrlUtilMitWork as CtrlUtilWork
from hex_robo_utils import part2trans, trans2part, trans_inv
from hex_robo_utils.math_utils import trans2se3, se32trans

def wait_client_working(client, timeout: float = 5.0) -> bool:
    start_time = time.time()
    while time.time() - start_time < timeout:
        if client.is_working():
            return True
        time.sleep(0.1)
    return False


def interp_joint(cur_q, tar_joint, err_limit=0.05):
    err = tar_joint - cur_q
    max_err_fab = np.fabs(err).max()
    if max_err_fab < err_limit:
        return tar_joint, False
    else:
        err_norm = err / max_err_fab
        return cur_q + err_norm * err_limit, True


def interp_arm(cur_q, tar_joint, grip_flag, use_gripper=True, err_limit=0.05):
    mid_joint = np.zeros(7 if use_gripper else 6)
    if use_gripper:
        mid_joint[:-1], interp_flag = interp_joint(
            cur_q[:-1],
            tar_joint,
            err_limit=err_limit,
        )
        mid_joint[-1], _ = interp_joint(
            cur_q[-1],
            1.33 if grip_flag else 0.2,
            err_limit=err_limit,
        )
    else:
        mid_joint, interp_flag = interp_joint(
            cur_q,
            tar_joint[:-1],
            err_limit=err_limit,
        )
    return mid_joint, interp_flag


def interp_vec(vec, norm_limit):
    norm = np.linalg.norm(vec)
    if norm < norm_limit:
        return vec, False
    else:
        return vec * (norm_limit / norm), True


def interp_se3(se3, pos_limit=0.1, rot_limit=0.1):
    mid_se3 = np.zeros_like(se3)
    pos_se3 = se3[:3]
    rot_se3 = se3[3:]

    mid_se3[:3], pos_interp_flag = interp_vec(pos_se3, pos_limit)
    mid_se3[3:], rot_interp_flag = interp_vec(rot_se3, rot_limit)

    return mid_se3, pos_interp_flag or rot_interp_flag

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cfg", type=str, required=True)
    args = parser.parse_args()
    cfg = json.loads(args.cfg)
    hex_log(HEX_LOG_LEVEL["info"], f"cfg: {cfg}")

    try:
        mujoco_net_cfg = cfg["mujoco_net_cfg"]
        model_path = cfg["model_path"]
        end_pose = np.array(cfg["end_pose"])
        init_pose = np.array(cfg["init_pose"])  # [x, y, z, qw, qx, qy, qz]
        joint_kp = np.array(cfg["mit_cfg"]["joint_kp"])
        joint_kd = np.array(cfg["mit_cfg"]["joint_kd"])
        se3_kp = np.array(cfg["mit_cfg"]["se3_kp"])
        se3_kd = np.array(cfg["mit_cfg"]["se3_kd"])

    except KeyError as ke:
        missing_key = ke.args[0]
        raise ValueError(
            f"Work impedance simulation config is not valid, missing key: {missing_key}"
        )

    # mujoco client
    client = HexMujocoArcherY6Client(net_config=mujoco_net_cfg)
    dyn_util = DynUtil(
        model_path=model_path, 
        end_pose=end_pose,
    )
    ctrl_util_work = CtrlUtilWork()

    # wait client working
    if not wait_client_working(client):
        hex_log(HEX_LOG_LEVEL["err"], "client not working")
        return

    # get dofs, limits and intri
    dof_arr = client.get_dofs()
    dofs = {
        "robot_arm": int(dof_arr[0]),
        "robot_gripper": int(dof_arr[1]) if len(dof_arr) > 1 else None,
        "sum": int(dof_arr.sum()),
    }
    limits = client.get_limits()
    _, intri = client.get_intri()
    assert limits.shape[0] == dof_arr.sum(
    ), "The number of limits must be equal to the number of dofs"
    hex_log(HEX_LOG_LEVEL["info"], f"dofs: {dofs}")
    hex_log(HEX_LOG_LEVEL["info"], f"limits: {limits.shape}")
    hex_log(HEX_LOG_LEVEL["info"], f"intri: {intri}")

    # get states, and set cmds
    rate = HexRate(2e3)
    pos_limit = 10.1
    rot_limit = 10.2
    # Initialize target pose from init_pose
    is_init = True
    init_pos = np.array(init_pose[:3])
    init_quat = np.array(init_pose[3:])
    tar_joint = None  # Will be set after IK solution
    try:
        cur_ts = None
        cur_q = None
        cur_dq = None
        cur_eff = None
        cur_dse3 = None
        c_mat = None
        g_vec = None
        while True:
            robot_states_hdr, robot_states = client.get_states("robot")
            if robot_states_hdr is not None:
                cur_ts = hex_zmq_ts_now()
                cur_q = robot_states[:, 0]
                cur_dq = robot_states[:, 1]
                cur_eff = robot_states[:, 2]
                cur_pos, cur_quat = dyn_util.forward_kinematics(cur_q[:-1])[-1]
                trans_cur_in_base = part2trans(cur_pos, cur_quat)
                _, c_mat, g_vec, jac, _ = dyn_util.dynamic_params(
                    cur_q[:-1], cur_dq[:-1], base_frame=True)
                cur_dse3 = jac @ cur_dq[:-1]
            else:
                cur_ts = None

            if cur_ts is not None:
                cmds = None
                if is_init:
                    # Initialize target joint from init_pose using IK on first iteration
                    if tar_joint is None and cur_q is not None:
                        init_q = np.array(
                            [0.0, 0.0, 0.5, 0.0, 0.0, 0.0],
                            dtype=np.float64,
                        )
                        ik_success, ik_q, _ = dyn_util.inverse_kinematics(
                            (init_pos, init_quat),
                            init_q,
                            max_iter = 1000,
                        )
                        if ik_success:
                            tar_joint = ik_q.copy()
                            hex_log(HEX_LOG_LEVEL["info"], f"IK solved for init_pose, tar_joint: {tar_joint}")
                        else:
                            hex_log(HEX_LOG_LEVEL["err"], "IK failed for init_pose")
                            tar_joint = cur_q[:-1].copy()  # Use current joint as fallback
                        
                        # Set cmds to hold current position while waiting for IK solution
                        tau_comp = np.zeros(7)
                        tau_model = c_mat @ cur_dq[:-1] + g_vec
                        tau_comp[:-1] = tau_model
                        cmds = np.vstack(
                            (cur_q, np.zeros(7), tau_comp, joint_kp, joint_kd)).T
                    else:
                        # Try to reach target joint
                        # Use joint interpolation to reach target joint
                        mid_q = cur_q.copy()
                        mid_q, interp_flag = interp_arm(
                            cur_q,
                            tar_joint,
                            grip_flag=False,
                            use_gripper=True,
                            err_limit=0.05,
                        )
                        # Arrive target joint
                        if not interp_flag:
                            tar_joint = None
                            is_init = False
                        
                        # Calculate tau_comp
                        tau_comp = np.zeros(7)
                        tau_model = c_mat @ cur_dq[:-1] + g_vec
                        tau_comp[:-1] = tau_model
                        
                        # Calculate cmds
                        cmds = np.vstack(
                            (mid_q, np.zeros(7), tau_comp, joint_kp, joint_kd)).T
                else:
                    # # check if far away from init pose
                    # if np.linalg.norm(cur_pos - init_pos) > 0.2:
                    #     hex_log(HEX_LOG_LEVEL["info"], "Far away from init pose")
                    #     is_init = True
                    #     continue

                    # use init pose as target pose
                    tar_pos = init_pos
                    tar_quat = init_quat
                    trans_tar_in_base = part2trans(tar_pos, tar_quat)

                    # tar err in base frame (Cartesian space)
                    trans_err_in_base = trans_tar_in_base @ trans_inv(trans_cur_in_base)
                    se3_err_in_base = trans2se3(trans_err_in_base)

                    # mid err in base frame
                    se3_mid_in_base, _ = interp_se3(
                        se3_err_in_base,
                        pos_limit=pos_limit,
                        rot_limit=rot_limit,
                    )

                    # calculate tau_comp
                    tau_comp = np.zeros(7)
                    tau_model = c_mat @ cur_dq[:-1] + g_vec
                    tau_comp[:-1] = tau_model

                    # calculate cmds in base frame (Cartesian space)
                    se3_cmds = ctrl_util_work(
                        kp=se3_kp,
                        kd=se3_kd,
                        se3_tar=se3_mid_in_base,
                        dse3_tar=np.zeros(6),
                        se3_cur=np.zeros(6),
                        dse3_cur=cur_dse3,
                        tau_comp=np.zeros(6),
                    ).reshape(-1, 1)
                    se3_cmds[0] = -2.0

                    jnt_cmds = jac.T @ se3_cmds.reshape(-1, 1)
                    jnt_cmds = jnt_cmds.reshape(-1)
                    tau_comp[:-1] += jnt_cmds
                    cmds = np.vstack((np.zeros(7), np.zeros(7), tau_comp,
                                      np.zeros(7), np.zeros(7))).T

                    # # calc kp kd
                    # cmds = np.zeros((7, 5))
                    # cmds[:, 1] = cur_q
                    # cmds[:-1, 0] += se3_mid_in_base 
                    # cmds[:, 2] = tau_comp
                    # cmds[:-1, 3] = (jac.T @ se3_kp.reshape(-1, 1)).reshape(-1)
                    # cmds[:-1, 4] = (jac.T @ se3_kd.reshape(-1, 1)).reshape(-1)

                # set cmds
                if cmds is not None:
                    client.set_cmds(cmds)

            key = cv2.waitKey(1)
            if key == ord('q'):
                break

            rate.sleep()
    finally:
        cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
