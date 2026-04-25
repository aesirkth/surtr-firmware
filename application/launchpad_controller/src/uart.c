#include "uart.h"

LOG_MODULE_REGISTER(uart, LOG_LEVEL_DBG);

/**
 * ==========================================================
 * handle_request_uart():
 *      Retrieves UART packet and places it on REQUEST queue.
 */
int uart_handle_request(Circbuf *rx_circbuf, struct uart_protocol *ps, uint8_t *payload)
{
    while(1)
    {
        uart_wait_IRQ();
        LOG_DBG("UART wait IRQ finished:\n");

        if(uart_retrieve_packet(rx_circbuf, ps))
            break;
    }

    for(int i = 0; i < ps->length; i++)
        payload[i] = ps->buffer[i+2];

    LOG_DBG("UART Retrieve packet success\n");
    return 1;
}

/**
 * ==========================================================
 * uart_wait_IRQ():
 *      Blocking wait for counting semaphore. 
 *      When UART IRQ fires, new message is placed in cir buffer and SEM (+1) released.
 */
void uart_wait_IRQ()
{
    k_sem_take(&sem_uart_irq, K_FOREVER);
}


/**
 * ==========================================================
 * retrieve_packet_uart():
 *      1. First byte is alignment.
 *      2. Collects length from 2nd byte.
 *      3. Retrieves data of size length.
 *      4. Confirm that checksum equals.
 *      UART uses Circular Buffer so bytes have to be taken out 1 by 1
 *      stored into a tmp_rx buffer in order to compare against CRC 
 *      CRC must use {Align, Length, Data} as comparison buffer.
 */
int uart_retrieve_packet(Circbuf *rx_circbuf, struct uart_protocol *ps)
{
    while(1)
    {
        switch (ps->state)
        {
            case ALIGNMENT:
                    /* ---- 1. Alignment byte 0x34 ----------- */
                    if (!circbuf_pop(rx_circbuf, &ps->alignment))
                    {
                        LOG_DBG("Alignment: Circular Buffer empty.");
                        return 0;
                    }

                    if (ps->alignment == PROTOCOL_ALIGNMENT_BYTE)
                    {
                        ps->buffer[0] = ps->alignment;
                        ps->state = LENGTH;
                        LOG_DBG("Alignment: Success.");
                    }
                break;
            
            case LENGTH:
                    /* ---- 2. Length byte ------------------- */
                    if (!circbuf_pop(rx_circbuf, &ps->length))
                    {
                        LOG_DBG("Length: Circular Buffer empty.");
                        return 0;
                    }

                    if (ps->length <= 0 || ps->length >= MSG_SIZE-4)
                        ps->state = ALIGNMENT;

                    ps->buffer[1] = ps->length;
                    ps->data_end = ps->length+2;
                    ps->data_index = 0;
                    ps->state = PAYLOAD;
                    LOG_DBG("Length: Success.");
                break;
            
            case PAYLOAD:
                    /* ---- 3. data bytes into buffer -------- */
                    if (!circbuf_pop(rx_circbuf, &ps->buffer[ps->data_index+2]))
                    {
                        LOG_DBG("Payload: Circular Buffer empty.");
                        return 0;
                    }
                    ps->data_index++;
                    if (ps->data_index >= ps->length)
                    {
                        LOG_DBG("Payload: Success.");
                        ps->state = CHECKSUM0;
                    }
                break;

            case CHECKSUM0:
                    /* ---- 4. CRC low byte ------------------- */
                    if (!circbuf_pop(rx_circbuf, &ps->crc_low))
                    {
                        LOG_DBG("CHECKSUM0: Circular Buffer empty.");
                        return 0;
                    }
                    ps->state = CHECKSUM1;
                break;
            
            case CHECKSUM1:
                    /* ---- 5. CRC cmp {Align, len, data} ---- */
                    if (!circbuf_pop(rx_circbuf, &ps->crc_high))
                    {
                        LOG_DBG("CHECKSUM1: Circular Buffer empty.");
                        return 0;
                    }

                    ps->crc = (uint16_t)(ps->crc_low) | ((uint16_t)(ps->crc_high) << 8);
                    uint16_t crc_dev = crc16(PROTOCOL_CRC_POLY, PROTOCOL_CRC_SEED, ps->buffer, ps->data_end);
                    LOG_DBG("CRC INCOMING: %d, CRC DEV: %d\n", ps->crc, crc_dev);
                        
                    ps->state = ALIGNMENT;

                    if(ps->crc == crc_dev)
                    {
                        LOG_DBG("CHECKSUM1: Success.");
                        return 1;
                    }
                    LOG_WRN("Invalid Checksum.");
                break;
        }
    }
    
}

/**
 * ==========================================================
 * uart_isr():
 *   Interrupt Service Routine for UART
 *   Reads RX data byte for byte and places in circular buffer.
 *   Call to uart_irq_update() has to be made before uart_irq_rx_ready().
 *   Releases SEM for UART to begin processing message.
 */
void uart_isr(const struct device *dev, void *circ_buf)
{
    LOG_DBG("UART_ISR\n");
    uint8_t byte;
    if(!uart_irq_update(dev))
        return;

    while (uart_irq_rx_ready(dev))
    {
        LOG_DBG("UART_RX_READY\n");
        uart_fifo_read(dev, &byte, 1);
        circbuf_push(circ_buf, byte);
    }
    
	k_sem_give(&sem_uart_irq);
    LOG_DBG("UART_ISR_FINISH\n");
}


/**
 * ==========================================================
 * uart_send_message():
 *      POLL UART message out TX_BUFFER.
 *      No IRQ needed here because client (PC) expects response.
 */
int uart_send_message(uint8_t *tx_buffer, const uint8_t tx_size)
{
    for (int i = 0; i < tx_size; i++)
		uart_poll_out(uart_dev, tx_buffer[i]);
}