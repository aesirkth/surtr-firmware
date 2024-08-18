#define DT_DRV_COMPAT ti_drv8711_dummy

#include <zephyr/drivers/spi.h>
#include <zephyr/input/input.h>
#include <zephyr/kernel.h>

#include <zephyr/logging/log.h>

#include "drv8711.h"

LOG_MODULE_REGISTER(drv8711, CONFIG_DRV8711_LOG_LEVEL);


int drv8711_dummy_init(const struct device* dev) {
    LOG_INF("Initialized dummy drv8711 driver");
    return 0;
}

int drv8711_dummy_enable(const struct device* dev, bool enabled) {
    return 0;
}

int drv8711_dummy_set_microstep(const struct device* dev, Drv8711MicrostepResolution_t resolution) {
    return 0;
}

int drv8711_dummy_set_current_limit(const struct device* dev, uint16_t current) {
    return 0;
}

struct drv8711_driver_api drv8711_dummy_api = {
    .set_current_limit = drv8711_dummy_set_current_limit,
    .set_microstep = drv8711_dummy_set_microstep,
    .enable = drv8711_dummy_enable
};

#define DRV8711_SPI_CS_HOLD_DELAY 2 //us

// CONFIG_APPLICATION_INIT_PRIORITY is 90 in autoconf.h
#define DRV8711_DUMMY_DEVICE_DEFINE(inst)                                       \
    DEVICE_DT_INST_DEFINE(                                                      \
        inst,                                                                   \
        drv8711_dummy_init,                                                     \
        NULL,                                                                   \
        NULL,                                                                   \
        NULL,                                                                   \
        POST_KERNEL,                                                            \
        CONFIG_APPLICATION_INIT_PRIORITY,                                       \
        &drv8711_dummy_api                                                      \
        );


DT_INST_FOREACH_STATUS_OKAY(DRV8711_DUMMY_DEVICE_DEFINE)