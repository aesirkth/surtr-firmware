#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include "ad4111.h"
#include "networking.h"
LOG_MODULE_REGISTER(main, CONFIG_APP_LOG_LEVEL);


// K_THREAD_DEFINE(networking_t, 2048, networking_thread, NULL, NULL, NULL, 5, 0, 0);

int main() {
    LOG_INF("Hello world!");
    
    // Let's go..!
    LOG_INF("Starting ADC initializaiton...");

    // Create adc driver instances
    //const struct device *adc_dev_0 = device_get_binding(DT_LABEL(DT_INST(0, ad4111)));
    //const struct device *adc_dev_1 = device_get_binding(DT_LABEL(DT_INST(1, ad4111)));

    //if (!adc_dev_0 || !adc_dev_1) {
    //    LOG_ERR("Failed to get ADC device bindings");
    //    return;
    //}

    // Use the ADC devices
    //adc_init(adc_dev_0);
    //adc_init(adc_dev_1);

    // Fail or success! 
    LOG_INF("ADC initialization complete");
    // Application logic
		return 0;
}
