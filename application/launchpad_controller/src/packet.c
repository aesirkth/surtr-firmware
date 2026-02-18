#include "packet.h"

LOG_MODULE_REGISTER(packet, CONFIG_APP_LOG_LEVEL);
/**
 * encode_packet():
 *      Adds protocol Alignment, length, and CRC checksum to packet.
 *      Writes finished packet into tx_buf and size of tx_buf into p_tx_size.
 *      | Align | len | DATA | Checksum (h) | Checksum (l) |
 */
void encode_packet(const uint8_t *data, uint8_t *tx_buf, const uint8_t data_size, uint8_t *p_tx_size)
{
    uint8_t crc_low, crc_high;
    uint16_t crc;

    tx_buf[0] = PROTOCOL_ALIGNMENT_BYTE;
    tx_buf[1] = data_size;
    
    for(int i = 0; i < data_size; i++)
        tx_buf[i+2] = data[i];

    crc = crc16(PROTOCOL_CRC_POLY, PROTOCOL_CRC_SEED, tx_buf, (data_size+2));
    crc_low = crc & 0x00FF;
    crc_high = (crc >> 8) & 0x00FF;

    tx_buf[data_size+2] = crc_low;
    tx_buf[data_size+3] = crc_high;

    *p_tx_size = data_size + 4;
    
}

/**
 * retrieve_packet():
 *      Sequentially goes through packet and checks that:
 *      1. First byte is alignment.
 *      2. Collects length from 2nd byte.
 *      3. Retrieves data of size length.
 *      4. Confirm that checksum equals.
 */
int retrieve_packet(const uint8_t *rx_buf, uint8_t *out_buf) 
{
    uint8_t length, data_end;
    uint16_t crc, crc_low, crc_high;

    if (rx_buf[0] != PROTOCOL_ALIGNMENT_BYTE)
    {
        LOG_WRN("Aligment byte invalid.");
        return 0;
    }

    length = rx_buf[1];
    for(int i = 0; i < length; i++)
    {
        out_buf[i] = rx_buf[i+2];
    }

    data_end = length + 2;
    crc_low  = (uint16_t) rx_buf[data_end];
    crc_high = (uint16_t) rx_buf[data_end+1];
    crc = crc_low | (crc_high << 8);

    if (crc != crc16(PROTOCOL_CRC_POLY, PROTOCOL_CRC_SEED, rx_buf, data_end))
    {
        LOG_WRN("Invalid Checksum.");
        return 0;
    }

    return 1;
}

/**
 * msg_construct():
 *      Creates a new Msg and stores length and data.
 */
Msg msg_construct(const uint8_t length, const uint8_t *data)
{
	Msg msg;
	msg.length = length;
	memset(msg.data, 0, sizeof(msg.data));
	for(int i = 0; i < length; i++)
		msg.data[i] = data[i];

	return msg;
}

/**
 * msg_construct():
 *      Creates a new Msg and stores length and data.
 *      Time (ms) is added to msg.data before actual data.
 *      sizeof(int64_t) is 8 bytes.
 */
Msg msg_construct_with_time(const uint8_t length, const uint8_t *data)
{
	Msg msg;
	memset(msg.data, 0, sizeof(msg.data));

	int64_t ms_since_boot = k_uptime_get();
	memcpy(msg.data, &ms_since_boot, sizeof(ms_since_boot));
	
	msg.length = length + 8;

	for(int i = 0; i < msg.length; i++)
		msg.data[i+8] = data[i];

	return msg;
}