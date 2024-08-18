#define DT_DRV_COMPAT analog_ad4111_dummy

#include "../inc/ad4111.h"
#include <zephyr/logging/log.h>


LOG_MODULE_REGISTER(ad4111, CONFIG_SENSOR_LOG_LEVEL);

static int ad4111_dummy_init(const struct device *dev) {
    LOG_INF("AD4111 dummy initialized");
    return 0;
}

static int ad4111_dummy_read_channel(const struct device *dev, int channel, int32_t *value) {
    // LOG_INF("AD717x dummy read single value on channel %d", channel);
    *value = channel * 10;
    return 0;
}

static struct ad4111_api ad4111_dummy_api = {
    .read_channel = ad4111_dummy_read_channel, //ad4111_read_register,   // Read from ADC register
};

#define AD4111_DUMMY_DEVICE_DEFINE(inst)                                \
    DEVICE_DT_INST_DEFINE(                                              \
        inst,                                                           \
        ad4111_dummy_init,                                              \
        NULL,                                                           \
        NULL,                                                           \
        NULL,                                                           \
        POST_KERNEL,                                                    \
        CONFIG_APPLICATION_INIT_PRIORITY,                               \
        &ad4111_dummy_api                                               \
    );

DT_INST_FOREACH_STATUS_OKAY(AD4111_DUMMY_DEVICE_DEFINE);
