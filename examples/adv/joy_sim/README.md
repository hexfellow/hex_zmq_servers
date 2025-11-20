# Joystick Sim Control Example

## Description

This example shows how to use a gamepad to control Mujoco Archer Y6 simulation.

## Structure

```bash
joy_sim/
├── cli.py     # client code (working code)
├── cli.json   # client configuration
├── launch.py  # launch script
└── README.md  # this file
```

## Dependencies

### Hardware

- USB gamepad

### Environment

None

## Usage

- Assuming you have installed the library from source code, and your `working directory` is `hex_zmq_servers/examples/adv/joy_sim`, you can run the example by:

    ```bash
    source ../../../.venv/bin/activate
    python3 launch.py
    ```
