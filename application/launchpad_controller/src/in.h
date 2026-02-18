#pragma once
#ifndef IN_H
#define IN_H

#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/device.h>
#include <stdint.h>
#include "server.h"
#include "packet.h"
#include "actuation.h"

#define SURTR_CMD_SYN_ACK       0
#define SURTR_CMD_SW_CTRL       1
#define SURTR_CMD_STEP_CTRL     2
#define SURTR_CMD_SW_STATE      3
#define SURTR_CMD_ADC_STATE     4
#define SURTR_CMD_IGNITION      5

#define SURTR_MSG_SW_CTRL_ID    1
#define SURTR_MSG_SW_CTRL_STATE 2

#define SURTR_MSG_STEP_CTRL_ID      1
#define SURTR_MSG_STEP_CTRL_DELTA   2

#define SURTR_CMD_INDEX         0

#define SURTR_MSG_ACK           0xFF
#define SURTR_MSG_ACK_SIZE      2

/* Write Message Queue declared in main. */
extern struct k_msgq write_msgq;

/**
 * execute_command():
 *      Executes Surtr command based request protocol.
 *      Only 4 commands are from outside -> surtr.
 *      SW_STATE and ADC_STATE go from surtr -> outside.
 * ===============================================================
 * PARSE SURTR COMMAND
 * Unpacks message and updates data accordingly.
 * MSG TYPE		ENUM	TIME (us)		RAW DATA
 * ===============================================================
 * SYN_ACK			0					| ACK |
 * SW CTRL		    1					| ID | STATE |
 * STEP CTRL		2					| ID | MOTOR DELTA |
 * SW STATE		    3					| SW[8] | MOTOR1 | MOTOR2 |
 * ADC STATE		4					| VALUE[24] |
 * IGNITION		    5					| PASSWORD |
 * 
 */
void execute_command(const uint8_t *message, const int size);

/**
 * surtr_syn_ack():
 *      Send ACK response back to client by placing onto write message queue.
 *      k_msgq_put(): 
 *      0        Success
 *      -ENOMSG  returned without waiting or queue purged.
 *      -EAGAIN  waiting period timed out
 */
int surtr_syn_ack();

/**
 * surtr_sw_ctrl():
 *      Dissects message and applies control command on desired switch.
 */
void surtr_sw_ctrl(const uint8_t *message);

/**
 * surtr_step_ctrl():
 *      Dissects message and applies control command on desired motor.
 *      Delta is not really delta here but in reality the TARGET VALUE...
 */
void surtr_step_ctrl(const uint8_t *message);

#endif