#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include "ad4111.h"
#include "networking.h"
LOG_MODULE_REGISTER(main, CONFIG_APP_LOG_LEVEL);


// K_THREAD_DEFINE(networking_t, 2048, networking_thread, NULL, NULL, NULL, 5, 0, 0);

int main() {
    LOG_INF("Hello world!");
    LOG_INF("Starting ADC initializaiton...");

    //const struct device *adc1 = DEVICE_DT_GET(DT_NODELABEL(ext_adc1));
		//init_adc(adc1);

    LOG_INF("ADC initialization complete");
		return 0;
}
