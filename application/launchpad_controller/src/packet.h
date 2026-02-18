#pragma once
#ifndef PACKET_H
#define PACKET_H

#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include <zephyr/sys/crc.h>
#include <stdint.h>
#include <stdbool.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

#define PROTOCOL_CRC_POLY 0x1011
#define PROTOCOL_CRC_SEED 0x35
#define PROTOCOL_ALIGNMENT_BYTE 0x34
#define MSG_SIZE	128

/* ============================================================ */
/* =				SURTR MESSAGE PROTOCOL					  = */
/* ============================================================ */
/* MSG TYPE		ENUM	TIME (ms)	RAW DATA				  	*/
/* ============================================================ */
/* SYN_ACK			0					| ACK |					*/
/* SW CTRL		    1					| ID | STATE |			*/
/* STEP CTRL		2					| ID | MOTOR DELTA |	*/
/* SW STATE		    3		X			| SW[8] | MOTOR1 | MOTOR2 |*/
/* ADC STATE		4		X			| VALUE[24] |			*/
/* IGNITION		    5					| PASSWORD |			*/

/* ============================================================ */
/* =					SYN_ACK	PACKET 					  	  = */
/* ============================================================ */
/* 	BYTESIZE:		1		1		1	1	2					*/
/* 	LAYOUT			[ALIGN][LEN][cmd][ACK][CRC]					*/
/*	TOTALSIZE:	6												*/
/* ============================================================ */

/* ============================================================ */
/* =					SW_CTRL	PACKET 					  	  = */
/* ============================================================ */
/* 	BYTESIZE:		1		1	  1		1	1	2				*/
/* 	LAYOUT			[ALIGN][LEN][cmd][id][state][CRC]			*/
/*	TOTALSIZE:	7												*/
/* ============================================================ */

/* ============================================================ */
/* =				STEP_CTRL	PACKET 					  	  = */
/* ============================================================ */
/* 	BYTESIZE:		1		1	 1		1		4	2			*/
/* 	LAYOUT			[ALIGN][LEN][cmd][id][mdelta][CRC]			*/
/*	TOTALSIZE:	10												*/
/* ============================================================ */

/* ============================================================ */
/* =				SW_STATE	PACKET 					  	  = */
/* ============================================================ */
/* 	BYTESIZE:		1		1	 1		8	8	  4	  4		2	*/
/* 	LAYOUT			[ALIGN][LEN][cmd][time][sw{8}][M1][M2][CRC]	*/
/*	TOTALSIZE:	29												*/
/* ============================================================ */

/* ============================================================ */
/* =				ADC_STATE	PACKET 					  	  = */
/* ============================================================ */
/* 	BYTESIZE:		1		1	 1		8		96	  2			*/
/* 	LAYOUT			[ALIGN][LEN][cmd][time][adc{24}][CRC]		*/
/*	TOTALSIZE:	109												*/
/* ============================================================ */

/* ============================================================ */
/* =				IGNITION	PACKET 					  	  = */
/* ============================================================ */
/* 	BYTESIZE:		1		1	 1		4	2					*/
/* 	LAYOUT			[ALIGN][LEN][cmd][pswd][CRC]				*/
/*	TOTALSIZE:	9												*/
/* ============================================================ */

typedef struct {
	uint8_t length;
	uint8_t data[MSG_SIZE-1];
} Msg;

/**
 * encode_packet():
 *      Adds protocol Alignment, length, and CRC checksum to packet.
 *      Writes finished packet into tx_buf and size of tx_buf into p_tx_size.
 *      | Align | len | DATA | Checksum (h) | Checksum (l) |
 */
void encode_packet(const uint8_t *data, uint8_t *tx_buf, const uint8_t data_size, uint8_t *p_tx_size);

/**
 * retrieve_packet():
 *      Sequentially goes through packet and checks that:
 *      1. First byte is alignment.
 *      2. Collects length from 2nd byte.
 *      3. Retrieves data of size length.
 *      4. Confirm that checksum equals.
 */
int retrieve_packet(const uint8_t *rx_buf, uint8_t *out_buf);

/**
 * msg_construct():
 *      Creates a new Msg and stores length and data.
 */
Msg msg_construct(const uint8_t length, const uint8_t *data);

/**
 * msg_construct():
 *      Creates a new Msg and stores length and data.
 *      Time (ms) is added to msg.data before actual data.
 *      sizeof(int64_t) is 8 bytes.
 */
Msg msg_construct_with_time(const uint8_t length, const uint8_t *data);

#endif