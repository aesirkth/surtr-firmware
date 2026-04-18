#ifndef UART_H
#define UART_H

#include <stdint.h>
#include <zephyr/drivers/uart.h>
#include "packet.h"
#include "circbuf.h"

/* Write Message Queue declared in main. */
extern struct k_msgq write_msgq;
extern const struct device *const uart_dev;

/**
 * uart_isr()
 *   Interrupt Service Routine for UART
 *   Reads RX data byte for byte and places in circular buffer.
 *   Call to uart_irq_update() has to be made before uart_irq_rx_ready().
 *   Releases SEM for IN_THREAD to begin processing message.
 */
void uart_isr(const struct device *dev, void *circ_buf);

/**
 * initialize_uart_sem():
 *      Wrapper function to initialize UART IRQ SEM.
 */
int uart_initialize_sem();

/**
 * handle_request_uart():
 *      Blocking wait for counting semaphore. 
 *      When UART IRQ fires, new message is placed in cir buffer and SEM (+1) released.
 *      Packet can then be retrieved.
 */
int uart_handle_request(Circbuf *rx_circbuf, uint8_t *p_data_buf, int *p_data_size);

/**
 * retrieve_packet_uart():
 *      Sequentially goes through packet and checks that:
 *      1. First byte is alignment.
 *      2. Collects length from 2nd byte.
 *      3. Retrieves data of size length.
 *      4. Confirm that checksum equals.
 *      UART uses Circular Buffer so bytes have to be taken out 1 by 1
 *      stored into a tmp_rx buffer in order to compare against CRC 
 *      CRC must use {Align, Length, Data} as comparison buffer.
 */
int uart_retrieve_packet(Circbuf *rx_circbuf, uint8_t *out_buf, int *p_data_size);

#endif