#include <zephyr.h>
#include <device.h>
#include <drivers/spi.h>
#include <drivers/gpio.h>
#include <logging/log.h>

LOG_MODULE_REGISTER(stepper_driver, LOG_LEVEL_DBG);

#define SPI3_LABEL DT_LABEL(DT_NODELABEL(spi3))

struct spi_config spi_cfg = {
    .frequency = 1000000,
    .operation = SPI_OP_MODE_MASTER | SPI_WORD_SET(8),
    .slave = 0,
    .cs = NULL,
};

const struct device *spi_dev;

static void init_stepper_driver(void) {
    spi_dev = device_get_binding(SPI3_LABEL);
    if (!spi_dev) {
        LOG_ERR("SPI device not found");
        return;
    }

    //to add here
}

static void set_stepper_direction(uint8_t motor, bool direction) {
    
    const struct device *gpio_dev;
    gpio_dev = device_get_binding(DT_GPIO_LABEL(DT_NODELABEL(gpiod), gpios));
    if (!gpio_dev) {
        LOG_ERR("Failed to bind GPIO device");
        return;
    }

    uint32_t pin = 0;
    switch (motor) {
        case 1: pin = 2; break; // pin 2
        case 2: pin = 4; break; // pin 4
        case 3: pin = 6; break; // pin 6
        default: LOG_ERR("Invalid motor number"); return;
    }

    gpio_pin_configure(gpio_dev, pin, GPIO_OUTPUT);
    gpio_pin_set(gpio_dev, pin, direction);
}

static void step_motor(uint8_t motor) {
    uint8_t data[2] = {0x00, 0x01}; // example command
    struct spi_buf tx_buf = {
        .buf = data,
        .len = sizeof(data),
    };
    struct spi_buf_set tx = {
        .buffers = &tx_buf,
        .count = 1,
    };

    spi_cfg.slave = motor - 1;
    if (spi_write(spi_dev, &spi_cfg, &tx)) {
        LOG_ERR("Failed to step motor %d", motor);
    }
}

void main(void) {
    init_stepper_driver();

    //test
    set_stepper_direction(1, true);
    step_motor(1);

    while (1) {
        k_sleep(K_SECONDS(1));
        step_motor(1);
    }
}
