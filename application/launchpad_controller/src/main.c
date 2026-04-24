#include <zephyr/kernel.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/logging/log.h>
#include <zephyr/drivers/uart.h>
#include <zephyr/device.h>
#include <drv8711.h>
#include <ad4111.h>
#include "circbuf.h"
#include "server.h"
#include "packet.h"
#include "dhcp.h"
#include "in.h"
#include "uart.h"

/* ========================================================== */
/* =			GLOBAL CONSTANT DEFINITIONS					= */
/* ========================================================== */
#define ETHERNET_THREAD_STACK_SIZE 		4096
#define ETHERNET_THREAD_PRIORITY		1

#define UART_THREAD_STACK_SIZE 			4096
#define UART_THREAD_PRIORITY			1	// Highest priority.

#define SENSOR_THREAD_STACK_SIZE 		4096
#define SENSOR_THREAD_PRIORITY			2	
#define SENSOR_THREAD_PERIOD			1000

#define BLINKER_THREAD_STACK_SIZE 	1024
#define BLINKER_THREAD_PRIORITY		5
#define BLINKER_THREAD_PERIOD		1000
#define THREAD_EMPTYARG 			void*

#define NUM_EXT_ADC					2
#define NUM_ADC_CHANNELS			24
#define ADC_ARRAY_BYTE_SIZE			96
#define NUM_CHANNELS_PER_ADC		12
#define NUM_STEPPERS				1	// board can hold 3.
#define NUM_LEDS 					2
#define NUM_SWITCHES 				8
#define MOTOR_CURRENT_I_LIMIT		2000
#define MOTOR1_INDEX				0

#define MSG_SIZE					128
#define MSGQ_BACKLOG				4
#define MSGQ_ALIGN					1	// default by zephyr.
#define STANDARD_BAUDRATE			115200

#define SURTR_REQUEST_SYN_ACK       0
#define SURTR_REQUEST_SW_CTRL       1
#define SURTR_REQUEST_STEP_CTRL     2
#define SURTR_REQUEST_STATE     	3
#define SURTR_REQUEST_IGNITION      5

#define SURTR_MSG_SW_CTRL_INDEX_CMD			0
#define SURTR_MSG_SW_CTRL_INDEX_ID			1
#define SURTR_MSG_SW_CTRL_INDEX_STATE		2

#define SURTR_MSG_STEP_CTRL_INDEX_CMD		0
#define SURTR_MSG_STEP_CTRL_INDEX_ID		1
#define SURTR_MSG_STEP_CTRL_INDEX_STATE		2

#define SURTR_MSG_ACK_SUCCESS   	0xFF
#define SURTR_MSG_ACK_FAIL			0x00

#define SURTR_RESPONSE_INDEX_ID		0
#define SURTR_RESPONSE_INDEX_METHOD	1
#define SURTR_RESPONSE_INDEX_TIME	2
#define SURTR_RESPONSE_INDEX_CMD	10
#define SURTR_RESPONSE_INDEX_ACK	11
#define SURTR_RESPONSE_INDEX_DATA	12


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

/* ========================================================== */
/* =				THREAD DEFINITIONS						= */
/* ========================================================== */
// CONFIG_SCHED_SIMPLE ready queue will be simple unordered list.
// CONFIG_WAITQ_SIMPLE
struct k_thread uart_thread;
struct k_thread ethernet_thread;
struct k_thread blinker_thread;
struct k_thread sensor_thread;
k_tid_t uart_id;
k_tid_t ethernet_id;
k_tid_t blinker_id;
k_tid_t sensor_id;

K_THREAD_STACK_DEFINE(uart_stack, UART_THREAD_STACK_SIZE);
K_THREAD_STACK_DEFINE(ethernet_stack, ETHERNET_THREAD_STACK_SIZE);
K_THREAD_STACK_DEFINE(blinker_stack, BLINKER_THREAD_STACK_SIZE);
K_THREAD_STACK_DEFINE(sensor_stack, SENSOR_THREAD_STACK_SIZE);

/* ========================================================== */
/* =				TIMER DEFINITIONS						= */
/* ========================================================== */
struct k_timer sampling_timer;

/* ========================================================== */
/* =				SEMAPHORE DEFINITIONS					= */
/* ========================================================== */
struct k_sem sem_uart_irq;
struct k_sem sem_sampling_irq;

/* ========================================================== */
/* =				SERVER DEFINITIONS						= */
/* ========================================================== */
static struct Server server;
static struct Client client;
static uint8_t ethernet_connection;

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
K_MSGQ_DEFINE(request_msgq, MSG_SIZE, MSGQ_BACKLOG, MSGQ_ALIGN);


/**
 * ==========================================================
 * send_message():
 * 		Encodes response in packet and sends out to both UART and ETH
 * 		If there is no ETH connection then skip Ethernet.
 */
int send_message(struct Client *client, uint8_t *response, uint8_t response_size)
{
    uint8_t tx_buffer[MSG_SIZE];
    uint8_t tx_size = 0;

	LOG_DBG("Send Message.\n");

    encode_packet(response, tx_buffer, response_size, &tx_size);
	LOG_DBG("response_size: %d\n", response_size);
	LOG_DBG("packet_size: %d\n", tx_size);

    if(!uart_send_message(tx_buffer, tx_size))
    {
        LOG_ERR("Send Message failed on UART.\n");
        return 0;
    }
	LOG_DBG("UART message sent.\n");

    if(!ethernet_connection)
        return 1;

    if(!ethernet_send_message(client, tx_buffer, tx_size))
    {
        LOG_ERR("Send Message failed on ETHERNET.\n");
        return 0;
    }

    return 1;
}

/**
 * ===============================================================
 * PARSE SURTR COMMAND
 * Unpacks message and updates data accordingly.
 * MSG TYPE		ENUM	TIME (us)		RAW DATA
 * ===============================================================
 * SYN_ACK			0					| ACK |
 * SW CTRL		    1					| ID | STATE |
 * STEP CTRL		2					| ID | MOTOR DELTA |
 * ADC/SW STATE		3					| ADC[24] | SW[8] |
 * IGNITION		    5					| PASSWORD |
 * 
 */
/**
 * ==========================================================
 * ask_server():
 *      Waits for job to be placed in queue by UART or ETH (CoAP protocol)
 *      Serve / Execute specific command.
 *      k_msgq_put(): 
 *      0        Success
 *      -ENOMSG  returned without waiting or queue purged.
 *      -EAGAIN  waiting period timed out
 */
void ask_server(struct Server *server, struct Client *client)
{
    LOG_DBG("Entering Server_main().\n");
    uint8_t payload_buffer[MSG_SIZE];
    uint8_t response[MSG_SIZE];
    uint8_t response_size = 0;

    while(1)
    {
		LOG_DBG("Ask server waiting for request.\n");
        if(k_msgq_get(&request_msgq, payload_buffer, K_FOREVER) != 0)
        {
            LOG_WRN("Message Queue failed to get item.\n");
            return 0;
        }
		LOG_DBG("Message Recieved from Request Queue.\n");

		/* -------- Mirror Request Unique ID -------------- */
		response[0] = payload_buffer[0];
        response_size++;

		/* -------- Mirror Request UART/ETH --------------- */
		response[1] = payload_buffer[1];
        response_size++;
        
		/* -------- Save Current Time --------------------- */
        int64_t ms_since_boot = k_uptime_get();
        memcpy(response+2, &ms_since_boot, sizeof(ms_since_boot));
        response_size += 8;

        /* -------- Save Command Requested ---------------- */
        const uint8_t cmd = payload_buffer[10];
        response[10] = cmd;
        response_size++;
		
		LOG_DBG("Unique ID: %d, Method: %d, CMD: %d\n", payload_buffer[0], payload_buffer[1], payload_buffer[10]);
                    
        /* -------- Add ACK after Command ----------------- */
		surtr_syn_ack(response, &response_size);

        /* -------- Execute Request Command --------------- */
        switch (cmd)
        {
            case SURTR_REQUEST_SYN_ACK:
					LOG_DBG("SURTR_REQUEST_SYN_ACK\n");
                break;

            case SURTR_REQUEST_SW_CTRL:
					LOG_DBG("SURTR_REQUEST_SW_CTRL\n");
                    surtr_sw_ctrl(payload_buffer[11], payload_buffer[12]);
                break;

            case SURTR_REQUEST_STEP_CTRL:
                    surtr_step_ctrl(payload_buffer);
                break;

            case SURTR_REQUEST_IGNITION:
                    LOG_ERR("Ignition does nothing for now.\n");
                break;

            default:
                LOG_ERR("Invalid Surtr Command.\n");
                break;
        }

        /* -------- Send Response Back -------------------- */
        if(!send_message(client, response, response_size))
        {
            LOG_ERR("Send Message failed.\n");
        }

        /* -------- Reset Response ------------------------ */
		response_size = 0;
    }
}

/**
 * ==========================================================
 * uart_thread_main():
 *      Waits for IRQ to fire which releases counting semaphore (+1)
 *      Begins handling request sent over UART.
 *      Pass request via MSGQ to ask_server.
 */
void uart_thread_main(struct Client* client, THREAD_EMPTYARG, THREAD_EMPTYARG)
{
    LOG_DBG("UART Thread Enter.\n");
	uint8_t payload_size;

    while(1)
    {
        uart_wait_IRQ();

		LOG_DBG("UART IRQ received.\n");

		if(!uart_handle_request(&rx_circbuf))
		{
            LOG_DBG("InThread Request Failed.\n");
			continue;
		}
        LOG_DBG("UART Thread Request Handled.\n");
    }
}

/**
 * ==========================================================
 * ethernet_thread_main():
 *      When connection is established, thread will enter ethnernet_handle_request()
 *      and stay there until connection fails.
 *      Blocking read on recv().
 */
void ethernet_thread_main(struct Server *server, struct Client *client, THREAD_EMPTYARG)
{
    while(1)
    {
        ethernet_connection = 0;
        if(accept_connection(server, client))
        {
            ethernet_connection = 1;
            ethernet_handle_request(client);
            close(client->socket);
        }
            
        LOG_DBG("TCP accept connection failed.\n");
    }

}


/**
 * ==========================================================
 * blinker_main_thread():
 * 		PERIOD of 1000 msec
 * 		Turns LED on/off to indicate SURTR is alive.
 */
void blinker_thread_main(THREAD_EMPTYARG, THREAD_EMPTYARG, THREAD_EMPTYARG)
{
	uint8_t led_state = 0;
	while(1)
	{
		blink_leds(led_state);
		led_state = !led_state;
		k_msleep(BLINKER_THREAD_PERIOD);
	}
}

/**
 * ==========================================================
 * sensor_thread_main():
 * 		PERIOD of 100 ms
 * 		Construct response which includes timestamp, adc, sw
 * 		0		 1	    2	   
 * 		| UNIQID | CMD | TIME | ADC[0-23] | SW[0-7]
 * 		
 */
void sensor_thread_main(struct Client *client, THREAD_EMPTYARG, THREAD_EMPTYARG)
{
	uint8_t response[MSG_SIZE];
	uint8_t response_size = 0;
    const uint8_t cmd = 3;

	while(1)
	{
		/* -------- Wait for Timer IRQ -------------------- */
		k_sem_take(&sem_sampling_irq, K_FOREVER);

		LOG_DBG("Sensor Thread begin iteraiton.\n");

		/* -------- Sensor Sampling Unique ID ------------- */
		response[SURTR_RESPONSE_INDEX_ID] = 0xFF;
        response_size++;

		// Assumes UART for now?
		response[SURTR_RESPONSE_INDEX_METHOD] = 0x00;
        response_size++;
    
        /* -------- Save Current Time --------------------- */
        int64_t ms_since_boot = k_uptime_get();
        memcpy(SURTR_RESPONSE_INDEX_TIME, &ms_since_boot, sizeof(ms_since_boot));
        response_size += 8;
        
		/* -------- Save Command Requested ---------------- */
        response[SURTR_RESPONSE_INDEX_CMD] = cmd;
        response_size++;
                    
        /* -------- Add ACK after Command ----------------- */
		surtr_syn_ack(response, &response_size);

        /* -------- Read ADC / SW States ------------------ */
		surtr_get_adc_state(response, &response_size);
		surtr_get_sw_state(response, &response_size);
        
		/* -------- Send Response Back -------------------- */
        if(!send_message(client, response, response_size))
        {
            LOG_ERR("Send Message failed.\n");
        }
		LOG_DBG("Sensor Thread Message sent.\n");

        /* -------- Reset Response ------------------------ */
		response_size = 0;
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

	memset(rx_buffer, 0, MSG_SIZE);
	circbuf_construct(&rx_circbuf, &rx_buffer, MSG_SIZE);

	if (uart_irq_callback_user_data_set(uart_dev, uart_isr, &rx_circbuf) < 0)
		FATALERROR("External UART ISR callback failed.");

	// Enable Interrupts before threads can be dangerous.
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
	k_timer_init(&sampling_timer, sampling_isr, NULL);
	k_timer_start(
		&sampling_timer, 
		K_MSEC(SENSOR_THREAD_PERIOD), 
		K_MSEC(SENSOR_THREAD_PERIOD));
	
	/* ---------- SEMAPHORE INITIALIZE ------------- */
	// initial = 0, count = 2 (2 threads);
    k_sem_init(&sem_uart_irq, 0, 5);
    k_sem_init(&sem_sampling_irq, 0, 1);
	
	/* ---------- RESET STATIC ARRAYS -------------- */
	/* Initialize adc[], sw[], led[] with zeroes */
	memset(motor_dir_state, 0, sizeof(motor_dir_state));
	memset(adc, 0, sizeof(adc));
	memset(sw, 0, sizeof(sw));
	memset(led, 0, sizeof(led));

	/* ---------- UART THREAD INITIALIZE ----------- */
	// All devices pass start threads.
	uart_id = k_thread_create(
		&uart_thread,
		uart_stack,
		K_THREAD_STACK_SIZEOF(uart_stack),
		uart_thread_main,
		&client,
		NULL,
		NULL,
		UART_THREAD_PRIORITY,
		0,
		K_NO_WAIT
	);
    LOG_DBG("UART Thread Initialized.\n");

	/* --------- ETHERNET THREAD INITIALIZE -------- */
	/*
	ethernet_id = k_thread_create(
		&ethernet_thread,
		ethernet_stack,
		K_THREAD_STACK_SIZEOF(ethernet_stack),
		ethernet_thread_main,
		&client,
		NULL,
		NULL,
		ETHERNET_THREAD_PRIORITY,
		0,
		K_NO_WAIT
	);
    LOG_DBG("ETHERNET Thread Initialized.\n");
	*/
	
	/* --------- BLINKER THREAD INITIALIZE -------- */
	blinker_id = k_thread_create(
		&blinker_thread,
		blinker_stack,
		K_THREAD_STACK_SIZEOF(blinker_stack),
		blinker_thread_main,
		NULL,
		NULL,
		NULL,
		BLINKER_THREAD_PRIORITY,
		0,
		K_NO_WAIT
	);
    LOG_DBG("BLINKER Thread Initialized.\n");
	
	/* --------- SENSOR THREAD INITIALIZE -------- */
	/*
	sensor_id = k_thread_create(
		&sensor_thread,
		sensor_stack,
		K_THREAD_STACK_SIZEOF(sensor_stack),
		sensor_thread_main,
		&client,
		NULL,
		NULL,
		SENSOR_THREAD_PRIORITY,
		0,
		K_NO_WAIT
	);
    LOG_DBG("SENSOR Thread Initialized.\n");
	*/
	
	ask_server(&server, &client);

	kernel_exit();
	return 0;
}
