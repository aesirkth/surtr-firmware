#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include <zephyr/drivers/adc.h>
#include <ad4111.h>

#include "sensors.h"

LOG_MODULE_REGISTER(sensors, CONFIG_APP_LOG_LEVEL);

void sensors_thread(void *p1, void *p2, void *p3);

K_THREAD_DEFINE(sensors_tid, 4096, sensors_thread, NULL, NULL, NULL, 5, 0, 0);

volatile _Atomic int32_t adc_channels1[12];
volatile _Atomic int32_t adc_channels2[12];

void sensors_thread(void *p1, void *p2, void *p3) {
    const struct device *ext_adc1 = DEVICE_DT_GET(DT_ALIAS(xadc1));
    const struct device *ext_adc2 = DEVICE_DT_GET(DT_ALIAS(xadc2));

    if (!device_is_ready(ext_adc1)) {
        LOG_ERR("ext_adc1 not ready");
    } else {
        LOG_INF("ext_adc1 ready");
    }

    if (!device_is_ready(ext_adc2)) {
        LOG_ERR("ext_adc2 not ready");
    } else {
        LOG_INF("ext_adc2 ready");
    }

    while (true) {
        for (int i = 0; i < 12; i++) {
            int32_t value;
            ad4111_read_channel(ext_adc1, i, &value);
            adc_channels1[i] = value;
        }

        for (int i = 0; i < 12; i++) {
            int32_t value;
            ad4111_read_channel(ext_adc2, i, &value);
            adc_channels2[i] = value;
        }
        k_msleep(1);
    }
}