#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include "../modules/drivers/inc/ad4111.h"
#include "networking.h"
#include <zephyr/device.h>
#include <zephyr/devicetree.h>

#define ADC1 DT_NODELABEL(ext_adcx1)
#define ADC2 DT_NODELABEL(ext_adcx2)

LOG_MODULE_REGISTER(main);

int main(void) {
    LOG_INF("++ Initiliazing... ++");

    // Let's go..!
    LOG_INF("++ Starting ADC initialization ++");

    if (!DT_NODE_HAS_STATUS(ADC1_NODE, okay)) {
        LOG_ERR("ADC1 node is not okay");
        return -1;
    }
    if (!DT_NODE_HAS_STATUS(ADC2_NODE, okay)) {
        LOG_ERR("ADC2 node is not okay");
        return -1;
    }
    // Create adc driver instances
    //const struct device *adc1 = DEVICE_DT_GET(ADC1);
    //const struct device *adc2 = DEVICE_DT_GET(ADC2);

    /* Retrieve the device binding for the first ADC */
    // adc1 = device_get_binding("ad4111_1");
    //if (!device_is_ready(adc1)) {
    //    LOG_INF("ad4111_1 failed to get binding");
    //    return -1;  // Indicate error
    //} else {
    //  LOG_INF("ad4111_1 successfully retrieved");
    //}

    /* Retrieve the device binding for the second ADC */
    //adc2 = device_get_binding("ad4111@1"); // For debugging
    // adc2 = device_get_binding("ad4111_2");
    //if (!device_is_ready(adc2)) {
    //    LOG_ERR("ad4111_2 failed to get binding");
    //    return -1;  // Indicate error
    //} else {
    //    LOG_INF("ad4111_2 successfully retrieved");
    //}

    /* Initialize the first ADC */
    //if (adc_init(adc1) != 0) {
    //    LOG_ERR("ad4111_1 failed to initialize");
    //    return -1;  // Indicate error
    //} else {
    //    LOG_INF("ad4111_1 successfully initialized");
    //}

    /* Initialize the second ADC */
    //if (adc_init(adc2) != 0) {
    //    LOG_ERR("ad4111_2 failed to initialize");
    //    return -1;  // Indicate error
    //} else {
    //    LOG_INF("ad4111_2 successfully initialized");
    //}

    // Fail or success! 
    LOG_INF("++ Finished ADC initialization ++");

    // Application logic
    // ...

    return 0;  // Indicate success
}