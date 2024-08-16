#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include <zephyr/drivers/adc.h>

LOG_MODULE_REGISTER(sensors, CONFIG_APP_LOG_LEVEL);

void sensors_thread(void *p1, void *p2, void *p3);

K_THREAD_DEFINE(sensors_tid, 4096, sensors_thread, NULL, NULL, NULL, 5, 0, 0);


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
}