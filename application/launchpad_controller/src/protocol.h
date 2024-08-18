#pragma once

#include <pb.h>
#include <src/surtr.pb.h>

#define PROTOCOL_HEADER_SIZE 2
#define PROTOCOL_FOOTER_SIZE 2
#define PROTOCOL_BUFFER_LENGTH (PROTOCOL_HEADER_SIZE + PROTOCOL_FOOTER_SIZE + surtrpb_SurtrMessage_size)

enum com_channels {
    COM_CHAN_USB,
    COM_CHAN_EXT_UART,
    COM_CHAN_LORA,
    COM_CHAN_FLASH,
    COM_CHAN_MAX,
};

enum protocol_states {
    PROT_STATE_ALIGNMENT,
    PROT_STATE_LENGTH,
    PROT_STATE_DATA,
    PROT_STATE_CHECKSUM0,
    PROT_STATE_CHECKSUM1
};

struct protocol_state {
    enum protocol_states state;
    uint8_t data[surtrpb_SurtrMessage_size];
    int data_index;
    uint16_t crc;
    uint8_t length;
};

int encode_surtr_message(surtrpb_SurtrMessage *data, uint8_t *buf);
void reset_protocol_state(struct protocol_state *ps);
int parse_protocol_message(struct protocol_state *ps, uint8_t byte, surtrpb_SurtrMessage *message);

int get_encoded_message_length(uint8_t *buf);

void handle_message(surtrpb_SurtrMessage *msg);
