#pragma once
#ifndef COLLECT_H
#define COLLECT_H

#include <stdint.h>
#include <zephyr/logging/log.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/device.h>
#include <zephyr/kernel.h>
#include "actuation.h"
#include "packet.h"

/* Write Message Queue declared in main. */
extern struct k_msgq write_msgq;

/**
 * Collect_adc():
 *      Sub-routine for ADC thread. 
 *      Reads adc values into array, creates a message and places it on queue.
 */
int collect_adc(uint32_t *adc_val, Msg *msg);

/**
 * Collect_sw():
 *      Sub-routine for ADC thread. 
 *      Creates msg with current SW states.
 *      Should also read motor1 and motor2 states.
 */
int collect_sw(uint8_t *sw, Msg *msg);

#endif