#include <zephyr/kernel.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/drivers/spi.h>
#include <zephyr/logging/log.h>

#include "steppers.h"


#define REG_CTRL   0x00
#define REG_TORQUE 0x01
#define REG_OFF    0x02
#define REG_BLANK  0x03
#define REG_DECAY  0x04
#define REG_STALL  0x05
#define REG_DRIVE  0x06
#define REG_STATUS 0x07

#define MICROSTEP1      0b0000
#define MICROSTEP2      0b0001
#define MICROSTEP4      0b0010
#define MICROSTEP8      0b0011
#define MICROSTEP16     0b0100
#define MICROSTEP32     0b0101
#define MICROSTEP64     0b0110
#define MICROSTEP128    0b0111
#define MICROSTEP256    0b1000


#define DECAY_SLOW                    0b000
#define DECAY_SLOW_INC_MIXED_DEC      0b001
#define DECAY_FAS                     0b010
#define DECAY_MIXED                   0b011
#define DECAY_SLOW_INC_AUTO_MIXED_DEC 0b100
#define DECAY_AUTO_MIXED              0b101

int target_motor1;
int target_motor2;

K_THREAD_DEFINE(stepper_tid, 2048,  stepper_thread, NULL, NULL, NULL, 5, 0, 0);

uint16_t stepper_read_reg(const struct device *spi, const struct spi_config *cfg, uint8_t address) {
    // Read/write bit and register address are the first 4 bits of the first
    // byte; data is in the remaining 4 bits of the first byte combined with
    // the second byte (12 bits total).
    uint8_t tx_buf[2];
    struct spi_buf spi_tx_buf = {
        .buf = tx_buf,
        .len = 2
    };
    struct spi_buf_set spi_tx_buf_set = {
        .buffers = &spi_tx_buf,
        .count = 1
    };


    uint8_t rx_buf[2];
    struct spi_buf spi_rx_buf = {
        .buf = rx_buf,
        .len = 2
    };
    struct spi_buf_set spi_rx_buf_set = {
        .buffers = &spi_rx_buf,
        .count = 1
    };

    tx_buf[0] = (0x8 | (address & 0x7)) << 4;
    // tx_buf[0] = (0x0 | (address & 0x7)) << 4; // invert RW bit
    // tx_buf[1] = (0x8 | (address & 0x7)) << 4;

    int ret = spi_transceive(spi, cfg, &spi_tx_buf_set, &spi_rx_buf_set);
    printk("ret: %d\n", ret);
    uint16_t result = ((rx_buf[0] & 0xF) << 8) + rx_buf[1];
    // printk("read register %d and got %d\n", );
    return result;
}

void stepper_write_reg(const struct device *spi, const struct spi_config *cfg, uint8_t address, uint16_t value) {
    uint8_t tx_buf[2];
    struct spi_buf spi_tx_buf = {
        .buf = tx_buf,
        .len = 2
    };
    struct spi_buf_set spi_tx_buf_set = {
        .buffers = &spi_tx_buf,
        .count = 1
    };

    // address = 0x01;
    // value = 0x01ff;

    // address & 0x7 << 4 = 0x01 << 4 = 0x10
    // value & 0xF00 >> 8 = 0x1 >> 8 = 0x01
    // value & 0xFF = 0xff
    // tx_buf[0] = 0x11
    // tx_buf[1] = 0xff

    tx_buf[0] = ((address & 0x7) << 4) | ((value & 0xF00) >> 8);
    // tx_buf[0] = ((0x8 | (address & 0x7)) << 4) | ((value & 0xF00) >> 8); // invert RW bit
    tx_buf[1] = value & 0xFF;

    // tx_buf[1] = ((address & 0x7) << 4) | ((value & 0xF00) >> 8);
    // tx_buf[0] = value & 0xFF;
    spi_write(spi, cfg, &spi_tx_buf_set);
}


int stepper_init(const struct device *spi, const struct spi_config *cfg) {
    // default settings
    uint16_t ctrl   = 0xC10;
    uint16_t torque = 0x1FF;
    uint16_t off    = 0x030;
    uint16_t blank  = 0x080;
    uint16_t decay  = 0x110;
    uint16_t stall  = 0x040;
    uint16_t drive  = 0xA59;

    stepper_write_reg(spi, cfg, REG_TORQUE, torque);
    stepper_write_reg(spi, cfg, REG_OFF, off);
    stepper_write_reg(spi, cfg, REG_BLANK, blank);
    stepper_write_reg(spi, cfg, REG_DECAY, decay);
    stepper_write_reg(spi, cfg, REG_STALL, stall);
    stepper_write_reg(spi, cfg, REG_DRIVE, drive);
    stepper_write_reg(spi, cfg, REG_CTRL, ctrl);


    if (stepper_read_reg(spi, cfg, REG_TORQUE) != torque) {
        printk("FUCK1\n");
        return -1;
    }
    if (stepper_read_reg(spi, cfg, REG_OFF) != off) {
        printk("FUCK2\n");
        return -1;
    }
    if (stepper_read_reg(spi, cfg, REG_BLANK) != blank) {
        printk("FUCK3\n");
        return -1;
    }
    if (stepper_read_reg(spi, cfg, REG_DECAY) != decay) {
        printk("FUCK4\n");
        return -1;
    }
    if (stepper_read_reg(spi, cfg, REG_STALL) != stall) {
        printk("FUCK5\n");
        return -1;
    }
    if (stepper_read_reg(spi, cfg, REG_DRIVE) != drive) {
        printk("FUCK6\n");
        return -1;
    }
    if (stepper_read_reg(spi, cfg, REG_CTRL) != ctrl) {
        printk("FUCK7\n");
        return -1;
    }



    // current limit
    uint16_t current = 1000; // mA
    uint8_t isgainBits = 0b11;
    uint16_t torqueBits = ((uint32_t)768  * current) / 6875;

    // Halve the gain and TORQUE until the TORQUE value fits in 8 bits.
    while (torqueBits > 0xFF)
    {
      isgainBits--;
      torqueBits >>= 1;
    }

    ctrl = (ctrl & 0b110011111111) | (isgainBits << 8);
    stepper_write_reg(spi, cfg, REG_CTRL, ctrl);
    torque = (torque & 0b111100000000) | torqueBits;
    stepper_write_reg(spi, cfg, REG_TORQUE, torque);



    //microstep
    // Pick 1/4 micro-step by default.
    uint8_t sm = MICROSTEP1;

    ctrl = (ctrl & 0b111110000111) | (sm << 3);

    // enable driver only after config
    ctrl |= 1; // enable bit
    stepper_write_reg(spi, cfg, REG_CTRL, ctrl);


    return 0;
}

void stepper_thread(void *p1, void *p2, void *p3) {
    const struct device *spi = DEVICE_DT_GET(DT_NODELABEL(spi3));

    const struct gpio_dt_spec cs1_gpio = SPI_CS_GPIOS_DT_SPEC_GET(DT_NODELABEL(motor1));
    const struct gpio_dt_spec cs2_gpio = SPI_CS_GPIOS_DT_SPEC_GET(DT_NODELABEL(motor2));
    const struct gpio_dt_spec cs3_gpio = SPI_CS_GPIOS_DT_SPEC_GET(DT_NODELABEL(motor3));
    int ret;
    
    ret = gpio_pin_configure_dt(&cs1_gpio, GPIO_OUTPUT_INACTIVE);
    if (ret < 0) {
        return;
    }

    ret = gpio_pin_configure_dt(&cs2_gpio, GPIO_OUTPUT_INACTIVE);
    if (ret < 0) {
        return;
    }
    ret = gpio_pin_configure_dt(&cs3_gpio, GPIO_OUTPUT_INACTIVE);
    if (ret < 0) {
        return;
    }

    // gpio_pin_set_dt(&cs1_gpio, 1);
    // gpio_pin_set_dt(&cs2_gpio, 1);
    // gpio_pin_set_dt(&cs3_gpio, 1);
    // k_msleep(500);
    // gpio_pin_set_dt(&cs1_gpio, 0);
    // gpio_pin_set_dt(&cs2_gpio, 0);
    // gpio_pin_set_dt(&cs3_gpio, 0);

    if (!device_is_ready(spi)) {
        printk("Device SPI not ready, aborting test");
        return;
    }

    const struct spi_config motor1_cfg = {
        .frequency = 500000,
        .operation = SPI_OP_MODE_MASTER | SPI_TRANSFER_MSB | SPI_WORD_SET(8),
        .cs = SPI_CS_CONTROL_INIT(DT_NODELABEL(motor1), 2)
    };

    const struct spi_config motor2_cfg = {
        .frequency = 500000,
        .operation = SPI_OP_MODE_MASTER | SPI_TRANSFER_MSB | SPI_WORD_SET(8),
        .cs = SPI_CS_CONTROL_INIT(DT_NODELABEL(motor2), 2)
    };

    // const struct spi_config motor2_cfg = {
    //     .frequency = 500000,
    //     .operation = SPI_OP_MODE_MASTER | SPI_TRANSFER_MSB | SPI_WORD_SET(8),
    //     .cs = SPI_CS_CONTROL_INIT(DT_NODELABEL(motor2), 2),
    // };

    int e;

    e |= stepper_init(spi, &motor1_cfg);
    e |= stepper_init(spi, &motor2_cfg);
    if (e) {
        printk("FUGG\n");
    }

    int pulse_length_us = 1000;

    int pulse_every = 2000;

    int motor1_current_pos = 0;
    int motor2_current_pos = 0;

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
        if (motor1_current_pos < target_motor1) {
            gpio_pin_set_dt(&motor1_dir_dt, 1);
            dir1 = 1;
        }
        if (motor1_current_pos > target_motor1) {
            gpio_pin_set_dt(&motor1_dir_dt, 0);
            dir1 = -1;
        }


        if (motor2_current_pos < target_motor2) {
            gpio_pin_set_dt(&motor2_dir_dt, 1);
            dir2 = 1;
        }
        if (motor2_current_pos > target_motor2) {
            gpio_pin_set_dt(&motor2_dir_dt, 0);
            dir2 = -1;
        }

        if (motor1_current_pos != target_motor1) {
            gpio_pin_set_dt(&motor1_step_dt, 1);
        }
        if (motor2_current_pos != target_motor2) {
            gpio_pin_set_dt(&motor2_step_dt, 1);
        }

        k_usleep(pulse_length_us);

        if (motor1_current_pos != target_motor1) {
            gpio_pin_set_dt(&motor1_step_dt, 0);
            motor1_current_pos += dir1;
        }
        if (motor2_current_pos != target_motor2) {
            gpio_pin_set_dt(&motor2_step_dt, 0);
            motor2_current_pos += dir2;
        }
        k_usleep(pulse_every - pulse_length_us);
    }
}