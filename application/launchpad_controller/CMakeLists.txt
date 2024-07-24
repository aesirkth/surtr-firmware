cmake_minimum_required(VERSION 3.20.0)

set(BOARD_ROOT ${CMAKE_CURRENT_LIST_DIR})

# Specify the overlay file
# set(DTC_OVERLAY_FILE "boards/native_sim_64.overlay")
# set(DTC_OVERLAY_FILE "boards/nucleo_h723zg.overlay")

list(APPEND ZEPHYR_EXTRA_MODULES 
    ${CMAKE_CURRENT_SOURCE_DIR}/modules/drivers
)

find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})
project(launchpad_controller)


# zephyr_include_directories(modules/drivers)
# add_subdirectory(modules/drivers) # If we use this instead of above, build fails with offsets.h
# zephyr_include_directories(modules/drivers/dts/bindings)

target_sources(app PRIVATE src/main.c)
# target_sources(app PRIVATE src/main.c)
# target_include_directories(app PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/modules/drivers)