# Mujoco Archer Y6 Example

## Description

This example shows how to use Mujoco simulation for Archer Y6 robot. It simulates the Archer Y6 robot in Mujoco physics engine and provides position, velocity, torque control, as well as RGB and depth image feedback.

## Structure

```bash
mujoco_archer_y6/
├── cli.py     # client code (working code)
├── cli.json   # client configuration
├── launch.py  # launch script
└── README.md  # this file
```

## Dependencies

### Hardware

None.

### Environment

None.

## Usage

- Assuming you have installed the library from source code, and your `working directory` is `hex_zmq_servers/examples/basic/mujoco_archer_y6`, you can run the example by:

    ```bash
    source ../../../.venv/bin/activate
    python3 launch.py
    ```

- The Mujoco visualization window will open automatically.
