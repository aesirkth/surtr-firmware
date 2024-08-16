cmake_minimum_required(VERSION 3.20.0)

find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})
# zephyr_include_directories(inc)
zephyr_include_directories(src)
# zephyr_include_directories(dts/bindings)
zephyr_library()
zephyr_library_sources(
    src/ad4111.c
    src/no_os/ad717x.c
    src/no_os/no_os_spi.c
    src/no_os/no_os_util.c
    )
# zephyr_target_sources(app PRIVATE src/ad4111.c)