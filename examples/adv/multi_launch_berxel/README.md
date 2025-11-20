# Multi Berxel Example

## Description

This example shows how to use multiple Berxel RGB-D camera devices using multi-launch. It captures RGB and depth images from multiple Berxel cameras.

## Structure

```bash
cam_berxel/
├── cli.py     # client code (working code)
├── cli.json   # client configuration
├── launch.py  # launch script
└── README.md  # this file
```

## Dependencies

### Hardware

- Berxel RGB-D camera

### Environment

1. Check device connection:

    ```bash
    lsusb | grep Berxel
    ```

2. If permission denied, you may need to add udev rules. For details, please refer to the [Berxel Website](https://www.hessian-matrix.com/%e4%b8%8b%e8%bd%bd%e4%b8%ad%e5%bf%83/).

3. (**Important**) Modify the `SERIAL_NUMBER` and `EXPOSURE` in `launch.py` to match your device before running the example.

## Usage

- Assuming you have installed the library from source code, and your `working directory` is `hex_zmq_servers/examples/adv/multi_berxel`, you can run the example by:

    ```bash
    source ../../../.venv/bin/activate
    python3 launch.py
    ```
