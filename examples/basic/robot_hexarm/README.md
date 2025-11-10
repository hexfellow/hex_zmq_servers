# Robot HexArm Example

## Description

This example shows how to use HexArm robot device. It controls the HexArm robot and provides position, velocity, and torque feedback and control.

## Structure

```bash
robot_hexarm/
├── cli.py     # client code (working code)
├── cli.json   # client configuration
├── launch.py  # launch script
└── README.md  # this file
```

## Dependencies

### Hardware

- HexArm robot

### Environment

1. Find the robot IP address.

2. (**Important**) Modify the `ARM_TYPE` and `GRIPPER_TYPE` in `launch.py` to match your device model before running the example.

3. (**Important**) Modify the `DEVICE_IP` and `HEXARM_DEVICE_PORT` in `launch.py` to match your device port (e.g., `DEVICE_IP = "192.168.1.101"` and `HEXARM_DEVICE_PORT = 8439`) before running the example.
   1. `CAN0` => `8439`
   2. `CAN1` => `9439`

## Usage

- Assuming you have installed the library from source code, and your `working directory` is `hex_zmq_servers/examples/basic/robot_hexarm`, you can run the example by:

    ```bash
    source ../../../.venv/bin/activate
    python3 launch.py
    ```

- ⚠️ **Safety Notice**: This controls a real robot. Make sure there is enough safe space around the robot and you can cut off power at any time.
