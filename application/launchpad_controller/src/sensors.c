#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include <zephyr/drivers/adc.h>
#include <ad4111.h>

#include "sensors.h"
#include "protocol.h"
#include "networking.h"

LOG_MODULE_REGISTER(sensors, CONFIG_APP_LOG_LEVEL);

void sensors_thread(void *p1, void *p2, void *p3);

// Define the thread for the sensors. 4096 bytes of stack space.
K_THREAD_DEFINE(sensors_tid, 4096, sensors_thread, NULL, NULL, NULL, 5, 0, 0);

void sensors_thread(void *p1, void *p2, void *p3) {
    // Get the devices for the external ADCs. (Analog to Digital Converters)
    //! These probably convert analog sensor signals to digital signals.
    const struct device *ext_adc1 = DEVICE_DT_GET(DT_ALIAS(xadc1));
    const struct device *ext_adc2 = DEVICE_DT_GET(DT_ALIAS(xadc2));

    // Check if the ADCs are ready.
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

    const struct device *adcs[2] = {ext_adc1, ext_adc2};
    while (true) {
        // Loop through the ADCs (only two a.t.m.)
        for (int i = 0; i < 2; i++) {
            if (i == 1) {
                //continue;
            }
            int32_t adc_values[12];

            // Start composing a protobuf message. pb = protobuf
            surtrpb_SurtrMessage msg;
            msg.has_us_since_boot = true; // us = microseconds
            msg.us_since_boot = k_uptime_get() * 1000;
            msg.which_command = surtrpb_SurtrMessage_adc_measurements_tag; // Selects the right command code from the associated alias.
           
            // Loop through the channels of the ADC (ad4111). There are 12 channels on each ADC.
            // Sensors can be connect to any of the 12 channels.
            //! Shouldn't the ad4111 have 16 channels?
            for (int j = 0; j < 12; j++) {
                ad4111_read_channel(adcs[i], j, &adc_values[j]); // Reads the value of the channel and stores it in the adc_values array.

                // if (j < 8) {
                //     LOG_INF("Channel %d: %fV (%d)", j, adc_values[j] * 2.5 / ( (1 << 24) * 50) * 1000, adc_values[j]);
                // } else {
                //     LOG_INF("Channel %d: %fmA (%d)", j, adc_values[j] * 2.5 / ((1 << 24) * 0.1), adc_values[j]);
                // }
            }

            // Update the protobuf message with the values of the ADC channels
            msg.command.adc_measurements.id = i;
            msg.command.adc_measurements.value0 = adc_values[0];
            msg.command.adc_measurements.value1 = adc_values[1];
            msg.command.adc_measurements.value2 = adc_values[2];
            msg.command.adc_measurements.value3 = adc_values[3];
            msg.command.adc_measurements.value4 = adc_values[4];
            msg.command.adc_measurements.value5 = adc_values[5];
            msg.command.adc_measurements.value6 = adc_values[6];
            msg.command.adc_measurements.value7 = adc_values[7];
            msg.command.adc_measurements.value8 = adc_values[8];
            msg.command.adc_measurements.value9 = adc_values[9];
            msg.command.adc_measurements.value10 = adc_values[10];
            msg.command.adc_measurements.value11 = adc_values[11];

            // Send the message using the networking thread.
            send_msg(&msg); //! Where is the message sent to?
            k_msleep(10);
        }


        // int32_t value = 42;
        // int e = ad4111_read_channel(ext_adc1, 4, &value);
        // LOG_INF("Bajs %d %d", value, e);
        // k_msleep(1000);
    }
}