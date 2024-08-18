#include <zephyr/kernel.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/logging/log.h>
#include <drv8711.h>

#include "protocol.h"
#include "networking.h"
#include "steppers.h"

LOG_MODULE_REGISTER(actuation, CONFIG_APP_LOG_LEVEL);

static const struct gpio_dt_spec leds[] = {
    GPIO_DT_SPEC_GET(DT_ALIAS(led0), gpios),
    GPIO_DT_SPEC_GET(DT_ALIAS(led1), gpios),
};
#define NUM_LEDS sizeof(leds) / sizeof(leds[0])

static const struct gpio_dt_spec switches[] = {
    GPIO_DT_SPEC_GET(DT_ALIAS(switch1), gpios),
    GPIO_DT_SPEC_GET(DT_ALIAS(switch2), gpios),
    GPIO_DT_SPEC_GET(DT_ALIAS(switch3), gpios),
    GPIO_DT_SPEC_GET(DT_ALIAS(switch4), gpios),
    GPIO_DT_SPEC_GET(DT_ALIAS(switch5), gpios),
    GPIO_DT_SPEC_GET(DT_ALIAS(switch6), gpios),
    GPIO_DT_SPEC_GET(DT_ALIAS(switch7), gpios),
    GPIO_DT_SPEC_GET(DT_ALIAS(switch8), gpios),
};
#define NUM_SWITCHES (sizeof(switches) / sizeof(switches[0]))

void blinker_thread(void *p1, void *p2, void *p3);

K_THREAD_DEFINE(blinker_tid, 2048, blinker_thread, NULL, NULL, NULL, 5, 0, 1000);

volatile bool switch_states[NUM_SWITCHES] = {0};

void init_actuation(void *p1, void *p2, void *p3) {
    // initialize switches
    int ret;
    for(int i = 0; i < NUM_SWITCHES; i++) {
        if (!gpio_is_ready_dt(&switches[i])) {
            LOG_ERR("switch gpio is not ready");
        }

        ret = gpio_pin_configure_dt(&switches[i], GPIO_OUTPUT_INACTIVE);
        if (ret < 0) {
            LOG_ERR("switch gpio couldn't be configured");
        }
    }


    // initialize LEDs
    for (int i = 0; i < NUM_LEDS; i++) {
        if (!gpio_is_ready_dt(&leds[i])) {
            LOG_ERR("led gpio is not ready");
        }

        ret = gpio_pin_configure_dt(&leds[i], GPIO_OUTPUT_INACTIVE);
        if (ret < 0) {
            LOG_ERR("led gpio couldn't be configured");
        }
    }

}

void toggle_switch(int id, bool on) {
    if (id >= NUM_SWITCHES) {
        LOG_WRN("tried to toggle invalid switch");
        return;
    }
    gpio_pin_set_dt(&switches[id - 1], on);
    switch_states[id - 1] = on;
}

void blinker_thread(void *p1, void *p2, void *p3) {
    bool ping = false;
    while (true) {
        for (int i = 0; i < NUM_LEDS; i++) {
            gpio_pin_set_dt(&leds[i], ping);
        }
        ping = !ping;
        k_msleep(100);

        surtrpb_SurtrMessage msg;
        msg.has_us_since_boot = true;
        msg.us_since_boot = k_uptime_get() * 1000; // epic
        msg.which_command = surtrpb_SurtrMessage_switch_states_tag;
        msg.command.switch_states.sw1 = switch_states[0];
        msg.command.switch_states.sw2 = switch_states[1];
        msg.command.switch_states.sw3 = switch_states[2];
        msg.command.switch_states.sw4 = switch_states[3];
        msg.command.switch_states.sw5 = switch_states[4];
        msg.command.switch_states.sw6 = switch_states[5];
        msg.command.switch_states.sw7 = switch_states[6];
        msg.command.switch_states.sw8 = switch_states[7];
        msg.command.switch_states.step1 = current_motor1;
        msg.command.switch_states.step2 = current_motor2;

        send_msg(&msg);
    }
}
