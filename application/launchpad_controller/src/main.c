#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include "../modules/drivers/inc/ad4111.h"
#include "networking.h"

LOG_MODULE_REGISTER(main);

int main(void) {
    LOG_INF("++ Initiliazing... ++");

    // Let's go..!
    LOG_INF("++ Starting ADC initialization ++");

    // Create adc driver instances
    const struct device *adc1;
    const struct device *adc2;

    /* Retrieve the device binding for the first ADC */
    //adc1 = device_get_binding("AD4111_1"); // For debugging
    adc1 = DEVICE_DT_GET(DT_NODELABEL(ad4111_1));

    // adc1 = device_get_binding("ad4111_1");
    if (!device_is_ready(adc1)) {
        LOG_INF("ad4111_1 failed to get binding");
        return -1;  // Indicate error
    } else {
      LOG_INF("ad4111_1 successfully retrieved");
    }

    /* Retrieve the device binding for the second ADC */
    adc2 = device_get_binding("ad4111@1"); // For debugging
    // adc2 = device_get_binding("ad4111_2");
    if (!adc2) {
        LOG_ERR("ad4111_2 failed to get binding");
        return -1;  // Indicate error
    } else {
        LOG_INF("ad4111_2 successfully retrieved");
    }

    /* Initialize the first ADC */
    if (adc_init(adc1) != 0) {
        LOG_ERR("ad4111_1 failed to initialize");
        return -1;  // Indicate error
    } else {
        LOG_INF("ad4111_1 successfully initialized");
    }

    /* Initialize the second ADC */
    if (adc_init(adc2) != 0) {
        LOG_ERR("ad4111_2 failed to initialize");
        return -1;  // Indicate error
    } else {
        LOG_INF("ad4111_2 successfully initialized");
    }

    // Fail or success! 
    LOG_INF("++ Finished ADC initialization ++");

    // Application logic
    // ...

    return 0;  // Indicate success
}