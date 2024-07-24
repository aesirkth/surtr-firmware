/*
 * Copyright (c) 2017 Linaro Limited
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <stdio.h>
#include <stdlib.h>
#include <errno.h>

#if !defined(__ZEPHYR__) || defined(CONFIG_POSIX_API)

#include <netinet/in.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <unistd.h>

#else

#include <zephyr/net/socket.h>
#include <zephyr/kernel.h>

#include <zephyr/net/net_pkt.h>

#endif

#include <zephyr/drivers/gpio.h>
#include "steppers.h"

#include <zephyr/logging/log.h>
#include "src/commands.pb.h"
#include "src/sensor_vals.pb.h"
#include <pb_encode.h>
#include <pb_decode.h>

// ADC includes
#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
// #include "../modules/drivers/inc/ad4111.h"
#include "../modules/ad4111/src/ad4111.h"
// #include "networking.h"

#if !DT_NODE_EXISTS(DT_NODELABEL(ext_adc1))
#error "whoops, no adc1"
#endif
#if !DT_NODE_EXISTS(DT_NODELABEL(ext_adc2))
#error "whoops, no adc2"
#endif

// end ADC includes

#define BIND_PORT 8080

#define CHECK(r) { if (r == -1) { printk("Error: " #r "\n"); exit(1); } }

/* If accept returns an error, then we are probably running
 * out of resource. Sleep a small amount of time in order the
 * system to cool down.
 */
#define ACCEPT_ERROR_WAIT 100 /* in ms */

static void sleep_after_error(unsigned int amount)
{
#if defined(__ZEPHYR__)
	k_msleep(amount);
#else
	usleep(amount * 1000U);
#endif
}

#define LED0_NODE DT_ALIAS(led0)
#define LED1_NODE DT_ALIAS(led1)

#define SWITCH1_NODE DT_ALIAS(switch1)
#define SWITCH2_NODE DT_ALIAS(switch2)
#define SWITCH3_NODE DT_ALIAS(switch3)
#define SWITCH4_NODE DT_ALIAS(switch4)

#define aesirADC1 DT_NODELABEL(ext_adc1)
#define aesirADC2 DT_NODELABEL(ext_adc2)

LOG_MODULE_REGISTER(main);

static const struct gpio_dt_spec leds[] = {
    GPIO_DT_SPEC_GET(LED0_NODE, gpios),
    GPIO_DT_SPEC_GET(LED1_NODE, gpios),
};

static const struct gpio_dt_spec switches[] = {
    GPIO_DT_SPEC_GET(SWITCH1_NODE, gpios),
    GPIO_DT_SPEC_GET(SWITCH2_NODE, gpios),
    GPIO_DT_SPEC_GET(SWITCH3_NODE, gpios),
    GPIO_DT_SPEC_GET(SWITCH4_NODE, gpios),
};


// read and write callbacks taken from common.c in deps/modules/lib/nanopb/examples/network_server
static bool write_callback(pb_ostream_t *stream, const uint8_t *buf, size_t count)
{
    int fd = (intptr_t)stream->state;
    return send(fd, buf, count, 0) == count;
}

static bool read_callback(pb_istream_t *stream, uint8_t *buf, size_t count)
{
    int fd = (intptr_t)stream->state;
    int result;
    
    if (count == 0)
        return true;

    result = recv(fd, buf, count, MSG_WAITALL);
    
    if (result == 0)
        stream->bytes_left = 0; /* EOF */
    
    return result == count;
}

int main(void)
{ 
    // should use a better data structure for this (struct!)
    // initialize switches
    bool switch_states[] = {0,0,0,0};
    int ret;
    for(int i = 0; i < 4; i++) {
        if (!gpio_is_ready_dt(&switches[i])) {
        return 0;
        }

        ret = gpio_pin_configure_dt(&switches[i], GPIO_OUTPUT_INACTIVE);
        if (ret < 0) {
            return 0;
        }   
    }


    // initialize LEDs

    bool led_states[] = {0, 0};
    for (int i = 0; i < 2; i++) {
        if (!gpio_is_ready_dt(&leds[i])) {
        return 0;
        }

        ret = gpio_pin_configure_dt(&leds[i], GPIO_OUTPUT_INACTIVE);
        if (ret < 0) {
            return 0;
        }   
    }

    // begin ADC initialization
    LOG_INF("++ Initiliazing... ++");

    // Let's go..!
    LOG_INF("++ Starting ADC initialization ++");

    // Create adc driver instances
    const struct device *adc1 = DEVICE_DT_GET(aesirADC1);
    const struct device *adc2 = DEVICE_DT_GET(aesirADC2);

    /* Retrieve the device binding for the first ADC */
    // adc1 = device_get_binding("ad4111_1");
    if (!device_is_ready(adc1)) {
        LOG_INF("ad4111_1 failed to get binding");
        return -1;  // Indicate error
    } else {
    LOG_INF("ad4111_1 successfully retrieved");
    }

    /* Retrieve the device binding for the second ADC */
    // adc2 = device_get_binding("ad4111@1"); // For debugging
    // adc2 = device_get_binding("ad4111_2");
    if (!device_is_ready(adc2)) {
        LOG_ERR("ad4111_2 failed to get binding");
        return -1;  // Indicate error
    } else {
        LOG_INF("ad4111_2 successfully retrieved");
    }

    /* Initialize the first ADC */
    if (adc_init(adc1) != 0) {
        LOG_ERR("ad4111_1 failed to initialize");
        return -1;  // Indicate error
    } else {
        LOG_INF("ad4111_1 successfully initialized");
    }

    /* Initialize the second ADC */
    if (adc_init(adc2) != 0) {
        LOG_ERR("ad4111_2 failed to initialize");
        return -1;  // Indicate error
    } else {
        LOG_INF("ad4111_2 successfully initialized");
    }

    // Fail or success! 
    LOG_INF("++ Finished ADC initialization ++");

    // End ADC initialization

    target_motor1 += 10000;
    target_motor2 += 10000;

    // quick test of led0

    // wait 1s, turn on
    // k_msleep(1000);
    // ret = gpio_pin_toggle_dt(&leds[0]);
    // led_states[0] = !led_states[0];

    // // wait 1s, turn off
    // k_msleep(1000);
    // ret = gpio_pin_toggle_dt(&leds[0]);
    // led_states[0] = !led_states[0];

    // initialize TCP socket
	int serv;
	struct sockaddr_in bind_addr;
	static int counter;

	serv = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
	CHECK(serv);

	bind_addr.sin_family = AF_INET;
	bind_addr.sin_addr.s_addr = htonl(INADDR_ANY);
	bind_addr.sin_port = htons(BIND_PORT);
	CHECK(bind(serv, (struct sockaddr *)&bind_addr, sizeof(bind_addr)));

	CHECK(listen(serv, 5));

	printk("Single-threaded dumb HTTP server waits for a connection on "
	       "port %d...\n", BIND_PORT);

    while (1) {
        struct sockaddr_in client_addr;
        socklen_t client_addr_len = sizeof(client_addr);
        char addr_str[32];
        // int req_state = 0;
        // size_t len;

        int client = accept(serv, (struct sockaddr *)&client_addr,
                    &client_addr_len);
        if (client < 0) {
            printk("Error in accept: %d - continuing\n", errno);
            sleep_after_error(ACCEPT_ERROR_WAIT);
            continue;
        }
        inet_ntop(client_addr.sin_family, &client_addr.sin_addr,
            addr_str, sizeof(addr_str));
        printk("Connection #%d from %s\n", counter++, addr_str);

        pb_ostream_t protoOutputStream = {&write_callback, (void*)(intptr_t) client, SIZE_MAX, 0};
        pb_istream_t protoInputStream = {&read_callback, (void*)(intptr_t) client, SIZE_MAX, 0};

        /* Discard HTTP request (or otherwise client will get
        * connection reset error).
        */

        char command_data[100];
        // for (int i = 0; i < 100; i++) {
        //     command_data[i] = '\0';
        // }
        memset(command_data, 0, sizeof(command_data));
        int commandDataOffset = 0;
        while (1) {
            ssize_t r;
            char c;

            r = recv(client, &c, 1, 0);
            if (r == 0) {
                goto close_client;
            }

            if (r < 0) {
                if (errno == EAGAIN || errno == EINTR) {
                    continue;
                }

                printk("Got error %d when receiving from "
                    "socket\n", errno);
                goto close_client;
            }

            if(c == '\n') {
                break;
            }
            else {
                command_data[commandDataOffset++] = c;
            }
        }

        // logic here
        if(!strcmp(command_data, "ignition")) {

        }
        else if(!strcmp(command_data, "abort")) {

        }
        else if(!strcmp(command_data, "switch1")) {
            switch_states[0] = !switch_states[0];
            ret = gpio_pin_set_dt(&switches[0], switch_states[0]);

            led_states[0] = !led_states[0];
            ret = gpio_pin_set_dt(&leds[0], led_states[0]);
        }
        else if(!strcmp(command_data, "switch2")) {
            ret = gpio_pin_toggle_dt(&switches[1]);
            switch_states[1] = !switch_states[1];

            ret = gpio_pin_toggle_dt(&leds[1]);
            led_states[1] = !led_states[1];

        }
        else if(!strcmp(command_data, "switch3")) {
            ret = gpio_pin_toggle_dt(&switches[2]);
            switch_states[2] = !switch_states[2];
        }
        else if(!strcmp(command_data, "switch4")) {
            ret = gpio_pin_toggle_dt(&switches[3]);
            switch_states[3] = !switch_states[3];
        }
        else if(!strcmp(command_data, "led0")) {
            ret = gpio_pin_toggle_dt(&leds[0]);
            led_states[0] = !led_states[0];
        }
        else if(!strcmp(command_data, "led1")) {
            ret = gpio_pin_toggle_dt(&leds[1]);
            led_states[1] = !led_states[1];
        }
        else if(!strcmp(command_data, "step1")) {
            target_motor1 += 100;
        }
        else if(!strcmp(command_data, "step2")) {
            target_motor2 += 100;   
        }

        memset(command_data, 0, sizeof(command_data));
        commandDataOffset = 0;
        // here to add stepper stepping ourselves

        // use this to mirror a state packet
        // state packet looks like: {switches state, calculated stepper state}
        // char buf = "ok\n";
        // len = 3;
        // while (len) {
        //     int sent_len = send(client, buf, len, 0);

        //     if (sent_len == -1) {
        //         printk("Error sending data to peer, errno: %d\n", errno);
        //         break;
        //     }
        //     buf += sent_len;
        //     len -= sent_len;
        // }
        // continue;
close_client:
		ret = close(client);
		if (ret == 0) {
			printk("Connection from %s closed\n", addr_str);
		} else {
			printk("Got error %d while closing the "
			       "socket\n", errno);
		}

#if defined(__ZEPHYR__) && defined(CONFIG_NET_BUF_POOL_USAGE)
		struct k_mem_slab *rx, *tx;
		struct net_buf_pool *rx_data, *tx_data;

		net_pkt_get_info(&rx, &tx, &rx_data, &tx_data);
		printk("rx buf: %d, tx buf: %d\n",
		       atomic_get(&rx_data->avail_count), atomic_get(&tx_data->avail_count));
#endif

	}
	return 0;
}
