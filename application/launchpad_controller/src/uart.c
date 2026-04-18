#include "uart.h"

LOG_MODULE_REGISTER(uart, LOG_LEVEL_DBG);

static struct k_sem sem_uart_irq;

/**
 * initialize_uart_sem():
 *      Wrapper function to initialize UART IRQ SEM.
 */
int uart_initialize_sem()
{
    k_sem_init(&sem_uart_irq, 0, 5);
}

/**
 * handle_request_uart():
 *      Blocking wait for counting semaphore. 
 *      When UART IRQ fires, new message is placed in cir buffer and SEM (+1) released.
 *      Packet can then be retrieved.
 */
int uart_handle_request(Circbuf *rx_circbuf, uint8_t *p_data_buf, int *p_data_size)
{
    LOG_DBG("Handle request waiting\n.");
	k_sem_take(&sem_uart_irq, K_FOREVER);
    LOG_DBG("Handle request SEM recieved\n.");

    if(!uart_retrieve_packet(rx_circbuf, p_data_buf, p_data_size))
    {
        return 0;
    }
    return 1;
}

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
int uart_retrieve_packet(Circbuf *rx_circbuf, uint8_t *out_buf, int *p_data_size) 
{
    uint8_t alignment,
            length, 
            data_byte,
            data_end,
            crc_low, 
            crc_high;
    uint16_t crc;
    uint8_t tmp_rx[MSG_SIZE];

    /* ---- 1. Alignment byte 0x34 ----------- */
    circbuf_pop(rx_circbuf, &alignment);
    if (alignment != PROTOCOL_ALIGNMENT_BYTE)
    {
        LOG_WRN("Aligment byte invalid.");
        return 0;
    }
    tmp_rx[0] = alignment;

    /* ---- 2. Length byte ------------------- */
    circbuf_pop(rx_circbuf, &length);
    *p_data_size = length;
    tmp_rx[1] = length;

    /* ---- 3. data bytes into tmp_rx -------- */
    for(int i = 0; i < length; i++)
    {
        circbuf_pop(rx_circbuf, &data_byte);
        tmp_rx[i+2] = data_byte;
    }
    data_end = length+2;

    /* ---- 4. CRC cmp {Align, len, data} ---- */
    circbuf_pop(rx_circbuf, &crc_low);
    circbuf_pop(rx_circbuf, &crc_high);
    crc = (uint16_t)(crc_low) | ((uint16_t)(crc_high) << 8);
    if (crc != crc16(PROTOCOL_CRC_POLY, PROTOCOL_CRC_SEED, tmp_rx, data_end))
    {
        LOG_WRN("Invalid Checksum.");
        return 0;
    }
    
    /* ---- 5. Transfer only data payload ---- */
    for(int i = 0; i < length; i++)
        out_buf[i] = tmp_rx[i+2];

    return 1;
}

/**
 * uart_isr()
 *   Interrupt Service Routine for UART
 *   Reads RX data byte for byte and places in circular buffer.
 *   Call to uart_irq_update() has to be made before uart_irq_rx_ready().
 *   Releases SEM for IN_THREAD to begin processing message.
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
 * send_message():
 * 
 *      MSGQ -> ENCODE -> UART TX
 */
int uart_send_message(uint8_t *tx_buf)
{
    LOG_DBG("UART_SEND_MESSAGE\n");
    Msg msg;
    uint8_t tx_size = 0;

    if(k_msgq_get(&write_msgq, &msg, K_FOREVER) != 0)
    {
        LOG_WRN("Message Queue failed to get item.");
        return 0;
    }

    encode_packet(msg.data, tx_buf, msg.length, &tx_size);
    LOG_DBG("UART PACKET ENCODED\n");

    for (int i = 0; i < tx_size; i++)
		uart_poll_out(uart_dev, tx_buf[i]);

    LOG_DBG("UART PACKET SENT\n");
    return 1;
}