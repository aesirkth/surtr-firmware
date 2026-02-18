#pragma once
#ifndef ACTUATION_H
#define ACTUATION_H

#include <zephyr/kernel.h>
#include <zephyr/drivers/adc.h>
#include <zephyr/logging/log.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/device.h>
#include <ad4111.h>
#include <stdint.h>

#define NUM_LEDS                2
#define NUM_EXT_ADC				2
#define ADC0_TAG                0
#define ADC1_TAG                1
#define NUM_ADC_CHHANNELS		24
#define NUM_CHANNELS_PER_ADC	12
#define NUM_SWITCHES 			8
#define NUM_STEPPERS			1	// board can hold 3.
#define MOTOR_CURRENT_I_LIMIT	2000
#define MOTOR1_INDEX			0
#define MOTOR_PULSE_LENGTH_US   20
#define FORWARD                 1
#define BACKWARD                (-1)


/* Devices declared in main. */
extern const struct device *adcs[];
extern const struct device *steppers[];

/* GPIOs declared in main. */
extern const struct gpio_dt_spec leds[];
extern const struct gpio_dt_spec switches[];
extern const struct gpio_dt_spec motor_dir_dt[];
extern const struct gpio_dt_spec motor_step_dt[];

/* global data declared in main. */
extern uint32_t motor_dir_state[NUM_STEPPERS];
extern uint8_t sw[NUM_SWITCHES];
extern uint8_t led[NUM_LEDS];


/**
 * toggle_switch():
 *      Both gpio_pin_set_dt() and switch_states has to be updated.
 *      Toggles a single switch.
 */
void toggle_switch(int id, uint8_t state);

/**
 * toggle_led(): 
 *      Toggles a single LED 
 */
void toggle_led(int id, uint8_t state);

/**
 * blink_leds(): 
 *      Toggles all LEDs.
 */
void blink_leds(uint8_t state);

/**
 * read_adc():
 *      Collects first 12 adc values into adc[0-11] (ADC0)
 *      Then collects the last 12 adc values into adc[12-23] (ADC1)
 */
int read_adc(uint32_t *adc_val);

/**
 * update_stepper_motor():
 *      Delta is not performing the function a "delta" it is intead a TARGET VALUE...
 *      If current motor is lower than target then move forward.
 *      If current motor is higher than target then move backwards.
 *      Iterate until motor has stepped to target.
 *      Sleep 20 us between iteration to let motor breathe? not sure why?
 */
void update_stepper_motor(int id, const uint32_t delta);

#endif