#include "in.h"

LOG_MODULE_REGISTER(in, CONFIG_APP_LOG_LEVEL);

/**
 * ===============================================================
 * surtr_syn_ack():
 *      Add ACK response 0xFF (SUCCESS) to response message.
 */
void surtr_syn_ack(uint8_t *response, uint8_t *response_size) 
{
    LOG_DBG("surtr syn ack: size before: %d\n", (*response_size));
    response[(*response_size)] = SURTR_MSG_ACK_SUCCESS;
    (*response_size)++;
}

/**
 * ===============================================================
 * surtr_syn_fail():
 *      Add ACK response 0x00 (FAIL) to response message.
 */
void surtr_syn_fail(uint8_t *response, uint8_t *response_size) 
{
    response[(*response_size)] = SURTR_MSG_ACK_FAIL;
    (*response_size)++;
}

/**
 * ===============================================================
 * surtr_sw_ctrl():
 *      Dissects message and applies control command on desired switch.
 *      Paired together with ACK on response for confirmation.
 *      MSG TYPE		ENUM	TIME (us)		RAW DATA
 *      ===============================================================
 *      SW CTRL 1 | ID | STATE |
 */
int surtr_sw_ctrl(const uint8_t id, const uint8_t state)
{
    if (id >= NUM_SWITCHES)
        return 0;

    toggle_switch(id, state);
    return 1;
}

/**
 * ===============================================================
 * surtr_step_ctrl():
 *      Dissects message and applies control command on desired motor.
 *      Delta is not really delta here but in reality the TARGET VALUE...
 *      ===============================================================
 *      STEP CTRL		2					| ID | MOTOR DELTA |
 */
void surtr_step_ctrl(const uint8_t *payload)
{
    uint32_t delta;
    int id = payload[SURTR_MSG_STEP_CTRL_INDEX_ID];
    memcpy(&delta, &payload[SURTR_MSG_STEP_CTRL_INDEX_DELTA], sizeof(delta));
    update_stepper_motor(id, delta);
}

/**
 * ===============================================================
 * surtr_get_adc_state():
 *      Reads state of ADCs and combines into surtr response message.
 *      data begins after 10 bytes and then is 96 bytes long.
 *      MSG TYPE		ENUM	TIME (us)		RAW DATA
 *      ===============================================================
 *      ADC STATE		4					| VALUE[24] |
 */
int surtr_get_adc_state(uint8_t *response, uint8_t *response_size)
{
    uint32_t adc_val[NUM_ADC_CHANNELS];
    uint8_t *p_response_data;
    uint8_t adc_byte_size; 
    
    if(!read_adc(adc_val))
    {
        LOG_ERR("Read_adc() failed.");
        return 0;
    }

    // Little endian LSB first
    for (int i = 0; i < NUM_ADC_CHANNELS; i++) {
        uint32_t v = adc_val[i];
        response[*response_size + 0] = v & 0xFF;
        response[*response_size + 1] = (v >> 8) & 0xFF;
        response[*response_size + 2] = (v >> 16) & 0xFF;
        response[*response_size + 3] = (v >> 24) & 0xFF;
        (*response_size) += 4;
    }

    return 1;
}

/**
 * ===============================================================
 * surtr_get_sw_state():
 *      Reads state of SWs and combines into surtr response message.
 *      data begins after 10 bytes and then is 8 bytes long.
 *      MSG TYPE		ENUM	TIME (us)		RAW DATA
 *      ===============================================================
 *      SW STATE		    3					| SW[8] 
 */
int surtr_get_sw_state(uint8_t *response, uint8_t *response_size)
{
    for(int i = 0; i < NUM_SWITCHES; i++)
    {
        response[(*response_size)] = sw[i];
        (*response_size)++;
    }
    return 1;
}

void sampling_isr(struct k_timer *timer_id)
{
	k_sem_give(&sem_sampling_irq);
}
