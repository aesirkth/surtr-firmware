cmake_minimum_required(VERSION 3.20.0)

set(BOARD_ROOT ${CMAKE_CURRENT_LIST_DIR})


# if(TEST_BUILD)
#     set(EXTRA_CONF_FILE ${CMAKE_CURRENT_LIST_DIR}/testing/preferences.conf)
# else()
#     set(EXTRA_CONF_FILE ${CMAKE_CURRENT_LIST_DIR}/preferences.conf)
# endif()

find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})

project(launchpad_controller)

target_sources(app PRIVATE
    src/main.c
    src/steppers.c
)

# list(APPEND CMAKE_MODULE_PATH ${ZEPHYR_BASE}/modules/nanopb)
# include(nanopb)

# set(gen_dir ${ZEPHYR_BINARY_DIR}/include/generated/)
# generate_inc_file_for_target(app src/response_small.html.bin ${gen_dir}/response_small.html.bin.inc)
# generate_inc_file_for_target(app src/response_big.html.bin   ${gen_dir}/response_big.html.bin.inc)

include(${ZEPHYR_BASE}/samples/net/common/common.cmake)

# # main
# target_sources(app PRIVATE
#     src/flight_state.c
#     src/sensors.c
#     src/communication.c
#     src/commands.c
#     src/actuation.c
#     src/filter.c
# )

# if(TEST_BUILD)
#     message(STATUS "Building test")
#     target_sources(app PRIVATE
#         testing/test_main.c
#     )
# else()
#     message(STATUS "Building app")
#     target_sources(app PRIVATE
#         src/main.c
#     )
# endif()