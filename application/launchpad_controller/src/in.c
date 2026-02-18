#include "in.h"

LOG_MODULE_REGISTER(in, CONFIG_APP_LOG_LEVEL);

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
void execute_command(const uint8_t *message, const int size)
{
    const uint8_t cmd = message[SURTR_CMD_INDEX];
    switch (cmd)
    {
        case SURTR_CMD_SYN_ACK:
                surtr_syn_ack();
            break;

        case SURTR_CMD_SW_CTRL:
                surtr_sw_ctrl(message);
            break;

        case SURTR_CMD_STEP_CTRL:
                surtr_step_ctrl(message);
            break;

        case SURTR_CMD_IGNITION:
                LOG_INF("Ignition does nothing for now.");
            break;
        
        default:
            break;
    }
}


/**
 * surtr_syn_ack():
 *      Send ACK response back to client by placing onto write message queue.
 *      k_msgq_put(): 
 *      0        Success
 *      -ENOMSG  returned without waiting or queue purged.
 *      -EAGAIN  waiting period timed out
 */
int surtr_syn_ack() 
{
    const uint8_t payload[2] = { SURTR_CMD_SYN_ACK, SURTR_MSG_ACK };
    Msg msg = msg_construct(SURTR_MSG_ACK_SIZE, payload);

    // Might want to have timeout here.
	if(k_msgq_put(&write_msgq, &msg, K_NO_WAIT) != 0) 
    {
        LOG_WRN("Message could not be placed on queue.");
        return 0;
    }
    return 1;
}

/**
 * surtr_sw_ctrl():
 *      Dissects message and applies control command on desired switch.
 */
void surtr_sw_ctrl(const uint8_t *message)
{
    toggle_switch(message[SURTR_MSG_SW_CTRL_ID], message[SURTR_MSG_SW_CTRL_STATE]);
}

/**
 * surtr_step_ctrl():
 *      Dissects message and applies control command on desired motor.
 *      Delta is not really delta here but in reality the TARGET VALUE...
 */
void surtr_step_ctrl(const uint8_t *message)
{
    uint32_t delta;
    int id = message[SURTR_MSG_STEP_CTRL_ID];
    memcpy(&delta, &message[SURTR_MSG_STEP_CTRL_DELTA], sizeof(delta));
    update_stepper_motor(id, delta);
}