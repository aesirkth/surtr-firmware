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

# Add additional directories
target_include_directories(app PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/modules/drivers/inc
)

# Add this to your CMakeLists.txt
include(ZephyrCodeBase)

zephyr_get_include_directories_for_lang_as_string(HEADER_DIRECTORIES C)

zephyr_include_directories(
  ${HEADER_DIRECTORIES}
)

# Custom target to run QEMU without the slip.sock serial
add_custom_target(run_qemu_custom
  COMMAND ${QEMU_EXECUTABLE}
  -cpu cortex-m3
  -machine lm3s6965evb
  -nographic -vga none -net none -pidfile qemu.pid
  -chardev stdio,id=con,mux=on -serial chardev:con
  -mon chardev=con,mode=readline
  -kernel ${PROJECT_BINARY_DIR}/zephyr/zephyr.elf
  DEPENDS zephyr_elf
  WORKING_DIRECTORY ${PROJECT_BINARY_DIR}
)

add_custom_target(run_custom ALL DEPENDS run_qemu_custom)