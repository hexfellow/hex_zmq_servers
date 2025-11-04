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
    HexZMQDummyClient,
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
        raise ValueError(
            f"dummy_zmq_config is not valid, missing key: {missing_key}")

    client = HexZMQDummyClient(net_config=net_config)

    rate = HexRate(1_000)
    for _ in range(2_000):
        client.single_test()
        rate.sleep()


if __name__ == '__main__':
    main()
