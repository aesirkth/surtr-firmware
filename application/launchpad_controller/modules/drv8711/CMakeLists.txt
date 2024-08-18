cmake_minimum_required(VERSION 3.20.0)

find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})

if(CONFIG_DRV8711)
    zephyr_include_directories(src)
    zephyr_library()
    zephyr_library_sources(src/drv8711.c)
endif()

if(CONFIG_DRV8711_DUMMY)
    zephyr_include_directories(src)
    zephyr_library()
    zephyr_library_sources(src/drv8711_dummy.c)
endif()