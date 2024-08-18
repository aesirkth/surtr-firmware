cmake_minimum_required(VERSION 3.20.0)

find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})

if(CONFIG_AD4111)
    zephyr_include_directories(inc)
    zephyr_library()
    zephyr_library_sources(
        src/ad4111.c
        src/no_os/ad717x.c
        src/no_os_spi_impl.c
        src/no_os/no_os_util.c
    )
endif()

if(CONFIG_AD4111_DUMMY)
    zephyr_include_directories(inc)
    zephyr_library()
    zephyr_library_sources(
        src/ad4111_dummy.c
    )
endif()