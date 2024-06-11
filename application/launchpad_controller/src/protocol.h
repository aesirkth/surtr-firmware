#pragma once

#include <stdint.h>

#define MSG_ADC1_ID 0
#define MSG_ADC2_ID 1

struct surtr_message {
    uint8_t msg_id;
    uint8_t msg_length;
    union {
        struct {
            float channel_1;
            float channel_2;
            float channel_3;
            float channel_4;
        } adc1;

        struct {
            float channel_1;
            float channel_2;
            float channel_3;
            float channel_4;
        } adc2;
    } msg;
} __attribute__((aligned(4)));