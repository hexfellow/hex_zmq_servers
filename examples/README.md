# Examples

This directory contains the example code of `hex_zmq_servers`, showing how to use various devices and functions.

## Directory Structure

```bash
examples/
├── basic/                  # Basic examples (single device)
│   ├── robot_dummy/        # Dummy robot
│   ├── robot_gello/        # GELLO robot
│   ├── robot_hexarm/       # HexArm robot
│   ├── cam_dummy/          # Dummy camera
│   ├── cam_berxel/         # Berxel depth camera
│   ├── mujoco_archer_y6/   # Archer Y6 simulation
│   ├── mujoco_e3_desktop/  # E3 Desktop simulation
│   └── zmq_dummy/          # ZMQ communication test
└── adv/                    # Advanced examples (multi-device coordination)
    ├── gello_sim/          # GELLO + Mujoco simulation teleoperation
    ├── gello_real/         # GELLO + real robot teleoperation
    ├── joy_sim/            # Joystick + Mujoco simulation control
    ├── joy_real/           # Joystick + real robot control
    ├── force_feedback/     # Force feedback teleoperation
    └── zero_gravity/       # Zero gravity test
```

## Example Categories

### Basic Examples

- **robot_dummy**
  - Description: Dummy robot example, showing how to use robot device.
  - [Details](basic/robot_dummy/README.md)
- **robot_gello**
  - Description: GELLO robot example, showing how to use GELLO robot.
  - [Details](basic/robot_gello/README.md)
- **robot_hexarm**
  - Description: HexArm robot example, showing how to use HexArm robot.
  - [Details](basic/robot_hexarm/README.md)
- **cam_dummy**
  - Description: Dummy camera example, showing how to use camera device.
  - [Details](basic/cam_dummy/README.md)
- **cam_berxel**
  - Description: Berxel depth camera example, showing how to use Berxel RGB-D camera.
  - [Details](basic/cam_berxel/README.md)
- **mujoco_archer_y6**
  - Description: Archer Y6 simulation example, showing how to use Archer Y6 simulation.
  - [Details](basic/mujoco_archer_y6/README.md)
- **mujoco_e3_desktop**
  - Description: E3 Desktop simulation example, showing how to use E3 Desktop simulation.
  - [Details](basic/mujoco_e3_desktop/README.md)
- **zmq_dummy**
  - Description: ZMQ communication test example, showing how to communicate with the device server.
  - [Details](basic/zmq_dummy/README.md)

### Advanced Examples

- **gello_sim**
  - Description: GELLO + Mujoco simulation teleoperation example, showing how to use GELLO controller to control Mujoco simulation.
  - [Details](adv/gello_sim/README.md)
- **gello_real**
  - Description: GELLO + HexArm robot teleoperation example, showing how to use Gello controller to control HexArm robot.
  - [Details](adv/gello_real/README.md)
- **joy_sim**
  - Description: Joystick + Mujoco simulation control example, showing how to use Joystick to control Mujoco simulation.
  - [Details](adv/joy_sim/README.md)
- **joy_real**
  - Description: Joystick + HexArm robot control example, showing how to use Joystick to control HexArm robot.
  - [Details](adv/joy_real/README.md)
- **force_feedback**
  - Description: Force feedback teleoperation example, showing how to control HexArm robot using another HexArm robot with force feedback.
  - [Details](adv/force_feedback/README.md)
- **zero_gravity**
  - Description: Zero gravity test example, showing how to use torque compensation to compensate the gravity of HexArm robot.
  - [Details](adv/zero_gravity/README.md)
- **multi_berxel**
  - Description: Multi Berxel example, showing how to use multiple Berxel RGB-D camera devices.
  - [Details](adv/multi_berxel/README.md)
- **multi_launch**
  - Description: Multi launch example, showing how to use multiple launch files.
  - [Details](adv/multi_launch/README.md)
