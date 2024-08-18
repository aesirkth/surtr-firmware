#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>

#include "steppers.h"
#include "ignition.h"
#include "actuation.h"

LOG_MODULE_REGISTER(ignition, CONFIG_APP_LOG_LEVEL);

void ignition_thread(void *p1, void *p2, void *p3);

K_THREAD_DEFINE(ignition_tid, 4096, ignition_thread, NULL, NULL, NULL, 2, 0, 2000);

#define PYRO_SWITCH 4
#define VALVE_PARTIAL_OPENING 100
#define VALVE_FULL_OPENING 250

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

        target_motor1 = VALVE_PARTIAL_OPENING;
        LOG_INF("motor1 partial opening");
        k_msleep(200);
        target_motor2 = VALVE_PARTIAL_OPENING;
        LOG_INF("motor2 partial opening");
        k_msleep(500);
        toggle_switch(PYRO_SWITCH, true);
        LOG_INF("enabling pyro");
        k_msleep(200);
        target_motor1 = VALVE_FULL_OPENING;
        target_motor2 = VALVE_FULL_OPENING;
        LOG_INF("Valves fully opening");
        k_msleep(3000);
        toggle_switch(PYRO_SWITCH, false);
    }
}