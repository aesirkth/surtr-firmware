#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>

#include "steppers.h"
#include "ignition.h"
#include "actuation.h"

LOG_MODULE_REGISTER(ignition, CONFIG_APP_LOG_LEVEL);

void ignition_thread(void *p1, void *p2, void *p3);

K_THREAD_DEFINE(ignition_tid, 4096, ignition_thread, NULL, NULL, NULL, 2, 0, 2000);

#define PYRO_SWITCH 4

#define VALVE1_PARTIAL_OPENING 2500

#define VALVE2_PARTIAL_OPENING 2200

#define VALVE1_FULL_OPENING 4500
#define VALVE2_FULL_OPENING 4400

volatile bool should_start_ignition_sequence;

void start_ignition_sequence() {
    LOG_WRN("Starting ignition!");
    should_start_ignition_sequence = true;
}

void ignition_thread(void *p1, void *p2, void *p3) {
    while (true) {
        k_msleep(100);
        if (!should_start_ignition_sequence) {
            continue;
        }
        should_start_ignition_sequence = false;

        target_motor1 += VALVE1_PARTIAL_OPENING;
        k_msleep(300);
        target_motor2 += VALVE2_PARTIAL_OPENING;
        LOG_INF("motor1 partial opening");
        LOG_INF("motor2 partial opening");
        k_msleep(1200);
        toggle_switch(PYRO_SWITCH, true);
        LOG_WRN("enabling pyro");
        k_msleep(2500);
        target_motor1 += VALVE1_FULL_OPENING - VALVE1_PARTIAL_OPENING;
        target_motor2 += VALVE2_FULL_OPENING - VALVE2_PARTIAL_OPENING;
        LOG_INF("Valves fully opening");
        k_msleep(2000);
        toggle_switch(PYRO_SWITCH, false);
    }
}