cmake_minimum_required(VERSION 3.20.0)

set(BOARD_ROOT ${CMAKE_CURRENT_LIST_DIR})

list(APPEND ZEPHYR_EXTRA_MODULES
    ${CMAKE_CURRENT_SOURCE_DIR}/modules/ad4111
    ${CMAKE_CURRENT_SOURCE_DIR}/modules/drv8711
)

find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})
project(launchpad_controller)

list(APPEND CMAKE_MODULE_PATH ${ZEPHYR_BASE}/modules/nanopb)
include(nanopb)

zephyr_nanopb_sources(app src/surtr.proto)

target_sources(app PRIVATE
    src/main.c
    src/networking.c
    src/sensors.c
    src/actuation.c
    src/protocol.c
)