#!/usr/bin/env python3
# -*- coding:utf-8 -*-
################################################################
# Copyright 2025 Dong Zhaorui. All rights reserved.
# Author: Dong Zhaorui 847235539@qq.com
# Date  : 2025-09-25
################################################################

import argparse, json, time
import numpy as np
import pygame
import pygame.locals as pygconst
from hex_zmq_servers import (
    HexRate,
    HEX_LOG_LEVEL,
    hex_log,
    HexRobotHexarmClient,
)
from hex_robo_utils import HexDynUtil as DynUtil
from hex_robo_utils import part2trans, trans2part, trans_inv, quat_mul

JOY_BUTTON_MAP = {
    "L1": 4,
    "L2": 6,
    "R1": 5,
    "R2": 7,
    "A": 0,
    "B": 1,
    "X": 3,
    "Y": 2,
    "LA": 11,
    "RA": 12,
}

JOY_AXIS_MAP = {
    "LX": 1,
    "LY": 0,
    "RX": 4,
    "RY": 3,
    "L2": 2,
    "R2": 5,
}

INIT_JOINT = np.array(
    [0.0, -0.0205679922, 2.57081467, -0.978840246, 0.0, 0.0],
    dtype=np.float64,
)
END_POSE = np.array(
    [0.0, 0.0, 0.12, 0.7071068, 0.0, -0.7071068, 0.0],
    dtype=np.float64,
)
POSE_END_IN_STABLE = [
    np.array(
        [0.0, 0.0, 0.17],
        dtype=np.float64,
    ),
    np.array(
        [0.7071068, 0.0, -0.7071068, 0.0],
        dtype=np.float64,
    ),
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


def deadzone(var, deadzone=0.1):
    if type(var) != np.ndarray:
        res = 0.0 if np.fabs(var) < deadzone else var - np.sign(var) * deadzone
    else:
        res = var.copy()
        zero_mask = np.fabs(res) < deadzone
        res[zero_mask] = 0.0
        res[~zero_mask] -= np.sign(res[~zero_mask]) * deadzone
    return res


def update_tar_pose(
    last_tar_pos,
    last_tar_quat,
    last_vel,
    last_omega,
    last_grip_flag,
    period_s,
):
    tar_pos = last_tar_pos.copy()
    tar_quat = last_tar_quat.copy()
    tar_vel = last_vel.copy()
    tar_omega = last_omega.copy()
    quit_flag = False
    reset_flag = False
    grip_flag = last_grip_flag
    for event in pygame.event.get():
        if event.type == pygconst.QUIT:
            quit_flag = True
            break
        elif event.type == pygconst.JOYAXISMOTION:
            if event.axis == JOY_AXIS_MAP["LX"]:
                tar_vel[0] = -0.5 * deadzone(event.value)
            elif event.axis == JOY_AXIS_MAP["LY"]:
                tar_vel[1] = -0.5 * deadzone(event.value)
            elif event.axis == JOY_AXIS_MAP["RY"]:
                tar_omega[2] = -deadzone(event.value)
            elif event.axis == JOY_AXIS_MAP["L2"]:
                tar_vel[2] = -0.5 * deadzone(0.5 * (event.value + 1.0))
            elif event.axis == JOY_AXIS_MAP["R2"]:
                tar_vel[2] = 0.5 * deadzone(0.5 * (event.value + 1.0))
        elif event.type == pygconst.JOYBUTTONDOWN:
            if event.button == JOY_BUTTON_MAP["X"]:
                quit_flag = True
                break
            elif event.button == JOY_BUTTON_MAP["B"]:
                reset_flag = True
                break
            elif event.button == JOY_BUTTON_MAP["A"]:
                grip_flag = True
        elif event.type == pygconst.JOYBUTTONUP:
            if event.button == JOY_BUTTON_MAP["A"]:
                grip_flag = False
        elif event.type == pygconst.JOYHATMOTION:
            tar_omega[0] = event.value[0]
            tar_omega[1] = event.value[1]

    if (not reset_flag) and (not quit_flag):
        # update target pos
        tar_pos = tar_pos + tar_vel * period_s

        # update target quat
        delta_angle = tar_omega * period_s
        delta_angle_norm = np.linalg.norm(delta_angle)
        if delta_angle_norm > 1e-6:
            angle_axis = delta_angle / delta_angle_norm
            cos_theta = np.cos(delta_angle_norm * 0.5)
            sin_theta = np.sin(delta_angle_norm * 0.5)
            delta_quat = np.array([
                cos_theta,
                angle_axis[0] * sin_theta,
                angle_axis[1] * sin_theta,
                angle_axis[2] * sin_theta,
            ])
            tar_quat = quat_mul(tar_quat, delta_quat)

    return tar_pos, tar_quat, tar_vel, tar_omega, quit_flag, reset_flag, grip_flag


def interp_joint(cur_q, tar_joint, err_limit=0.05):
    err = tar_joint - cur_q
    max_err_fab = np.fabs(err).max()
    if max_err_fab < err_limit:
        return tar_joint, False
    else:
        err_norm = err / max_err_fab
        return cur_q + err_norm * err_limit, True


def interp_arm(cur_q, tar_joint, grip_flag, use_gripper, err_limit=0.05):
    mid_joint = np.zeros(7 if use_gripper else 6)
    if use_gripper:
        mid_joint[:-1], interp_flag = interp_joint(cur_q[:-1],
                                                   tar_joint,
                                                   err_limit=err_limit)
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cfg", type=str, required=True)
    args = parser.parse_args()
    cfg = json.loads(args.cfg)

    try:
        model_path = cfg["model_path"]
        last_link = cfg["last_link"]
        use_gripper = cfg["use_gripper"]
        hexarm_net_cfg = cfg["hexarm_net_cfg"]
    except KeyError as ke:
        missing_key = ke.args[0]
        raise ValueError(f"cfg is not valid, missing key: {missing_key}")

    hexarm_client = HexRobotHexarmClient(net_config=hexarm_net_cfg)
    dyn_util = DynUtil(
        model_path=model_path,
        last_link=last_link,
        end_pose=END_POSE,
    )

    pygame.init()
    pygame.joystick.init()
    if pygame.joystick.get_count() != 0:
        joystick = pygame.joystick.Joystick(0)
        joystick.init()
        print(f"Connected to joystick: {joystick.get_name()}")
    else:
        hex_log(
            HEX_LOG_LEVEL["err"],
            "No joystick detected. Please connect the joystick and restart the program."
        )
        return

    # wait servers to work
    if not wait_client_working(hexarm_client):
        hex_log(HEX_LOG_LEVEL["err"], "hexarm server is not working")
        return

    # work loop
    hz = 500.0
    period_s = 1.0 / hz
    rate = HexRate(hz)
    err_limit = 0.1
    cur_q = None
    tau_comp = np.zeros(7 if use_gripper else 6)
    tar_joint = INIT_JOINT.copy()
    tar_pos, tar_quat = dyn_util.forward_kinematics(tar_joint)[-1]
    tar_vel = np.zeros(3)
    tar_omega = np.zeros(3)
    grip_flag = False
    trans_stable_in_end = part2trans(
        POSE_END_IN_STABLE[0],
        POSE_END_IN_STABLE[1],
    )
    trans_end_in_stable = trans_inv(trans_stable_in_end)
    while True:
        # current states
        hexarm_states_hdr, hexarm_states = hexarm_client.get_states()
        if hexarm_states_hdr is not None:
            cur_q = hexarm_states[:, 0]
            cur_dq = hexarm_states[:, 1]
            arm_q = cur_q[:-1] if use_gripper else cur_q
            arm_dq = cur_dq[:-1] if use_gripper else cur_dq
            _, c_mat, g_vec, _, _ = dyn_util.dynamic_params(arm_q, arm_dq)
            tau_comp = c_mat @ arm_dq + g_vec
            if use_gripper:
                tau_comp = np.concatenate((tau_comp, np.zeros(1)), axis=0)

        if cur_q is not None:
            # update target pose
            tar_pos, tar_quat, tar_vel, tar_omega, quit_flag, reset_flag, grip_flag = update_tar_pose(
                tar_pos, tar_quat, tar_vel, tar_omega, grip_flag, period_s)
            if quit_flag:
                hex_log(HEX_LOG_LEVEL["info"], "Joystick Quit")
                break

            if reset_flag:
                hex_log(HEX_LOG_LEVEL["info"], "Joystick Reset")
                tar_joint = INIT_JOINT.copy()
                tar_pos, tar_quat = dyn_util.forward_kinematics(tar_joint)[-1]
            else:
                # proj pose
                tar_end_in_base = part2trans(tar_pos, tar_quat)
                tar_stable_in_base = tar_end_in_base @ trans_stable_in_end
                tar_stable_pos = tar_stable_in_base[:3, 3].copy()
                tar_stable_dist = np.linalg.norm(tar_stable_pos)
                valid_dist = np.clip(tar_stable_dist, 0.3, 0.7)
                tar_stable_pos = tar_stable_pos / tar_stable_dist * valid_dist
                tar_stable_in_base[:3, 3] = tar_stable_pos
                tar_pos, tar_quat = trans2part(
                    tar_stable_in_base @ trans_end_in_stable)

            # interp joint
            mid_joint = cur_q.copy()
            if tar_joint is not None:
                mid_joint, interp_flag = interp_arm(
                    cur_q,
                    tar_joint,
                    grip_flag,
                    use_gripper,
                    err_limit=err_limit,
                )
                # arrive target joint
                if not interp_flag:
                    tar_joint = None
            else:
                ik_success, ik_q, _ = dyn_util.inverse_kinematics(
                    (tar_pos, tar_quat),
                    cur_q[:-1] if use_gripper else cur_q,
                )
                if ik_success:
                    mid_joint, interp_flag = interp_arm(
                        cur_q,
                        ik_q,
                        grip_flag,
                        use_gripper,
                        err_limit=err_limit,
                    )
                else:
                    tar_pos, tar_quat = dyn_util.forward_kinematics(
                        cur_q[:-1] if use_gripper else cur_q)[-1]

            # set cmds
            cmds = np.concatenate(
                (mid_joint.reshape(-1, 1), tau_comp.reshape(-1, 1)),
                axis=1,
            )
            _ = hexarm_client.set_cmds(cmds)

        rate.sleep()


if __name__ == '__main__':
    main()
