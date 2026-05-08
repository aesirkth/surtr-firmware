#pragma once
#ifndef IN_H
#define IN_H

#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include <stdint.h>
#include "packet.h"
#include "actuation.h"


#define ADC_ARRAY_BYTE_SIZE 96
#define NUM_ADC_CHANNELS    24

#define SURTR_MSG_SW_CTRL_INDEX_CMD			0
#define SURTR_MSG_SW_CTRL_INDEX_ID			1
#define SURTR_MSG_SW_CTRL_INDEX_STATE		2

#define SURTR_MSG_STEP_CTRL_INDEX_CMD		0
#define SURTR_MSG_STEP_CTRL_INDEX_ID		1
#define SURTR_MSG_STEP_CTRL_INDEX_DELTA		2

#define SURTR_MSG_ACK_SUCCESS   	0xFF
#define SURTR_MSG_ACK_FAIL			0x00

#define SURTR_RESPONSE_INDEX_CMD	0
#define SURTR_RESPONSE_INDEX_ACK	1
#define SURTR_RESPONSE_INDEX_TIME	2
#define SURTR_RESPONSE_INDEX_DATA	10

extern struct k_sem sem_sampling_irq;

/**
 * ==========================================================
 * surtr_syn_ack():
 *      Add ACK response 0xFF (SUCCESS) to response message.
 */
void surtr_syn_ack(uint8_t *response, uint8_t *response_size);

/**
 * ==========================================================
 * surtr_syn_fail():
 *      Add ACK response 0x00 (FAIL) to response message.
 */
void surtr_syn_fail(uint8_t *response, uint8_t *response_size);

/**
 * ==========================================================
 * surtr_sw_ctrl():
 *      Dissects message and applies control command on desired switch.
 *      Paired together with ACK on response for confirmation.
 *      MSG TYPE		ENUM	TIME (us)		RAW DATA
 *      ===============================================================
 *      SW CTRL 1 | ID | STATE |
 */
int surtr_sw_ctrl(const uint8_t id, const uint8_t state);

/**
 * ==========================================================
 * surtr_step_ctrl():
 *      Dissects message and applies control command on desired motor.
 *      Delta is not really delta here but in reality the TARGET VALUE...
 *      ===============================================================
 *      STEP CTRL		2					| ID | MOTOR DELTA |
 */
void surtr_step_ctrl(const uint8_t *payload);

/**
 * ==========================================================
 * surtr_get_adc_state():
 *      Reads state of ADCs and combines into surtr response message.
 *      data begins after 10 bytes and then is 96 bytes long.
 *      MSG TYPE		ENUM	TIME (us)		RAW DATA
 *      ===============================================================
 *      ADC STATE		4					| VALUE[24] |
 */
int surtr_get_adc_state(uint8_t *response, uint8_t *response_size);

/**
 * ==========================================================
 * surtr_get_sw_state():
 *      Reads state of SWs and combines into surtr response message.
 *      data begins after 10 bytes and then is 8 bytes long.
 *      MSG TYPE		ENUM	TIME (us)		RAW DATA
 *      ===============================================================
 *      SW STATE		    3					| SW[8] 
 */
int surtr_get_sw_state(uint8_t *response, uint8_t *response_size);

void sampling_isr(struct k_timer *timer_id);

#endif