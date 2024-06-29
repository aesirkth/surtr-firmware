cmake_minimum_required(VERSION 3.20.0)

# Specify the overlay file early
set(DTC_OVERLAY_FILE "boards/native_sim_64.overlay")

find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})
project(launchpad_controller)

# Include directories for the drivers
zephyr_include_directories(modules/drivers/inc)
zephyr_include_directories(modules/drivers/dts/bindings)

# Add source files for the drivers
target_sources(app PRIVATE src/main.c src/networking.c modules/drivers/src/ad4111.c)