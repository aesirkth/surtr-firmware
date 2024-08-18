#include <zephyr/kernel.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/logging/log.h>

#include "steppers.h"

LOG_MODULE_REGISTER(stepper, CONFIG_APP_LOG_LEVEL);

#define PULSE_LENGTH_US 250
#define PULSE_EVERY_US 500

_Atomic int32_t target_motor1 = 0;
_Atomic int32_t target_motor2 = 0;

_Atomic int32_t current_motor1 = 0;
_Atomic int32_t current_motor2 = 0;

void steppers_thread(void *p1, void *p2, void *p3);

K_THREAD_DEFINE(steppers_tid, 4096, steppers_thread, NULL, NULL, NULL, 1, 0, 2000);

void steppers_thread(void *p1, void *p2, void *p3) {
    const struct device *motor1 = DEVICE_DT_GET(DT_ALIAS(motor1));
    const struct device *motor2 = DEVICE_DT_GET(DT_ALIAS(motor2));

    if (device_is_ready(motor1)) {
        LOG_INF("Motor1 ready");
    } else {
        LOG_ERR("Motor1 not initialized");
    }

    if (device_is_ready(motor2)) {
        LOG_INF("Motor2 ready");
    } else {
        LOG_ERR("Motor2 not initialized");
    }

    const struct gpio_dt_spec motor1_dir_dt = GPIO_DT_SPEC_GET(DT_NODELABEL(step1_dir), gpios);
    const struct gpio_dt_spec motor2_dir_dt = GPIO_DT_SPEC_GET(DT_NODELABEL(step2_dir), gpios);
    gpio_pin_configure_dt(&motor1_dir_dt, GPIO_OUTPUT_ACTIVE);
    gpio_pin_configure_dt(&motor2_dir_dt, GPIO_OUTPUT_ACTIVE);

    const struct gpio_dt_spec motor1_step_dt = GPIO_DT_SPEC_GET(DT_NODELABEL(step1_ctrl), gpios);
    const struct gpio_dt_spec motor2_step_dt = GPIO_DT_SPEC_GET(DT_NODELABEL(step2_ctrl), gpios);
    gpio_pin_configure_dt(&motor1_step_dt, GPIO_OUTPUT_ACTIVE);
    gpio_pin_configure_dt(&motor2_step_dt, GPIO_OUTPUT_ACTIVE);

    while (true) {
        int dir1 = 0;
        int dir2 = 0;
        if (current_motor1 < target_motor1) {
            gpio_pin_set_dt(&motor1_dir_dt, 1);
            dir1 = 1;
        }
        if (current_motor1 > target_motor1) {
            gpio_pin_set_dt(&motor1_dir_dt, 0);
            dir1 = -1;
        }


        if (current_motor2 < target_motor2) {
            gpio_pin_set_dt(&motor2_dir_dt, 1);
            dir2 = 1;
        }
        if (current_motor2 > target_motor2) {
            gpio_pin_set_dt(&motor2_dir_dt, 0);
            dir2 = -1;
        }

        if (current_motor2 != target_motor1) {
            gpio_pin_set_dt(&motor1_step_dt, 1);
        }
        if (current_motor2 != target_motor2) {
            gpio_pin_set_dt(&motor2_step_dt, 1);
        }

        k_usleep(PULSE_LENGTH_US);

        if (current_motor1 != target_motor1) {
            gpio_pin_set_dt(&motor1_step_dt, 0);
            current_motor1 += dir1;
        }
        if (current_motor2 != target_motor2) {
            gpio_pin_set_dt(&motor2_step_dt, 0);
            current_motor2 += dir2;
        }
        k_usleep(PULSE_EVERY_US - PULSE_LENGTH_US);
    }
}