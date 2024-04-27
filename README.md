# New Launchpad Controller Firmware

### Overview
This repository contains code to support the new launchpad controller, whose name is yet to be decided. It was based off of the [Fjalar firmware](https://github.com/aesirkth/fjalar_firmware), so some structure is reflective of the design choices made in setting up the build toolchain there.

Currently, the only supported hardware is the [new Launchpad Controller](https://github.com/aesirkth/launchpad-controller-v2) (as the name suggests) but one of the goals of this project is portability.

### dependencies
#### Zephyr SDK
Building the software is most easily done with the Zephyr SDK. This is separate thing from the Zephyr RTOS/library and is just a bundle with tools for compiling, linking and so on. Please refer to the [zephyr docs](https://docs.zephyrproject.org/latest/develop/toolchains/zephyr_sdk.html) on how to install.

#### Python
It is recommended to set up a Python virtual environment for the repository. A virtual environment is basically a sandbox isolate each project and prevent collisions between library versions. The project can be built without this but there will most likely be unexpected issues a few months down the line.

Configuring one can be as simple as running `python -m venv venv`. Every time you want to build something run `source .venv/bin/activate` to activate and enter the virtual environment.

#### West & Zephyr
The project is built and managed using [West](https://docs.zephyrproject.org/latest/develop/west/index.html). West will automatically fetch everything Zephyr related (other than the SDK).

West can be installed through pip `pip install west`. (enable your virtual environment first if you have one). Then run `west update` in the root of this repository to make West fetch Zephyr RTOS and all required dependencies.

Note, if west already was installed prior to entering the virtual environment, you must first write 'west init' when in the virtual environment before you can proceed with 'west update'.  


### Building and Flashing
#### Flight controller
Run `west build application/flight_controller/ -p auto -b fjalar -t flash` to build and flash.

### Native simulation
Simulation is not yet supported for the launchpad controller repository. Ideally, it will support compiling for `native_sim_64` allowing you to run it natively. This only works on linux, if you are on Windows try using WSL 2 (WSL 1 doesn't work).

To run natively change the board to `-b native_sim_64` and use `-t run` instead of `-t flash`
