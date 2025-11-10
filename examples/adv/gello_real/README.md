# GELLO Real Teleoperation Example

## Description

This example shows how to use GELLO robot to control a real HexArm robot in real-time. It demonstrates bilateral teleoperation where GELLO serves as the master device and HexArm follows its movements.

## Structure

```bash
gello_real/
├── cli.py     # client code (working code)
├── cli.json   # client configuration
├── launch.py  # launch script
└── README.md  # this file
```

## Dependencies

### Hardware

- GELLO robot device
- HexArm robot

### Environment

**For GELLO robot:**

1. Check USB connection:

    ```bash
    ls /dev/ttyUSB*
    ```

2. Set device permission:

    ```bash
    sudo chmod 666 /dev/ttyUSB0
    ```

3. (Optional) Add user to dialout group (permanent solution):

    ```bash
    sudo usermod -aG dialout $USER
    # Logout and login again
    ```

4. (**Important**) Modify the `GELLO_DEVICE` in `launch.py` to match your device port (e.g., `/dev/ttyUSB0`) before running the example.

**For HexArm robot:**

1. Find the robot IP address.

2. (**Important**) Modify the `ARM_TYPE` and `GRIPPER_TYPE` in `launch.py` to match your device model before running the example.

3. (**Important**) Modify the `DEVICE_IP` and `HEXARM_DEVICE_PORT` in `launch.py` to match your device port (e.g., `DEVICE_IP = "192.168.1.101"` and `HEXARM_DEVICE_PORT = 8439`) before running the example.
   1. `CAN0` => `8439`
   2. `CAN1` => `9439`

## Usage

- Assuming you have installed the library from source code, and your `working directory` is `hex_zmq_servers/examples/adv/gello_real`, you can run the example by:

    ```bash
    source ../../../.venv/bin/activate
    python3 launch.py
    ```
