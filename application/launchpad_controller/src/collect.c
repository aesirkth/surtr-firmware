#include "collect.h"

#include <zephyr/logging/log.h>
LOG_MODULE_REGISTER(collect, CONFIG_APP_LOG_LEVEL);

/**
 * Collect_adc():
 *      Sub-routine for ADC thread. 
 *      Reads adc values into array, creates a message and places it on queue.
 */
int collect_adc(uint32_t *adc_val, Msg *msg)
{
    if(!read_adc(adc_val))
    {
        LOG_ERR("Read_adc failed.");
        return 0;
    }

    *msg = msg_construct_with_time(sizeof(adc_val), (uint8_t*) adc_val);
    if(k_msgq_put(&write_msgq, msg->data, K_NO_WAIT) != 0)
    {
        //LOG_WRN("Message could not be placed on queue.");
        return 0;
    }

    return 1;
}

/**
 * Collect_sw():
 *      Sub-routine for ADC thread. 
 *      Creates msg with current SW states.
 *      Should also read motor1 and motor2 states.
 */
int collect_sw(uint8_t *sw, Msg *msg)
{
    *msg = msg_construct_with_time(sizeof(sw), sw);
    // Motor1 -> 0x00000000 
    // Motor2 -> 0x00000000
    if(k_msgq_put(&write_msgq, msg->data, K_NO_WAIT) != 0)
    {
        //LOG_WRN("Message could not be placed on queue.");
        return 0;
    }

    return 1;
}