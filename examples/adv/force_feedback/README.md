# Force Feedback Teleoperation Example

## Description

This example demonstrates bilateral teleoperation with force feedback. The master HexArm can feel the forces encountered by the slave HexArm, providing realistic haptic feedback for improved operation precision and safety.

## Structure

```bash
force_feedback/
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

3. (**Important**) Modify the `DEVICE_IP`, `MASTER_DEVICE_PORT` and `SLAVE_DEVICE_PORT` in `launch.py` to match your device port (e.g., `DEVICE_IP = "192.168.1.101"`, `MASTER_DEVICE_PORT = 8439` and `SLAVE_DEVICE_PORT = 9439`) before running the example.
   1. `CAN0` => `8439`
   2. `CAN1` => `9439`

## Usage

- Assuming you have installed the library from source code, and your `working directory` is `hex_zmq_servers/examples/adv/force_feedback`, you can run the example by:

    ```bash
    source ../../../.venv/bin/activate
    python3 launch.py
    ```
