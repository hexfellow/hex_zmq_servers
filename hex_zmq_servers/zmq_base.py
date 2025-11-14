#!/usr/bin/env python3
# -*- coding:utf-8 -*-
################################################################
# Copyright 2025 Dong Zhaorui. All rights reserved.
# Author: Dong Zhaorui 847235539@qq.com
# Date  : 2025-09-12
################################################################

import os, signal
import time
import zmq
import threading
import json
import numpy as np
from abc import ABC, abstractmethod

MAX_SEQ_NUM = int(1e12)

################################################################
# Time Related
################################################################


def hex_zmq_ts_now() -> dict:
    t_ns = time.time_ns()
    return {
        "s": t_ns // 1_000_000_000,
        "ns": t_ns % 1_000_000_000,
    }


def hex_zmq_ts_delta_ms(curr_ts, hdr_ts) -> float:
    try:
        return (curr_ts['s'] - hdr_ts['s']) * 1_000 + (
            curr_ts['ns'] - hdr_ts['ns']) / 1_000_000

    except Exception as e:
        print(f"hex_zmq_ts_delta_ms failed: {e}")
        return np.inf


class HexRate:

    def __init__(self, hz: float):
        if hz <= 0:
            raise ValueError("hz must be greater than 0")
        self.__period_ns = int(1_000_000_000 / hz)
        self.__next_ns = self.__now_ns() + self.__period_ns

    @staticmethod
    def __now_ns() -> int:
        return time.perf_counter_ns()

    def reset(self):
        self.__next_ns = self.__now_ns() + self.__period_ns

    def sleep(self):
        start_ns = self.__now_ns()
        remain_ns = self.__next_ns - start_ns
        if remain_ns > 0:
            time.sleep(remain_ns / 1_000_000_000.0)
            self.__next_ns += self.__period_ns
        else:
            needed_period = (start_ns - self.__next_ns) // self.__period_ns + 1
            self.__next_ns += needed_period * self.__period_ns


################################################################
# ZMQ Related
################################################################


class HexSafeValue:

    def __init__(self):
        self.__value = None
        self.__ready = threading.Event()
        self.__lock = threading.Lock()

    def set(self, value):
        with self.__lock:
            self.__value = value
            self.__ready.set()

    def get(self, timeout_s=1.0):
        if (not self.__ready.is_set()) and timeout_s > 0.0:
            print(f"no value yet, waiting for {timeout_s}s")
            self.__ready.wait(timeout_s)

        with self.__lock:
            return self.__value


NET_CONFIG = {
    "ip": "127.0.0.1",
    "port": 12345,
    "client_timeout_ms": 200,
    "server_timeout_ms": 1_000,
    "server_num_workers": 4,
}


class HexZMQClientBase(ABC):

    def __init__(self, net_config: dict = NET_CONFIG):
        self._max_seq_num = MAX_SEQ_NUM
        try:
            port = net_config["port"]
            ip = net_config["ip"]
            client_timeout_ms = net_config["client_timeout_ms"]
        except KeyError as ke:
            missing_key = ke.args[0]
            raise ValueError(
                f"net_config is not valid, missing key: {missing_key}")

        self._context = zmq.Context().instance()
        self._ip = ip
        self._port = port
        self._timeout_ms = client_timeout_ms
        self._socket = None
        self._lock = threading.Lock()
        self.__make_socket()

    def __del__(self):
        self.close()

    def __make_socket(self):
        if self._socket is not None:
            try:
                self._socket.close(0)
            except Exception:
                pass

        new_socket = self._context.socket(zmq.REQ)
        new_socket.setsockopt(zmq.LINGER, 0)
        new_socket.setsockopt(zmq.RCVTIMEO, self._timeout_ms)
        new_socket.setsockopt(zmq.SNDTIMEO, self._timeout_ms)
        new_socket.setsockopt(zmq.IMMEDIATE, 1)
        new_socket.setsockopt(zmq.TCP_KEEPALIVE, 1)
        new_socket.connect(f"tcp://{self._ip}:{self._port}")
        self._socket = new_socket

    def request(self, req_dict: dict, req_buf: np.ndarray | None = None):
        with self._lock:
            try:
                self.__send_req(req_dict, req_buf)
            except zmq.Again:
                print("client send failed; recreate socket")
                self.__make_socket()
                return None, None

            resp_hdr, resp_buf = self.__recv_resp()
            if resp_hdr is None:
                print("client recv failed; recreate socket")
                self.__make_socket()
            return resp_hdr, resp_buf

    def is_working(self):
        working_hdr, _ = self.request({"cmd": "is_working"})
        return working_hdr

    def __send_req(self, req_dict: dict, req_buf: np.ndarray | None = None):
        # construct send header
        if not "cmd" in req_dict:
            raise ValueError("`cmd` is required")
        if req_buf is None:
            req_buf = np.zeros(0, dtype=np.uint8)
        if not req_buf.flags.c_contiguous:
            req_buf = np.ascontiguousarray(req_buf)
        send_hdr = {
            "cmd": req_dict["cmd"],
            "ts": req_dict.get("ts", hex_zmq_ts_now()),
            "args": req_dict.get("args", None),
            "dtype": str(req_buf.dtype),
            "shape": tuple(req_buf.shape),
        }

        try:
            self._socket.send_multipart(
                [json.dumps(send_hdr).encode("utf-8"),
                 memoryview(req_buf)],
                copy=(req_buf.nbytes < 65536),
            )
        except zmq.Again:
            print("client send failed")
            raise

    def __recv_resp(self):
        try:
            frames = self._socket.recv_multipart()
            if len(frames) != 2:
                raise ValueError("invalid response")
            send_hdr_bytes, raw_buf = frames
            resp_hdr = json.loads(send_hdr_bytes)
            resp_buf = np.frombuffer(
                raw_buf,
                dtype=np.dtype(resp_hdr["dtype"]),
            ).reshape(
                tuple(resp_hdr["shape"]),
                order="C",
            )
            return resp_hdr, resp_buf
        except zmq.Again:
            return None, None

    def close(self):
        if self._socket is not None:
            try:
                self._socket.close(0)
            except Exception:
                pass


class HexZMQServerBase(ABC):

    def __init__(
        self,
        net_config: dict = NET_CONFIG,
    ):
        self._max_seq_num = MAX_SEQ_NUM
        try:
            port = net_config["port"]
            ip = net_config["ip"]
            num_workers = net_config["server_num_workers"]
            timeout_ms = net_config["server_timeout_ms"]
        except KeyError as ke:
            missing_key = ke.args[0]
            raise ValueError(
                f"net_config is not valid, missing key: {missing_key}")

        self._stop_event = threading.Event()
        self._num_workers = max(1, min(num_workers, os.cpu_count()))
        self._timeout_ms = timeout_ms

        self._context = zmq.Context().instance()
        self._frontend = self._context.socket(zmq.ROUTER)
        self._frontend.setsockopt(zmq.LINGER, 0)
        self._frontend.setsockopt(zmq.TCP_KEEPALIVE, 1)
        self._frontend.bind(f"tcp://{ip}:{port}")

        self._backend = self._context.socket(zmq.DEALER)
        self._backend.setsockopt(zmq.LINGER, 0)
        self._backend.bind(f"inproc://hex_workers")

        self._workers: list[threading.Thread] = []
        self._proxy_thread: threading.Thread | None = None

    def __del__(self):
        self.close()

    def _single_thread(self, worker_id: int):
        socket = self._context.socket(zmq.REP)
        socket.setsockopt(zmq.LINGER, 0)
        socket.setsockopt(zmq.RCVTIMEO, self._timeout_ms)
        socket.connect(f"inproc://hex_workers")

        while not self._stop_event.is_set():
            try:
                frames = socket.recv_multipart()
            except zmq.Again:
                continue

            try:
                if len(frames) != 2:
                    raise ValueError("invalid request")
                send_hdr_bytes, raw_buf = frames
                req_hdr = json.loads(send_hdr_bytes)
                req_buf = np.frombuffer(
                    raw_buf,
                    dtype=np.dtype(req_hdr["dtype"])).reshape(req_hdr["shape"],
                                                              order="C")

                resp_hdr, resp_buf = self._process_request(req_hdr, req_buf)

                if resp_buf is None:
                    resp_buf = np.zeros(0, dtype=np.uint8)
                if not resp_buf.flags.c_contiguous:
                    resp_buf = np.ascontiguousarray(resp_buf)
                send_hdr = {
                    "cmd": resp_hdr["cmd"],
                    "ts": resp_hdr.get("ts", hex_zmq_ts_now()),
                    "args": resp_hdr.get("args", None),
                    "dtype": str(resp_buf.dtype),
                    "shape": tuple(resp_buf.shape),
                }

                socket.send_multipart([
                    json.dumps(send_hdr).encode("utf-8"),
                    memoryview(resp_buf)
                ],
                                      copy=(resp_buf.nbytes < 65536))

            except Exception as e:
                err_hdr = {
                    "cmd": (f"{req_hdr.get('cmd')}_error"
                            if isinstance(req_hdr, dict) and "cmd" in req_hdr
                            else "error"),
                    "args": {
                        "err": str(e)
                    },
                    "ts":
                    hex_zmq_ts_now(),
                    "dtype":
                    "uint8",
                    "shape": (0, ),
                }
                socket.send_multipart(
                    [json.dumps(err_hdr).encode("utf-8"),
                     memoryview(b"")],
                    copy=True)

        socket.close(0)

    def start(self):
        for i in range(self._num_workers):
            th = threading.Thread(
                target=self._single_thread,
                args=(i, ),
                daemon=True,
            )
            th.start()
            self._workers.append(th)

        def _proxy():
            try:
                zmq.proxy(self._frontend, self._backend)
            except Exception:
                pass

        self._proxy_thread = threading.Thread(target=_proxy, daemon=True)
        self._proxy_thread.start()

    def close(self):
        self._stop_event.set()
        try:
            if self._frontend:
                self._frontend.close(0)
        except Exception:
            pass
        try:
            if self._backend:
                self._backend.close(0)
        except Exception:
            pass

    def no_ts_hdr(self, hdr: dict, ok_flag: bool) -> dict:
        return {
            "cmd": f"{hdr['cmd']}_ok"
        } if ok_flag else {
            "cmd": f"{hdr['cmd']}_failed"
        }

    @abstractmethod
    def work_loop(self):
        raise NotImplementedError(
            "`work_loop` should be implemented by the child class")

    @abstractmethod
    def _process_request(self, recv_hdr: dict, recv_buf: np.ndarray):
        raise NotImplementedError(
            "`_process_request` should be implemented by the child class")


################################################################
# Server Helper
################################################################
def hex_server_helper(cfg: dict, server_cls: type):
    try:
        net = cfg["net"]
        params = cfg["params"]
    except KeyError as ke:
        missing_key = ke.args[0]
        raise ValueError(f"cfg is not valid, missing key: {missing_key}")

    server = server_cls(net, params)

    shutdown_flag = False

    def signal_handler(signum, frame):
        nonlocal shutdown_flag
        if not shutdown_flag:
            shutdown_flag = True
            print(
                f"[server] Received signal {signal.Signals(signum).name}, shutting down..."
            )
            server._stop_event.set()

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    try:
        server.start()
        server.work_loop()
    finally:
        server.close()


################################################################
# Dummy Sample
################################################################


class HexZMQDummyClient(HexZMQClientBase):

    def __init__(
        self,
        net_config: dict = NET_CONFIG,
    ):
        HexZMQClientBase.__init__(self, net_config)

    def single_test(self):
        resp_hdr, resp_buf = self.request({"cmd": "test"})
        print(f"resp_hdr: {resp_hdr}")
        print(f"resp_buf: {resp_buf}")


class HexZMQDummyServer(HexZMQServerBase):

    def __init__(
        self,
        net_config: dict = NET_CONFIG,
        params_config: dict = {},
    ):
        HexZMQServerBase.__init__(self, net_config)

    def work_loop(self):
        try:
            while not self._stop_event.is_set():
                time.sleep(1)
        finally:
            self.close()

    def _process_request(self, recv_hdr: dict, recv_buf: np.ndarray):
        if recv_hdr["cmd"] == "test":
            print("test received")
            print(f"recv_hdr: {recv_hdr}")
            print(f"recv_buf: {recv_buf}")
            resp_hdr = {
                "cmd": "test_ok",
            }
            return resp_hdr, None
        else:
            raise ValueError(f"unknown command: {recv_hdr['cmd']}")


if __name__ == "__main__":
    import argparse, json

    parser = argparse.ArgumentParser()
    parser.add_argument("--cfg", type=str, required=True)
    args = parser.parse_args()
    cfg = json.loads(args.cfg)

    hex_server_helper(cfg, HexZMQDummyServer)
