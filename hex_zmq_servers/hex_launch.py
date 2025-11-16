#!/usr/bin/env python3
# -*- coding:utf-8 -*-
################################################################
# Copyright 2025 Dong Zhaorui. All rights reserved.
# Author: Dong Zhaorui 847235539@qq.com
# Date  : 2025-09-25
################################################################

from __future__ import annotations

import json
import os, sys, signal, subprocess, threading, time
import termios
import importlib.util

from datetime import datetime
from pathlib import Path

HEX_LOG_LEVEL = {
    "info": 0,
    "warn": 1,
    "err": 2,
}


def hex_log(level: int, message):
    print(f"[{level}] {message}")


def hex_err(message):
    print(message, file=sys.stderr)


def dict_update(dict_raw: dict, dict_new: dict, add_new: bool = False):
    for key, value in dict_new.items():
        if key in dict_raw:
            if isinstance(dict_raw[key], dict) and isinstance(value, dict):
                dict_update(dict_raw[key], value)
            else:
                dict_raw[key] = value
        elif add_new:
            dict_raw[key] = value


class HexNodeConfig():

    def __init__(
        self,
        init_params: dict[str, dict] | list[dict] | HexNodeConfig = {},
    ):
        len_init_params = len(init_params)
        if isinstance(init_params, list):
            self._cfgs_dict = {cfg["name"]: cfg for cfg in init_params}
        elif isinstance(init_params, dict):
            self._cfgs_dict = init_params
            if len_init_params != len(self._cfgs_dict):
                raise ValueError(f"Invalid init_params: {init_params}")
        elif isinstance(init_params, HexNodeConfig):
            self._cfgs_dict = init_params._cfgs_dict
        else:
            raise ValueError(f"Invalid init_params: {init_params}")

        assert len(self._cfgs_dict
                   ) == len_init_params, f"Invalid init_params: {init_params}"

    def __len__(self) -> int:
        return len(self._cfgs_dict)

    def get_cfgs(self, use_list: bool = True) -> list[dict]:
        if use_list:
            return list(self._cfgs_dict.values())
        else:
            return self._cfgs_dict

    def add_cfgs(
        self,
        node_cfgs: list[dict] | dict[str, dict] | HexNodeConfig,
    ):
        new_cfgs = {}
        if isinstance(node_cfgs, list):
            new_cfgs = {cfg["name"]: cfg for cfg in node_cfgs}
        elif isinstance(node_cfgs, dict):
            new_cfgs = node_cfgs
        elif isinstance(node_cfgs, HexNodeConfig):
            new_cfgs = node_cfgs.get_cfgs(use_list=False)
        else:
            raise ValueError(f"Invalid node_cfgs: {node_cfgs}")

        print(f"new_cfgs: {new_cfgs}")
        print(f"self._cfgs_dict: {self._cfgs_dict}")
        dict_update(self._cfgs_dict, new_cfgs, add_new=True)
        print(f"self._cfgs_dict: {self._cfgs_dict}")

    def __str__(self) -> str:
        print_str = f"[HexNodeConfig] Total {len(self._cfgs_dict)} nodes:\n"
        for name in self._cfgs_dict.keys():
            print_str += f"  - {name}\n"
        return print_str

    @staticmethod
    def get_node_cfgs(
        launch_path: str,
        node_params_dict: dict = {},
    ) -> HexNodeConfig:
        # normalize the path
        launch_path = os.path.abspath(launch_path)
        if not os.path.exists(launch_path):
            raise FileNotFoundError(f"Launch file not found: {launch_path}")

        # load the module dynamically
        spec = importlib.util.spec_from_file_location("launch_module",
                                                      launch_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Failed to load module from: {launch_path}")

        # load module
        launch_module = importlib.util.module_from_spec(spec)
        sys.modules["launch_module"] = launch_module
        spec.loader.exec_module(launch_module)

        # check if `get_node_cfgs` function exists
        if not hasattr(launch_module, "get_node_cfgs"):
            raise AttributeError(
                f"Function 'get_node_cfgs' not found in {launch_path}")

        # call `get_node_cfgs` function
        get_node_cfgs_func = getattr(launch_module, "get_node_cfgs")
        node_cfgs_list = get_node_cfgs_func(node_params_dict)
        return HexNodeConfig(node_cfgs_list)


class HexLaunch:

    def __init__(
        self,
        node_cfgs: list[dict] | dict[str, dict] | HexNodeConfig,
        log_dir: str = "logs",
        min_level: int = HEX_LOG_LEVEL["warn"],
    ):
        if isinstance(node_cfgs, list):
            node_cfgs = HexNodeConfig(node_cfgs)
        elif isinstance(node_cfgs, dict):
            node_cfgs = HexNodeConfig(node_cfgs)
        elif isinstance(node_cfgs, HexNodeConfig):
            node_cfgs = node_cfgs
        else:
            raise ValueError(f"Invalid node_cfgs: {node_cfgs}")
        self.__node_cfgs = node_cfgs.get_cfgs(use_list=True)
        self.__state: dict[str, dict] = {}
        self.__stop_event = threading.Event()
        self.__log_dir = Path(log_dir)
        self.__log_dir.mkdir(parents=True, exist_ok=True)
        self.__min_level = min_level
        # lock state for node messages
        self.__state_lock = threading.Lock()
        self.__shutdown_called = False
        # terminal attrs
        self.__terminal_attrs = None
        self.__record_terminal_attrs()

    def __record_terminal_attrs(self):
        """record terminal attrs"""
        try:
            self.__terminal_attrs = termios.tcgetattr(sys.stdin.fileno())
            self.__terminal_attrs[3] |= (termios.ICANON | termios.ECHO)
            try:
                self.__terminal_attrs[6][termios.VMIN] = 1
                self.__terminal_attrs[6][termios.VTIME] = 0
            except Exception:
                pass
            print("[launcher] Terminal settings recorded")
        except Exception as e:
            print(f"[launcher] Failed to record terminal attrs: {e}")

    def __restore_terminal_attrs(self):
        """restore terminal attrs"""
        if self.__terminal_attrs is not None:
            try:
                termios.tcsetattr(
                    sys.stdin.fileno(),
                    termios.TCSADRAIN,
                    self.__terminal_attrs,
                )
                print("[launcher] Terminal attrs restored")
            except Exception as e:
                print(f"[launcher] Failed to restore terminal attrs: {e}")
        else:
            print("[launcher] No terminal attrs to restore")

    def __build_cmd(self, node_cfg: dict):
        # python path
        venv = node_cfg.get("venv") or None
        python_exe = os.path.join(
            venv,
            "bin",
            "python",
        ) if venv else sys.executable

        # node path
        node_path = node_cfg.get("node_path") or None
        if not node_path:
            raise ValueError("node_path is required")

        # cfg
        cfg_obj = {"name": node_cfg.get("name")}
        cfg_path = node_cfg.get("cfg_path", "") or None
        if cfg_path:
            if not os.path.exists(cfg_path):
                raise FileNotFoundError(f"cfg_path {cfg_path} not found")
            with open(cfg_path, "r", encoding="utf-8") as f:
                cfg_file = json.load(f)
                cfg_obj.update(cfg_file)
        dict_update(cfg_obj, node_cfg.get("cfg", {}))
        cfg_str = json.dumps(cfg_obj)

        # build cmd
        return [python_exe, "-u", str(node_path)] + ["--cfg", cfg_str]

    def __stream_printer(
        self,
        prefix: str,
        stream,
        is_stderr: bool,
        logfile_path: Path | None,
        min_level: int,
    ):
        logfile = logfile_path.open("a",
                                    encoding="utf-8") if logfile_path else None
        try:
            while True:
                raw = stream.readline()
                if not raw:
                    time.sleep(0.001)
                    continue
                line = raw.decode(errors="replace").rstrip("\n")

                record_flag = True
                print_start, print_end, log_start, log_end = "", "", "", ""
                if not is_stderr:
                    # parse level if present
                    level = HEX_LOG_LEVEL["info"]
                    if line.startswith("[") and "]" in line:
                        try:
                            lvl = int(line[1:line.index("]")])
                            if lvl in HEX_LOG_LEVEL.values():
                                level = lvl
                                line = line[line.index("]") + 1:].lstrip()
                        except Exception:
                            level = HEX_LOG_LEVEL["info"]

                    if level < min_level:
                        record_flag = False

                    # colored print
                    if level == HEX_LOG_LEVEL["info"]:
                        color_start, color_end = "", ""
                        level_str = "info"
                    elif level == HEX_LOG_LEVEL["warn"]:
                        color_start, color_end = "\033[33m", "\033[0m"
                        level_str = "warn"
                    elif level == HEX_LOG_LEVEL["err"]:
                        color_start, color_end = "\033[31m", "\033[0m"
                        level_str = "err"

                    print_start, print_end = f"{color_start}[{prefix}] ", f"{color_end}"
                    log_start, log_end = f"[{level_str}] ", ""
                else:
                    print_start, print_end = f"\033[31m[FATAL][{prefix}] ", "\033[0m"
                    log_start, log_end = "", ""

                print(f"{print_start}{line}{print_end}", flush=True)
                if logfile and record_flag:
                    logfile.write(f"{log_start}{line}{log_end}\n")
                    logfile.flush()
        finally:
            if logfile:
                logfile.close()

    def __start_node(self, node_cfg: dict):
        name = node_cfg.get("name", node_cfg.get("node_path"))
        env = os.environ.copy()
        env.update(node_cfg.get("env", {}) or {})
        cwd = node_cfg.get("cwd") or None
        cmd = self.__build_cmd(node_cfg)

        proc = subprocess.Popen(
            cmd,
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid,
        )

        log_path = Path(
            f"{self.__log_dir}/info/{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )
        err_path = Path(
            f"{self.__log_dir}/err/{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )
        log_path.parent.mkdir(parents=True, exist_ok=True)
        err_path.parent.mkdir(parents=True, exist_ok=True)

        log_thread = threading.Thread(target=self.__stream_printer,
                                      args=(name, proc.stdout, False, log_path,
                                            self.__min_level),
                                      daemon=True)
        err_thread = threading.Thread(target=self.__stream_printer,
                                      args=(name, proc.stderr, True, err_path,
                                            self.__min_level),
                                      daemon=True)
        log_thread.start()
        err_thread.start()

        return {
            "proc": proc,
            "threads": (log_thread, err_thread),
            "cfg": node_cfg
        }

    def __monitor_loop(self):
        print(f"[launcher] Started {len(self.__node_cfgs)} nodes")
        for node in self.__node_cfgs:
            print(
                f"[launcher] Starting {node.get('name', node.get('node_path'))}"
            )
            entry = self.__start_node(node)
            with self.__state_lock:
                self.__state[node.get("name", node.get("node_path"))] = entry

        try:
            while not self.__stop_event.is_set():
                with self.__state_lock:
                    if not self.__state:
                        break
                    state_items = list(self.__state.items())

                for name, entry in state_items:
                    proc = entry["proc"]
                    cfg_node = entry["cfg"]

                    if proc.poll() is not None:
                        print(
                            f"[launcher] Node {name} exited {proc.returncode}")
                        # Threads will stop automatically when stream ends

                        if cfg_node.get("respawn"):
                            delay = cfg_node.get("respawn_delay", 1)
                            print(
                                f"[launcher] Respawning {name} in {delay}s...")
                            time.sleep(delay)
                            new_entry = self.__start_node(cfg_node)
                            with self.__state_lock:
                                self.__state[name] = new_entry
                        else:
                            with self.__state_lock:
                                del self.__state[name]

                time.sleep(0.5)
        except KeyboardInterrupt:
            pass

    def __shutdown(self, signame):
        if self.__shutdown_called:
            return
        self.__shutdown_called = True

        print(f"[launcher] Got signal {signame}, shutting down children...")
        with self.__state_lock:
            state_items = list(self.__state.items())

        for _, entry in state_items:
            proc = entry["proc"]
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            except Exception:
                try:
                    proc.terminate()
                except Exception:
                    pass
        self.__stop_event.set()
        self.__restore_terminal_attrs()

    def run(self):
        # Set up signal handlers
        for s in (signal.SIGINT, signal.SIGTERM):
            signal.signal(
                s, lambda signum, frame: self.__shutdown(
                    signal.Signals(signum).name))

        # Start monitor in a separate thread
        monitor_thread = threading.Thread(target=self.__monitor_loop,
                                          daemon=True)
        monitor_thread.start()

        # Wait for stop event or monitor thread to finish
        while monitor_thread.is_alive() and not self.__stop_event.is_set():
            self.__stop_event.wait(timeout=0.5)

        # Give processes time to terminate gracefully
        time.sleep(1.0)

        # Force kill any remaining processes
        with self.__state_lock:
            state_items = list(self.__state.items())

        for name, entry in state_items:
            proc = entry["proc"]
            if proc.poll() is None:
                try:
                    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                except Exception:
                    try:
                        proc.kill()
                    except Exception:
                        pass

        # Wait for monitor thread to finish
        monitor_thread.join(timeout=0.5)
