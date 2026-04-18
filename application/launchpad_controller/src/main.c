#include <zephyr/kernel.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/logging/log.h>
#include <zephyr/drivers/uart.h>
#include <zephyr/device.h>
#include <drv8711.h>
#include <ad4111.h>
#include "circbuf.h"
#include "collect.h"
#include "server.h"
#include "packet.h"
#include "dhcp.h"
#include "in.h"
#include "uart.h"

/* ========================================================== */
/* =			GLOBAL CONSTANT DEFINITIONS					= */
/* ========================================================== */
#define IN_THREAD_STACK_SIZE 	2048
#define IN_THREAD_PRIORITY		1	// Highest priority.

#define OUT_THREAD_STACK_SIZE 	2048
#define OUT_THREAD_PRIORITY		2

#define ADC_THREAD_STACK_SIZE 	1024
#define ADC_THREAD_PRIORITY		3
#define ADC_THREAD_PERIOD		5000
#define THREAD_EMPTYARG 		void*

#define NUM_EXT_ADC				2
#define NUM_ADC_CHANNELS		24
#define NUM_CHANNELS_PER_ADC	12
#define NUM_STEPPERS			1	// board can hold 3.
#define NUM_LEDS 				2
#define NUM_SWITCHES 			8
#define MOTOR_CURRENT_I_LIMIT	2000
#define MOTOR1_INDEX			0

#define ADC_ARRAY_BYTE_SIZE		96

#define MSG_SIZE				128
#define MSGQ_BACKLOG			4
#define MSGQ_ALIGN				1	// default by zephyr.
#define STANDARD_BAUDRATE		115200

#define STATE_NO_CONNECTION 	0
#define STATE_CONNECTION		1


/* https://www.cs.yale.edu/homes/aspnes/pinewiki/C(2f)Macros.html */
#define FATALERROR(...) \
	do { \
		LOG_ERR(__VA_ARGS__); \
		kernel_exit(); \
	} while (0)

LOG_MODULE_REGISTER(main, CONFIG_APP_LOG_LEVEL);

/* ========================================================== */
/* =				DEVICE DEFINITIONS						= */
/* ========================================================== */
/* AD4111 devices drivers initialized by zephyr on boot.      */
/* DRV8711 devices drivers initialized by zephyr on boot.     */
/* UART has to be *const pointer.  UART4 on board.            */
const struct device *adcs[] = {
	DEVICE_DT_GET(DT_ALIAS(xadc1)),
	DEVICE_DT_GET(DT_ALIAS(xadc2)),
};

const struct device *const uart_dev = 
    DEVICE_DT_GET(DT_ALIAS(external_uart));
    
const struct device *steppers[] = {
	DEVICE_DT_GET(DT_ALIAS(motor1)),
};
    
const struct gpio_dt_spec motor_dir_dt[] = {
	GPIO_DT_SPEC_GET(DT_ALIAS(step1_dir), gpios),
};

const struct gpio_dt_spec motor_step_dt[] = {
	GPIO_DT_SPEC_GET(DT_ALIAS(step1_ctrl), gpios),
};

const struct gpio_dt_spec leds[] = {
    GPIO_DT_SPEC_GET(DT_ALIAS(led0), gpios),
    GPIO_DT_SPEC_GET(DT_ALIAS(led1), gpios),
};

const struct gpio_dt_spec switches[] = {
    GPIO_DT_SPEC_GET(DT_ALIAS(switch1), gpios),
    GPIO_DT_SPEC_GET(DT_ALIAS(switch2), gpios),
    GPIO_DT_SPEC_GET(DT_ALIAS(switch3), gpios),
    GPIO_DT_SPEC_GET(DT_ALIAS(switch4), gpios),
    GPIO_DT_SPEC_GET(DT_ALIAS(switch5), gpios),
    GPIO_DT_SPEC_GET(DT_ALIAS(switch6), gpios),
    GPIO_DT_SPEC_GET(DT_ALIAS(switch7), gpios),
    GPIO_DT_SPEC_GET(DT_ALIAS(switch8), gpios), // This connects to port 3 on the board, for some reason
	/* comment above is not confirmed yet! 17/02-2026 */
};



/* ========================================================== */
/* =				DATA DEFINITIONS						= */
/* ========================================================== */
uint32_t adc[NUM_ADC_CHANNELS];
uint32_t motor_dir_state[NUM_STEPPERS];
uint8_t sw[NUM_SWITCHES];
uint8_t led[NUM_LEDS];

struct uart_config uart_config = {
	.baudrate = STANDARD_BAUDRATE,
	.data_bits = UART_CFG_DATA_BITS_8,
	.flow_ctrl = UART_CFG_FLOW_CTRL_NONE,
	.parity = UART_CFG_PARITY_NONE,
	.stop_bits = UART_CFG_STOP_BITS_1
};

Circbuf rx_circbuf;
uint8_t rx_buffer[MSG_SIZE];
uint8_t payload[MSG_SIZE];

/* ========================================================== */
/* =				THREAD DEFINITIONS						= */
/* ========================================================== */
// CONFIG_SCHED_SIMPLE ready queue will be simple unordered list.
// CONFIG_WAITQ_SIMPLE
struct k_thread in_thread;
struct k_thread out_thread;
struct k_thread adc_thread;
k_tid_t in_id;
k_tid_t out_id;
k_tid_t adc_id;

K_THREAD_STACK_DEFINE(in_stack, IN_THREAD_STACK_SIZE);
K_THREAD_STACK_DEFINE(out_stack, OUT_THREAD_STACK_SIZE);
K_THREAD_STACK_DEFINE(adc_stack, ADC_THREAD_STACK_SIZE);


/* ========================================================== */
/* =				SEMAPHORE DEFINITIONS					= */
/* ========================================================== */
struct k_sem sem_connection;
struct k_sem sem_connection_fail;

/* ========================================================== */
/* =				SERVER DEFINITIONS						= */
/* ========================================================== */
static struct Server server;
static struct Client client;

/* ========================================================== */
/* =				SERVER STATE DEFINITIONS				= */
/* ========================================================== */
static uint8_t state = STATE_NO_CONNECTION;

/* ========================================================== */
/* =				MESSAGE QUEUE DEFINITIONS				= */
/* ========================================================== */
/* Zephyr M_MSGQ_DEFINE API reference:						  */
/* 	-	"Alignment of the message queue's ring buffer is 	  */
/*		not necessary, setting q_align to 1 is sufficient."	  */
/*	-	Defined statically, but can access in other files by: */
/*		extern struct k_msgq <name>;						  */
/* ========================================================== */
/* Defines Message Queue wmsq[4] where each message can be    */
/*  max 128 bytes long. 									  */
K_MSGQ_DEFINE(write_msgq, MSG_SIZE, MSGQ_BACKLOG, MSGQ_ALIGN);

/**
 * ==========================================================
 * server_main():
 * 		FSM with 2 states NO_CONNECTION, CONNECTION
 * 		Starts of in NO_CONNECTION and continously attempts to established connection.
 * 		When established, Give 2 signals into semaphore &sem_connect and move to state CONNECTION.
 * 		This lets the threads enter their work loop.
 * 		On Failure READ/WRITE the THREADS will give signal to semaphore &sem_connect_fail
 * 		While in CONNECTION state, main thread wait for this signal and when received,
 * 		main thread will wake up main thread and close socket, then go back to re-establish connection.
 */
void server_main(struct Server *server, struct Client *client)
{
    LOG_DBG("Entering Server_main().\n");
    while(1)
    {
		switch (state)
		{
			case STATE_NO_CONNECTION:
                LOG_DBG("State: NO_CONNECTION.\n");
				//if (accept_connection(server, client)) 
				if(1)
				{
                    LOG_DBG("New Connection Established.\n");
					state = STATE_CONNECTION;
					k_sem_give(&sem_connection);
					k_sem_give(&sem_connection);
				}
				break;

			case STATE_CONNECTION:
                    LOG_DBG("State: CONNECTION.\n");
					k_sem_take(&sem_connection_fail, K_FOREVER);
                    LOG_DBG("Connection Lost.\n");
					close(client->socket);
					state = STATE_NO_CONNECTION;

				break;
		}
    }
}

/**
 * ==========================================================
 * in_thread_main():
 *      The main function for thread IN which has the purpose of continously
 *      waiting for new input received and executing the commands received.
 * 		Thread is only working while state shows CONNECTION.
 * 		On Failure READ then we send signal to let main close connection.
 * 		This thread then begins waiting for a new CONNECTION signal via &sem_connection.
 */
void in_thread_main(struct Client* client, THREAD_EMPTYARG, THREAD_EMPTYARG)
{
    LOG_DBG("InThread Enter.\n");
	int payload_size;

	k_sem_take(&sem_connection, K_FOREVER);

    while(1)
    {
        LOG_DBG("InThread Waiting for Request.\n");
		//if(!handle_request(client, , payload, &payload_size))
		if(!uart_handle_request(&rx_circbuf, payload, &payload_size))
		{
            LOG_DBG("InThread Request Failed.\n");
			k_sem_give(&sem_connection_fail);
			k_sem_take(&sem_connection, K_FOREVER);
			continue;
		}
		execute_command(payload, payload_size);
        LOG_DBG("InThread Request Handled.\n");
    }
}

/**
 * ==========================================================
 * out_thread_main():
 * 		Only task is to send messages that are in write queue.
 * 		Initially waits for main thread CONNECTION which releases this thread.
 * 		Should message fail, signal to main to restart connection.
 */
void out_thread_main(struct Client *client, THREAD_EMPTYARG, THREAD_EMPTYARG)
{
    LOG_DBG("OutThread Enter.\n");
    uint8_t tx_buf[MSG_SIZE];

	k_sem_take(&sem_connection, K_FOREVER);

    while(1)
    {
        LOG_DBG("OutThread Waiting to Send Message.\n");
		//if(!send_message(client, tx_buf))
		if(!uart_send_message(tx_buf))
		{
            LOG_DBG("OutThread Send Message Failed.\n");
			k_sem_give(&sem_connection_fail);
			k_sem_take(&sem_connection, K_FOREVER);
			continue;
		}
    }
}

/**
 * ==========================================================
 * adc_main_thread():
 * 		PERIOD of 1000 msec
 * 		Blink LEDS, Collect ADC values and place on queue.
 * 		Collect switch states and places on queue.
 * 		Sleep until next period begins.
 * 		Coud possible make use of timers instead.
 */
void adc_thread_main(THREAD_EMPTYARG, THREAD_EMPTYARG, THREAD_EMPTYARG)
{
    LOG_DBG("ADCThread Enter.\n");
	int64_t ms_start_time, 
			ms_end_time,
			cycle_time,
			remainder;

	uint8_t led_state = 0;
	Msg msg;

	while(1)
	{
        //LOG_DBG("ADCThread Blink.\n");
		ms_start_time = k_uptime_get();
		
		blink_leds(led_state);
		led_state = !led_state;

		if(!collect_adc(adc, &msg))
        {
			//LOG_ERR("Collect ADC failed.");
        }

		if(!collect_sw(sw, &msg))
        {
			//LOG_ERR("Collect SW failed.");
        }


		ms_end_time = k_uptime_get();
		cycle_time = ms_end_time - ms_start_time;
		remainder = ADC_THREAD_PERIOD - cycle_time;

		k_msleep(remainder);

	}
}

/**
 * ==========================================================
 * kernel_exit():
 * 		Infinite loop for stalling when dead.
 */
void kernel_exit() 
{
	while(1)
	{
		LOG_INF("Kernel kernel_exit loop.");
		k_sleep(K_FOREVER);
	}
}

/**
 * ==========================================================
 * main():
 * 	Initializes all devices (ADC ad4111, STEPPER drv8711)
 *	Initializes all gpios (switches, leds)
 */
int main()
{
	/* ------------- ADCS INITIALIZE -------------- */
	for(int i = 0; i < NUM_EXT_ADC; i++)
		if (!device_is_ready(adcs[i]))
			FATALERROR("External ADC device ready failed.");
    LOG_DBG("ADC initialized.\n");
	
	/* ------------- LEDS INITIALIZE -------------- */
	// Initializes LED GPIOs as outputs with initial state 0.
	for(int i = 0; i < NUM_LEDS; i++)
	{
		if(!gpio_is_ready_dt(&leds[i]))
			FATALERROR("LED GPIO ready failed.");

		if (gpio_pin_configure_dt(&leds[i], GPIO_OUTPUT_INACTIVE) < 0)
			FATALERROR("Switch GPIO configure failed.");
	}
    LOG_DBG("LEDS initialized.\n");

	/* ---------- SWITCHES INITIALIZE --------------- */
	// Initializes Switch GPIOs as outputs with initial state 0.
    for(int i = 0; i < NUM_SWITCHES; i++)
    {
		if (!gpio_is_ready_dt(&switches[i]))
			FATALERROR("Switch GPIO ready failed.");
		
		if (gpio_pin_configure_dt(&switches[i], GPIO_OUTPUT_INACTIVE) < 0)
			FATALERROR("Switch GPIO configure failed.");
    }
    LOG_DBG("Switches initialized.\n");
    
	/* ------- STEPPER MOTOR INITIALIZE ------------- */
	/* ------- MICROSTEP1 = 0b0000 ------------------ */
    /*
	for(int i = 0; i < NUM_STEPPERS; i++)
		if (!device_is_ready(steppers[i]))
		FATALERROR("Steppers device ready failed.");

    LOG_DBG("STEPPERS device ready.\n");
	for(int i = 0; i < NUM_STEPPERS; i++)
		if(gpio_pin_configure_dt(&motor_dir_dt[i], GPIO_OUTPUT) < 0)
			FATALERROR("Stepper Motor Dir configure failed.");
	
	for(int i = 0; i < NUM_STEPPERS; i++)
    	if(gpio_pin_configure_dt(&motor_step_dt[i], GPIO_OUTPUT) < 0)
			FATALERROR("Stepper Motor Step configure failed.");

    drv8711_set_current_limit(steppers[MOTOR1_INDEX], MOTOR_CURRENT_I_LIMIT);
    drv8711_set_microstep(steppers[MOTOR1_INDEX], MICROSTEP1);
    drv8711_enable(steppers[MOTOR1_INDEX], true);
    LOG_DBG("Motors drv8711 conifgured.\n");
    */

	/* ---------- UART INITIALIZE ------------------ */
	/* -- Only need to enable RX (PC to Surtr) ----- */
	/* -- TX (Surtr to PC) uses polling ------------ */
    if (!device_is_ready(uart_dev))
		FATALERROR("External UART failed.");
	
	if (uart_configure(uart_dev, &uart_config) < 0)
		FATALERROR("External UART configure failed.");

	circbuf_construct(&rx_circbuf, &rx_buffer, MSG_SIZE);
	uart_initialize_sem();

	if (uart_irq_callback_user_data_set(uart_dev, uart_isr, &rx_circbuf) < 0)
		FATALERROR("External UART ISR callback failed.");

	uart_irq_rx_enable(uart_dev);
	// uart_irq_tx_enable(uart_dev);


	/* ---------- DHCP INITIALIZE ------------------ */
	if(initialize_dchp() != 0)
		FATALERROR("Initialized DCHP failed.");
    LOG_DBG("DCHP Initialized.\n");

	/* ---------- SERVER INITIALIZE ---------------- */
	// AF_INET = IPV4 	IPPROTO_TCP
	// SOCK_STREAM = TCP
	if(!server_constructor(&server, AF_INET, 
		SOCK_STREAM, IP, INADDR_ANY, PORT, BACKLOG))
		FATALERROR("Server failed to initialize.");
    LOG_DBG("Server Initialized.\n");
	
	/* ---------- SEMAPHORE INITIALIZE ------------- */
	// initial = 0, count = 2 (2 threads);
    k_sem_init(&sem_connection, 0, 2);
	k_sem_init(&sem_connection_fail, 0, 1);
	
	/* ---------- RESET STATIC ARRAYS -------------- */
	/* Initialize adc[], sw[], led[] with zeroes */
	memset(motor_dir_state, 0, sizeof(motor_dir_state));
	memset(adc, 0, sizeof(adc));
	memset(sw, 0, sizeof(sw));
	memset(led, 0, sizeof(led));

	/* ---------- IN THREAD INITIALIZE ------------- */
	// All devices pass start threads.
	in_id = k_thread_create(
		&in_thread,
		in_stack,
		K_THREAD_STACK_SIZEOF(in_stack),
		in_thread_main,
		&client,
		NULL,
		NULL,
		IN_THREAD_PRIORITY,
		0,
		K_NO_WAIT
	);
    LOG_DBG("InThread Initialized.\n");

	/* --------- OUT THREAD INITIALIZE ------------- */
	out_id = k_thread_create(
		&out_thread,
		out_stack,
		K_THREAD_STACK_SIZEOF(out_stack),
		out_thread_main,
		&client,
		NULL,
		NULL,
		OUT_THREAD_PRIORITY,
		0,
		K_NO_WAIT
	);
    LOG_DBG("OutThread Initialized.\n");
	
	/* --------- ADC THREAD INITIALIZE ------------- */
	adc_id = k_thread_create(
		&adc_thread,
		adc_stack,
		K_THREAD_STACK_SIZEOF(adc_stack),
		adc_thread_main,
		NULL,
		NULL,
		NULL,
		ADC_THREAD_PRIORITY,
		0,
		K_NO_WAIT
	);
    LOG_DBG("ADCThread Initialized.\n");
	
	server_main(&server, &client);

	kernel_exit();
	return 0;
}
