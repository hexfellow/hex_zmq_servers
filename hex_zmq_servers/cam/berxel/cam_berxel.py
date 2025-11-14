#!/usr/bin/env python3
# -*- coding:utf-8 -*-
################################################################
# Copyright 2025 Dong Zhaorui. All rights reserved.
# Author: Dong Zhaorui 847235539@qq.com
# Date  : 2025-09-14
################################################################

import cv2
import threading
import numpy as np

from ..cam_base import HexCamBase
from ...zmq_base import (
    hex_zmq_ts_now,
    HexSafeValue,
)
from ...hex_launch import hex_log, HEX_LOG_LEVEL
from berxel_py_wrapper import *

CAMERA_CONFIG = {
    "serial_number": 'P100RYB4C03M2B322',
    "exposure": 10000,
    "gain": 100,
    "frame_rate": 30,
    "sens_ts": True,
}


class HexCamBerxel(HexCamBase):

    def __init__(
        self,
        camera_config: dict = CAMERA_CONFIG,
    ):
        HexCamBase.__init__(self)

        try:
            self.__serial_number = camera_config["serial_number"]
            self.__exposure = camera_config["exposure"]
            self.__gain = camera_config["gain"]
            self.__frame_rate = camera_config["frame_rate"]
            self.__sens_ts = camera_config["sens_ts"]
        except KeyError as ke:
            missing_key = ke.args[0]
            raise ValueError(
                f"camera_config is not valid, missing key: {missing_key}")

        # variables
        # berxel variables
        self.__context = None
        self.__device = None
        # camera variables
        self.__intri = np.zeros(4)

        # open device
        if not self.__open_device(self.__serial_number):
            print("open device failed")
            return

        # start stream
        if not self.__start_stream():
            print("start stream failed")
            return

        # start work loop
        self._working.set()

    def get_intri(self) -> np.ndarray:
        self._wait_for_working()
        return self.__intri

    def get_serial_number(self) -> np.ndarray:
        self._wait_for_working()
        return self.__serial_number

    def work_loop(self, hex_values: list[HexSafeValue | threading.Event]):
        rgb_value = hex_values[0]
        depth_value = hex_values[1]
        stop_event = hex_values[2]

        rgb_count = 0
        depth_count = 0
        while self._working.is_set() and not stop_event.is_set():
            # read frame
            hawk_rgb_frame = self.__device.readColorFrame(40)
            hawk_depth_frame = self.__device.readDepthFrame(40)

            # collect rgb frame
            if hawk_rgb_frame is not None:
                ts, frame = self.__unpack_frame(hawk_rgb_frame, False)
                rgb_value.set((ts, rgb_count, frame))
                rgb_count = (rgb_count + 1) % self._max_seq_num

            # collect depth frame
            if hawk_depth_frame is not None:
                ts, frame = self.__unpack_frame(hawk_depth_frame, True)
                depth_value.set((ts, depth_count, frame))
                depth_count = (depth_count + 1) % self._max_seq_num

            self.__device.releaseFrame(hawk_rgb_frame)
            self.__device.releaseFrame(hawk_depth_frame)

        # close
        self.close()

    def __unpack_frame(self, hawk_frame: BerxelHawkFrame, depth: bool = False):
        # common variables
        berxel_ts = hawk_frame.getTimeStamp()
        ts = {
            "s": berxel_ts // 1_000_000,
            "ns": berxel_ts % 1_000_000 * 1_000,
        }
        width = hawk_frame.getWidth()
        height = hawk_frame.getHeight()

        if depth:
            # depth frame
            frame_buffer = hawk_frame.getDataAsUint16()
            frame = np.ndarray(
                shape=(height, width),
                dtype=np.uint16,
                buffer=frame_buffer,
            )
            pixel_type = hawk_frame.getPixelType()
            if pixel_type == BerxelHawkPixelType.forward_dict[
                    'BERXEL_HAWK_PIXEL_TYPE_DEP_16BIT_12I_4D']:
                frame = frame // 16
            elif pixel_type == BerxelHawkPixelType.forward_dict[
                    'BERXEL_HAWK_PIXEL_TYPE_DEP_16BIT_13I_3D']:
                frame = frame // 8
            else:
                raise ValueError(f"pixel_type: {pixel_type} not supported")
        else:
            # rgb frame
            frame_buffer = hawk_frame.getDataAsUint8()
            frame = np.ndarray(
                shape=(height, width, 3),
                dtype=np.uint8,
                buffer=frame_buffer,
            )
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        return ts if self.__sens_ts else hex_zmq_ts_now(), frame

    def __open_device(self, serial_number: str | None = None) -> bool:
        # init context
        self.__context = BerxelHawkContext()
        if self.__context is None:
            print("init failed")
            return False
        self.__context.initCamera()

        # open device
        device_list = self.__context.getDeviceList()
        if len(device_list) < 1:
            print("can not find device")
            return False
        if serial_number is not None:
            device_idx = -1

            # check serial number
            def same_serial(tar_serial, device_serial):

                def norm_serial(x):
                    if x is None:
                        return None
                    if isinstance(x, (bytes, bytearray)):
                        x = x.decode('utf-8', 'ignore')
                    x = x.replace('\x00', '').strip()
                    return x.upper()

                return norm_serial(tar_serial) == norm_serial(device_serial)

            for idx, device in enumerate(device_list):
                if same_serial(serial_number, device.serialNumber):
                    print(f"find device with serial number: {serial_number}")
                    device_idx = idx
                    break
            if device_idx == -1:
                print("can not find device with serial number")
                print("available device serial numbers:")
                for device in device_list:
                    print(f"{device.serialNumber}")
                return False
            self.__device = self.__context.openDevice(device_list[device_idx])
        else:
            print("No serial number, use first device")
            self.__device = self.__context.openDevice(device_list[0])

        if self.__device is None:
            print("open device failed")
            return False

        return True

    def __start_stream(self):
        self.__device.setColorExposureGain(self.__exposure, self.__gain)
        self.__device.setRegistrationEnable(True)
        self.__device.setFrameSync(True)
        self.__device.setSystemClock()

        intrinsic_params = self.__device.getDeviceIntriscParams()
        self.__intri[0] = intrinsic_params.colorIntrinsicParams.fx / 2
        self.__intri[1] = intrinsic_params.colorIntrinsicParams.fy / 2
        self.__intri[2] = intrinsic_params.colorIntrinsicParams.cx / 2
        self.__intri[3] = intrinsic_params.colorIntrinsicParams.cy / 2

        color_frame_mode = self.__device.getCurrentFrameMode(
            BerxelHawkStreamType.forward_dict['BERXEL_HAWK_COLOR_STREAM'])
        depth_frame_mode = self.__device.getCurrentFrameMode(
            BerxelHawkStreamType.forward_dict['BERXEL_HAWK_DEPTH_STREAM'])
        color_frame_mode.framerate = self.__frame_rate
        depth_frame_mode.framerate = self.__frame_rate
        self.__device.setFrameMode(
            BerxelHawkStreamType.forward_dict['BERXEL_HAWK_COLOR_STREAM'],
            color_frame_mode)
        self.__device.setFrameMode(
            BerxelHawkStreamType.forward_dict['BERXEL_HAWK_DEPTH_STREAM'],
            depth_frame_mode)
        ret = self.__device.startStreams(
            BerxelHawkStreamType.forward_dict['BERXEL_HAWK_DEPTH_STREAM']
            | BerxelHawkStreamType.forward_dict['BERXEL_HAWK_COLOR_STREAM'])
        if ret == 0:
            print("start stream succeed")
            return True
        else:
            print("start stream failed")
            return False

    def close(self):
        if not self._working.is_set():
            return
        self._working.clear()
        self.__stop_stream()
        self.__close_device()
        hex_log(HEX_LOG_LEVEL["info"], "HexCamBerxel closed")

    def __stop_stream(self):
        if self.__device is None:
            return False
        ret = self.__device.stopStream(
            BerxelHawkStreamType.forward_dict['BERXEL_HAWK_DEPTH_STREAM']
            | BerxelHawkStreamType.forward_dict['BERXEL_HAWK_COLOR_STREAM'])
        if ret == 0:
            return True
        else:
            return False

    def __close_device(self):
        if self.__context is None:
            return
        if self.__device is None:
            return

        ret = self.__context.clsoeDevice(self.__device)
        if ret == 0:
            print("clsoe device succeed")
        else:
            print("close device Failed")
        self.__context.destroyCamera()
