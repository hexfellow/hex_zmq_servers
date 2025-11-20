# GELLO Sim Teleoperation Example

## Description

This example shows how to use GELLO robot to control Mujoco Archer Y6 simulation in real-time. It demonstrates teleoperation where GELLO serves as the master device and the simulated robot follows its movements.

## Structure

```bash
gello_sim/
├── cli.py     # client code (working code)
├── cli.json   # client configuration
├── launch.py  # launch script
└── README.md  # this file
```

## Dependencies

### Hardware

- GELLO robot device

### Environment

1. Check GELLO device connection:

    ```bash
    ls /dev/ttyUSB*
    ```

2. Set device permission:

    ```bash
    sudo chmod 666 /dev/ttyUSB0
    ```

3. (**Important**) Modify the `GELLO_DEVICE` in `launch.py` to match your device port (e.g., `/dev/ttyUSB0`) before running the example.

## Usage

- Assuming you have installed the library from source code, and your `working directory` is `hex_zmq_servers/examples/adv/gello_sim`, you can run the example by:

    ```bash
    source ../../../.venv/bin/activate
    python3 launch.py
    ```
