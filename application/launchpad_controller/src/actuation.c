#include "actuation.h"

LOG_MODULE_REGISTER(actuation, CONFIG_APP_LOG_LEVEL);

/**
 * toggle_switch():
 *      Both gpio_pin_set_dt() and switch_states has to be updated.
 *      Toggles a single switch.
 */
void toggle_switch(int id, uint8_t state) 
{
    gpio_pin_set_dt(&switches[id - 1], state);
    sw[id - 1] = state;
}

/**
 * toggle_led(): 
 *      Toggles a single LED by configuring gpio and saving new state led data.
 */
void toggle_led(int id, uint8_t state) 
{
    gpio_pin_set_dt(&leds[id], state);
    led[id] = state;
}

/**
 * blink_leds(): 
 *      Toggles all LEDs by iterating in loop.
 */
void blink_leds(uint8_t state)
{
    for(int i = 0; i < NUM_LEDS; i++)
    {
        toggle_led(i, state);
    }
}

/**
 * read_adc():
 *      Collects first 12 adc values into adc[0-11] (ADC0)
 *      Then collects the last 12 adc values into adc[12-23] (ADC1)
 */
int read_adc(uint32_t *adc_val)
{
    for (int i = 0; i < NUM_CHANNELS_PER_ADC; i++) {
        if(ad4111_read_channel(adcs[ADC0_TAG], i, &adc_val[i]) != 0)
        {
            LOG_ERR("Error when reading ADC0");
            return 0;
        }
    }

    for (int i = 0; i < NUM_CHANNELS_PER_ADC; i++) {
        if(ad4111_read_channel(adcs[ADC1_TAG], i, &adc_val[i+NUM_CHANNELS_PER_ADC]) != 0)
        {
            LOG_ERR("Error when reading ADC1");
            return 0;
        }
    }

    return 1;
}

/**
 * update_stepper_motor():
 *      Delta is not performing the function a "delta" it is intead a TARGET VALUE...
 *      If current motor is lower than target then move forward.
 *      If current motor is higher than target then move backwards.
 *      Iterate until motor has stepped to target.
 *      Sleep 20 us between iteration to let motor breathe? not sure why?
 */
void update_stepper_motor(const int id, const uint32_t delta)
{
    while(1)
    {
        if(motor_dir_state[id] < delta)
        {
            gpio_pin_set_dt(&motor_dir_dt[id], 1);
            gpio_pin_set_dt(&motor_step_dt[id], 1);
            motor_dir_state[id] += FORWARD;
        }
        else if (motor_dir_state[id] > delta)
        {
            gpio_pin_set_dt(&motor_dir_dt[id], 0);
            gpio_pin_set_dt(&motor_step_dt[id], 1);
            motor_dir_state[id] += BACKWARD;
        }
        else 
        {
            // motor is equal to target.
            break;
        }

        k_usleep(MOTOR_PULSE_LENGTH_US);
    }
}