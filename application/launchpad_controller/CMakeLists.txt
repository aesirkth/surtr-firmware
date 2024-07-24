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

list(APPEND CMAKE_MODULE_PATH ${ZEPHYR_BASE}/modules/nanopb)
include(nanopb)

zephyr_nanopb_sources(app src/commands.proto)
zephyr_nanopb_sources(app src/sensor_vals.proto)

# TODO: review this later
# include(${ZEPHYR_BASE}/samples/net/common/common.cmake)

target_sources(app PRIVATE
    src/main.c
    src/steppers.c
)

# set(gen_dir ${ZEPHYR_BINARY_DIR}/include/generated/)
# generate_inc_file_for_target(app src/response_small.html.bin ${gen_dir}/response_small.html.bin.inc)
# generate_inc_file_for_target(app src/response_big.html.bin   ${gen_dir}/response_big.html.bin.inc)

target_sources(app PRIVATE src/main.c)
# target_include_directories(app PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/modules/drivers)