#include <zephyr/kernel.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/logging/log.h>
#include <drv8711.h>

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
    gpio_pin_set_dt(&leds[id - 1], on);
    switch_states[id - 1] = on;
}

void blinker_thread(void *p1, void *p2, void *p3) {
    bool ping = false;
    while (true) {
        for (int i = 0; i < NUM_LEDS; i++) {
            gpio_pin_set_dt(&leds[i], ping);
        }
        ping = !ping;
        LOG_ERR("hej");
        k_msleep(1000);
    }
}
