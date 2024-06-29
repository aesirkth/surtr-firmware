cmake_minimum_required(VERSION 3.20.0)

# set(BOARD_ROOT ${CMAKE_CURRENT_LIST_DIR})

find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})

project(launchpad_controller)

# Add source files
target_sources(app PRIVATE
    src/main.c
    src/networking.c
    modules/drivers/src/ad4111.c
)

# Include the driver directory
add_subdirectory(modules/drivers)

# Add additional directories
target_include_directories(app PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/modules/drivers
)