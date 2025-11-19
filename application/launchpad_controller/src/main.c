/*
 * Copyright (c) 2017 Linaro Limited
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <stdio.h>
#include <stdlib.h>
#include <errno.h>

#include <zephyr/net/socket.h>
#include <zephyr/kernel.h>

#include <zephyr/net/net_pkt.h>

#include <zephyr/logging/log.h>
#include <pb_encode.h>
#include <pb_decode.h>

// ADC includes
#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>

#include "networking.h"
#include "sensors.h"
#include "actuation.h"

LOG_MODULE_REGISTER(main, CONFIG_APP_LOG_LEVEL);

int main(void)
{
    // Start actuation and networking threads. Sensors are started when module is linked.
	init_actuation(NULL, NULL, NULL);
    init_networking(NULL, NULL, NULL);
	while (1) {
        LOG_INF("I'm alive");
        k_sleep(K_MSEC(4000));
    }
}
