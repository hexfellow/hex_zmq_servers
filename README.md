# hex_zmq_servers

## Introduction

**`hex_zmq_servers`** is a comprehensive distributed device control framework based on ZeroMQ, providing efficient client-server communication for HEXFELLOW devices.

## Project Structure

```bash
hex_zmq_servers/
├── hex_zmq_servers/         # Core library
│   ├── robot/               # Robot devices
│   ├── cam/                 # Camera devices
│   ├── mujoco/              # Mujoco simulation devices
│   └── config/              # Default configuration files
├── examples/                # Example code
│   ├── basic/               # Basic examples (single device)
│   └── adv/                 # Advanced examples (multi-device coordination)
└── venv.sh                  # Virtual environment script
```

## Devices

### Robot

- **dummy**: Dummy robot, for testing and development
- **gello**: GELLO robot, based on Dynamixel servo
- **hexarm**: HexArm robot of HEXFELLOW

### Camera

- **dummy**: Dummy camera, for testing and development
- **berxel**: Berxel depth camera, providing RGB and depth images

### Mujoco

- **archer_y6**: Physical simulation of Archer Y6 robot
- **e3_desktop**: Physical simulation of E3 Desktop robot

## Installation

### Install from PyPI

1. For those who only want to use the library in their projects, it is recommended to install it from PyPI.

    ```bash
    pip install hex_zmq_servers[all]
    ```

2. If you don't want to install the extra dependencies for extra devices, you can run:

    ```bash
    pip install hex_zmq_servers
    ```

### Install from Source Code

1. For those who want to test the examples or contribute to the project, you can install it from source code.

    ```bash
    git clone https://github.com/hexfellow/hex_zmq_servers.git
    cd hex_zmq_servers
    ./venv.sh
    ```

2. If you don't want to install the extra dependencies for extra devices, you can run:

    ```bash
    git clone https://github.com/hexfellow/hex_zmq_servers.git
    cd hex_zmq_servers
    ./venv.sh --min
    ```

    (**Important**) Some examples would not work without the extra dependencies.

3. If you don't want to install the examples, you can run:

    ```bash
    git clone https://github.com/hexfellow/hex_zmq_servers.git
    cd hex_zmq_servers
    ./venv.sh --pkg-only
    ```

## Examples

There are two types of examples in the project:

- **basic/**: Basic examples, showing the usage of a single device
- **adv/**: Advanced examples, showing multi-device coordination

More details please refer to [examples/README.md](examples/README.md)

## Contributions

Welcome to submit issues and pull requests!

## License

Apache License 2.0

## Contact

- Author: [Dong Zhaorui](https://github.com/IBNBlank)
- Maintainer: [jecjune](https://github.com/Jecjune)
- GitHub: [hex_zmq_servers](https://github.com/hexfellow/hex_zmq_servers)
- Issue Tracker: [hex_zmq_servers](https://github.com/hexfellow/hex_zmq_servers/issues)
