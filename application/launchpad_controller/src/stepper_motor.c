#include <zephyr.h>
#include <device.h>
#include <drivers/gpio.h>
#include <logging/log.h>

LOG_MODULE_REGISTER(stepper_motor, LOG_LEVEL_INF);

#define STEP1_CTRL_NODE DT_ALIAS(stepper1_control)
#define STEP1_DIR_NODE  DT_ALIAS(stepper1_direction)
#define STEP2_CTRL_NODE DT_ALIAS(stepper2_control)
#define STEP2_DIR_NODE  DT_ALIAS(stepper2_direction)
#define STEP3_CTRL_NODE DT_ALIAS(stepper3_control)
#define STEP3_DIR_NODE  DT_ALIAS(stepper3_direction)

struct stepper_motor {
    const struct device *ctrl_dev;
    const struct device *dir_dev;
    gpio_pin_t ctrl_pin;
    gpio_pin_t dir_pin;
};

static struct stepper_motor step1;
static struct stepper_motor step2;
static struct stepper_motor step3;

static int stepper_init(struct stepper_motor *motor, const char *ctrl_label, gpio_pin_t ctrl_pin, const char *dir_label, gpio_pin_t dir_pin)
{
    motor->ctrl_dev = device_get_binding(ctrl_label);
    if (!motor->ctrl_dev) {
        LOG_ERR("Failed to get control device binding for %s", ctrl_label);
        return -ENODEV;
    }
    motor->dir_dev = device_get_binding(dir_label);
    if (!motor->dir_dev) {
        LOG_ERR("Failed to get direction device binding for %s", dir_label);
        return -ENODEV;
    }

    motor->ctrl_pin = ctrl_pin;
    motor->dir_pin = dir_pin;

    gpio_pin_configure(motor->ctrl_dev, motor->ctrl_pin, GPIO_OUTPUT);
    gpio_pin_configure(motor->dir_dev, motor->dir_pin, GPIO_OUTPUT);

    return 0;
}

static void stepper_step(struct stepper_motor *motor, bool direction, int steps)
{
    gpio_pin_set(motor->dir_dev, motor->dir_pin, direction);

    for (int i = 0; i < steps; i++) {
        gpio_pin_toggle(motor->ctrl_dev, motor->ctrl_pin);
        k_msleep(1); // Adjust delay for motor
        gpio_pin_toggle(motor->ctrl_dev, motor->ctrl_pin);
        k_msleep(1);
    }
}

void main(void)
{
    if (stepper_init(&step1, DT_GPIO_LABEL(STEP1_CTRL_NODE, gpios), DT_GPIO_PIN(STEP1_CTRL_NODE, gpios),
                     DT_GPIO_LABEL(STEP1_DIR_NODE, gpios), DT_GPIO_PIN(STEP1_DIR_NODE, gpios)) < 0) {
        LOG_ERR("Failed to initialize Stepper Motor 1");
        return;
    }

    if (stepper_init(&step2, DT_GPIO_LABEL(STEP2_CTRL_NODE, gpios), DT_GPIO_PIN(STEP2_CTRL_NODE, gpios),
                     DT_GPIO_LABEL(STEP2_DIR_NODE, gpios), DT_GPIO_PIN(STEP2_DIR_NODE, gpios)) < 0) {
        LOG_ERR("Failed to initialize Stepper Motor 2");
        return;
    }

    if (stepper_init(&step3, DT_GPIO_LABEL(STEP3_CTRL_NODE, gpios), DT_GPIO_PIN(STEP3_CTRL_NODE, gpios),
                     DT_GPIO_LABEL(STEP3_DIR_NODE, gpios), DT_GPIO_PIN(STEP3_DIR_NODE, gpios)) < 0) {
        LOG_ERR("Failed to initialize Stepper Motor 3");
        return;
    }

    LOG_INF("Stepper motors initialized");

    while (1) {
        stepper_step(&step1, true, 200);
        k_msleep(1000);
        stepper_step(&step1, false, 200);
        k_msleep(1000);
    }
}
