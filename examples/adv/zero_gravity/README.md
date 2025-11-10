# Zero Gravity Example

## Description

This example demonstrates zero gravity mode (also called free-drive or gravity compensation mode) for HexArm robot. In this mode, the robot actively compensates its own gravity, allowing operators to manually move the robot with minimal force. This is ideal for teaching programming and path planning.

## Structure

```bash
zero_gravity/
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

- Assuming you have installed the library from source code, and your `working directory` is `hex_zmq_servers/examples/adv/zero_gravity`, you can run the example by:

    ```bash
    source ../../../.venv/bin/activate
    python3 launch.py
    ```

- ⚠️ **Safety Notice**: This controls a real robot. Make sure there is enough safe space around the robot and you can cut off power at any time.
