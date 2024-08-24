#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include <zephyr/sys/crc.h>

#include <pb_encode.h>
#include <pb_decode.h>
#include <src/surtr.pb.h>

#include "protocol.h"
#include "ignition.h"
#include "actuation.h"
#include "steppers.h"

#define PROTOCOL_CRC_POLY 0x1011
#define PROTOCOL_CRC_SEED 0x35

#define PROTOCOL_ALIGNMENT_BYTE '\x34'

LOG_MODULE_REGISTER(protocol, CONFIG_APP_LOG_LEVEL);

int encode_surtr_message(surtrpb_SurtrMessage *msg, uint8_t *buf) {
    pb_ostream_t stream = pb_ostream_from_buffer(buf + PROTOCOL_HEADER_SIZE, PROTOCOL_BUFFER_LENGTH);
    if (pb_encode(&stream, surtrpb_SurtrMessage_fields, msg) != true) {
        LOG_ERR("Could not encode message");
        return -1;
    };
    buf[0] = PROTOCOL_ALIGNMENT_BYTE;
    buf[1] = stream.bytes_written;
    uint16_t crc = crc16(PROTOCOL_CRC_POLY, PROTOCOL_CRC_SEED, buf, stream.bytes_written + PROTOCOL_HEADER_SIZE);
    LOG_DBG("crc %d", crc);
    LOG_DBG("payload length %d", stream.bytes_written);
    buf[stream.bytes_written + PROTOCOL_HEADER_SIZE] = crc;
    buf[stream.bytes_written + PROTOCOL_HEADER_SIZE + 1] = crc >> 8;
    return stream.bytes_written + PROTOCOL_HEADER_SIZE + PROTOCOL_FOOTER_SIZE;
}

void reset_protocol_state(struct protocol_state *ps) {
    ps->state = PROT_STATE_ALIGNMENT;
    ps->data_index = 0;
}

// returns:
// 1 received message
// 0 no message
// -1 an error reset the state machine
int parse_protocol_message(struct protocol_state *ps, uint8_t byte, surtrpb_SurtrMessage *message) {
    switch(ps->state) {
        case PROT_STATE_ALIGNMENT:
            LOG_DBG("Alignment byte: %d", byte);
            if (byte == PROTOCOL_ALIGNMENT_BYTE) {
                ps->state = PROT_STATE_LENGTH;
            } else {
                LOG_WRN("Invalid alignment byte %d", byte);
                return -1;
            }
            break;
        case PROT_STATE_LENGTH:
            LOG_DBG("State byte: %d", byte);
            ps->state = PROT_STATE_DATA;
            if (!(byte < PROTOCOL_BUFFER_LENGTH)) {
                LOG_ERR("message is too long");
                ps->state = PROT_STATE_ALIGNMENT;
                return -1;
            }
            ps->length = byte;
            break;
        case PROT_STATE_DATA:
            LOG_DBG("Data byte: %d", byte);
            if (ps->data_index < sizeof(ps->data)) {
                ps->data[ps->data_index] = byte;
            }
            ps->data_index++;
            if (ps->data_index == ps->length) {
                ps->state = PROT_STATE_CHECKSUM0;
                ps->data_index = 0;
            }
            break;
        case PROT_STATE_CHECKSUM0:
            LOG_DBG("Checksum low byte: %d", byte);
            ps->crc = byte;
            ps->state = PROT_STATE_CHECKSUM1;
            break;
        case PROT_STATE_CHECKSUM1:
            LOG_DBG("Checksum high byte: %d", byte);
            ps->crc |= byte << 8;
            ps->state = PROT_STATE_ALIGNMENT;
            uint16_t tmp_crc = PROTOCOL_CRC_SEED;
            const uint8_t alignment = PROTOCOL_ALIGNMENT_BYTE;
            tmp_crc = crc16(PROTOCOL_CRC_POLY, tmp_crc, &alignment, 1);
            tmp_crc = crc16(PROTOCOL_CRC_POLY, tmp_crc, &ps->length, 1);
            tmp_crc = crc16(PROTOCOL_CRC_POLY, tmp_crc, ps->data, ps->length);
            pb_istream_t istream = pb_istream_from_buffer(ps->data, ps->length);
            if (tmp_crc == ps->crc) {
                int ret;
                ret = pb_decode(&istream, surtrpb_SurtrMessage_fields, message);
                if (ret != true) {
                    LOG_ERR("Could not deocde surtr message");
                    return -1;
                }
                return 1;
            }
            LOG_WRN("Invalid checksum");
            return -1;
            break;
    }
    return 0;
}

int get_encoded_message_length(uint8_t *buf) {
    return buf[1] + PROTOCOL_FOOTER_SIZE + PROTOCOL_FOOTER_SIZE;
}

void handle_message(surtrpb_SurtrMessage *msg) {
    switch (msg->which_command) {
        case surtrpb_SurtrMessage_sw_ctrl_tag:
            LOG_INF("Handling switch control msg");
            toggle_switch(msg->command.sw_ctrl.id, msg->command.sw_ctrl.state);
            break;

        case surtrpb_SurtrMessage_ignition_tag:
            LOG_INF("Handling ignition msg");
            if (msg->command.ignition.password == 42) {
                start_ignition_sequence();
            } else {
                LOG_WRN("Got incorrect password");
            }
            break;

        case surtrpb_SurtrMessage_step_ctrl_tag:
            LOG_INF("Handling step control msg");
            switch (msg->command.step_ctrl.id) {
                case 1:
                    target_motor1 += msg->command.step_ctrl.motorDelta;
                    break;
                case 2:
                    target_motor2 += msg->command.step_ctrl.motorDelta;
                    break;
                default:
                    LOG_WRN("got invalid stepper id");
            }
            break;

        default:
            LOG_WRN("got unknown message");
    }
}