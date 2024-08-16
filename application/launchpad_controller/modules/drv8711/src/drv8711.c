#define DT_DRV_COMPAT ti_drv8711

#include <zephyr/drivers/spi.h>
#include <zephyr/input/input.h>
#include <zephyr/kernel.h>

#include <zephyr/logging/log.h>

#include "drv8711.h"

LOG_MODULE_REGISTER(drv8711);

typedef enum drv8711_reg {
    CTRL = 0x00,
    TORQUE = 0x01,
    OFF = 0x02,
    BLANK = 0x03,
    DECAY = 0x04,
    STALL = 0x05,
    DRIVE = 0x06,
    STATUS = 0x07
} Drv8711Reg;

typedef enum {
    DECAY_SLOW = 0b000,
    DECAY_SLOW_INC_MIXED_DEC = 0b001,
    DECAY_FAS = 0b010,
    DECAY_MIXED = 0b011,
    DECAY_SLOW_INC_AUTO_MIXED_DEC = 0b100,
    DECAY_AUTO_MIXED = 0b101
} Drv8711DecayMode_t;

struct drv8711_data {
    uint16_t ctrl;
    uint16_t torque;
    uint16_t off;
    uint16_t blank;
    uint16_t decay;
    uint16_t stall;
    uint16_t drive;
};

int drv8711_driver_init(const struct device* dev);
int drv8711_driver_enable(const struct device* dev, bool enabled);

int drv8711_driver_verify_settings(const struct device* dev, bool *result);
int drv8711_driver_apply_default_settings(const struct device* dev);

int drv8711_driver_set_microstep(const struct device* dev, Drv8711MicrostepResolution_t resolution);
int drv8711_driver_set_current_limit(const struct device* dev, uint16_t current);
int drv8711_driver_set_decay_mode(const struct device* dev, Drv8711DecayMode_t decayMode);

struct drv8711_config {
    struct spi_dt_spec spi;
    struct gpio_dt_spec cs_gpio;
    uint32_t spi_max_frequency;
};

// TODO: think about casting address enum to uint8_t
int drv8711_driver_write_reg(const struct device* dev, Drv8711Reg address, uint16_t value) {
    const struct drv8711_config* config = dev->config;
    // const struct drv8711_data* data = dev->data;

    const struct spi_dt_spec drv8711_spi_dt_spec = config->spi;
    // const struct device* spi = drv8711_spi_dt_spec.bus;
    // const struct spi_config* cfg = &(drv8711_spi_dt_spec.config);

    uint8_t tx_buf[2];
    struct spi_buf spi_tx_buf = {
        .buf = tx_buf,
        .len = 2
    };
    struct spi_buf_set spi_tx_buf_set = {
        .buffers = &spi_tx_buf,
        .count = 1
    };

    tx_buf[0] = ((address & 0x7) << 4) | ((value & 0xF00) >> 8);
    tx_buf[1] = value & 0xFF;

    // spi_write(spi, cfg, &spi_tx_buf_set);
    return spi_write_dt(&drv8711_spi_dt_spec, &spi_tx_buf_set);
}

int drv8711_driver_read_reg(const struct device* dev, Drv8711Reg address, uint16_t *value) {
    const struct drv8711_config* config = dev->config;
    // const struct drv8711_data* data = dev->data;

    const struct spi_dt_spec drv8711_spi_dt_spec = config->spi;
    // const struct device* spi = drv8711_spi_dt_spec.bus;
    // const struct spi_config* cfg = &(drv8711_spi_dt_spec.config);

    // uint8_t address

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

    // int ret = spi_transceive(spi, cfg, &spi_tx_buf_set, &spi_rx_buf_set);
    int ret = spi_transceive_dt(&drv8711_spi_dt_spec, &spi_tx_buf_set, &spi_rx_buf_set);
    uint16_t result = ((rx_buf[0] & 0xF) << 8) + rx_buf[1];
    *value = result;
    return ret;
}


int drv8711_driver_init(const struct device* dev) {
    int ret = drv8711_driver_apply_default_settings(dev);
    drv8711_driver_set_current_limit(dev, 3000); // 3A
    return ret;
}

int drv8711_driver_apply_default_settings(const struct device* dev) {
    // TODO: either hardcode better values (with e.g. current limts)
    // or read from the device tree
    // or maybe not since these are the actual device boot default values
    uint16_t ctrl   = 0xC10;
    uint16_t torque = 0x1FF;
    uint16_t off    = 0x030;
    uint16_t blank  = 0x080;
    uint16_t decay  = 0x110;
    uint16_t stall  = 0x040;
    uint16_t drive  = 0xA59;

    drv8711_driver_write_reg(dev, CTRL, ctrl);
    drv8711_driver_write_reg(dev, TORQUE, torque);
    drv8711_driver_write_reg(dev, OFF, off);
    drv8711_driver_write_reg(dev, BLANK, blank);
    drv8711_driver_write_reg(dev, DECAY, decay);
    drv8711_driver_write_reg(dev, STALL, stall);
    int e = drv8711_driver_write_reg(dev, DRIVE, drive);

    struct drv8711_data* data = dev->data;
    data->ctrl = ctrl;
    data->torque = torque;
    data->off = off;
    data->blank = blank;
    data->decay = decay;
    data->stall = stall;
    data->drive = drive;

    return e;
}

// return false if the registers on DRV8711 don't match what's currently in RAM
int drv8711_driver_verify_settings(const struct device* dev, bool *result) {
    const struct drv8711_data* data = dev->data;

    uint16_t ctrl;
    uint16_t torque;
    uint16_t off;
    uint16_t blank;
    uint16_t decay;
    uint16_t stall;
    uint16_t drive;

    drv8711_driver_read_reg(dev, CTRL, &ctrl);
    drv8711_driver_read_reg(dev, TORQUE, &torque);
    drv8711_driver_read_reg(dev, OFF, &off);
    drv8711_driver_read_reg(dev, BLANK, &blank);
    drv8711_driver_read_reg(dev, DECAY, &decay);
    drv8711_driver_read_reg(dev, STALL, &stall);
    int e = drv8711_driver_read_reg(dev, DRIVE, &drive);

    *result = (
        (ctrl == data->ctrl) &&
        (torque == data->torque) &&
        (off == data->off) &&
        (blank == data->blank) &&
        (decay == data->decay) &&
        (stall == data->stall) &&
        (drive == data->drive)
    );

    return e;
}

int drv8711_driver_enable(const struct device* dev, bool enabled) {
    struct drv8711_data* data = dev->data;
    uint16_t ctrl = data->ctrl;
    int e;
    if (enabled) {
        ctrl |= 1; // enable bit
        e = drv8711_driver_write_reg(dev, CTRL, ctrl);
    } else {
        ctrl &= (~0x0001); // enable bit
        e = drv8711_driver_write_reg(dev, CTRL, ctrl);
    }
    return e;
}

int drv8711_driver_set_microstep(const struct device* dev, Drv8711MicrostepResolution_t resolution) {
    struct drv8711_data* data = dev->data;
    uint16_t ctrl = data->ctrl;
    ctrl = (ctrl & 0xff87) | ((resolution & 0x0f) << 3);
    int e = drv8711_driver_write_reg(dev, CTRL, ctrl);
    data->ctrl = ctrl;
    return e;
}

int drv8711_driver_set_current_limit(const struct device* dev, uint16_t current) {
    struct drv8711_data* data = dev->data;
    uint16_t ctrl = data->ctrl;
    uint16_t torque = data->torque;

    // TODO: Figure out if this is the best way to avoid overwriting the ctrl and torque registers
    // uint16_t ctrl = drv8711_read_reg(dev, CTRL);
    // uint16_t torque = drv8711_read_reg(dev, CTRL);

    // spi = dev->config;
    // current limit
    // uint16_t current = 1000; // mA
    uint8_t isgainBits = 0b11;
    uint16_t torqueBits = ((uint32_t)768  * current) / 6875;

    // Halve the gain and TORQUE until the TORQUE value fits in 8 bits.
    while (torqueBits > 0xFF)
    {
      isgainBits--;
      torqueBits >>= 1;
    }

    // uint16_t ctrl, torque;
    ctrl = (ctrl & 0b110011111111) | (isgainBits << 8);
    drv8711_driver_write_reg(dev, CTRL, ctrl);
    torque = (torque & 0b111100000000) | torqueBits;
    int e = drv8711_driver_write_reg(dev, TORQUE, torque);

    data->ctrl = ctrl;
    data->torque = torque;
    return e;
}

int drv8711_driver_set_decay_mode(const struct device* dev, Drv8711DecayMode_t decayMode) {
    struct drv8711_data* data = dev->data;
    uint16_t decay = data->decay;

    decay &= 0xf8ff; // clear bits 10=8
    decay |= ((decayMode & 0b111) << 8);
    int e = drv8711_driver_write_reg(dev, DECAY, decay);
    data->decay = decay;

    return e;
}



struct drv8711_driver_api drv8711_api = {
    .set_current_limit = drv8711_driver_set_current_limit,
    .set_microstep = drv8711_driver_set_microstep,
    .enable = drv8711_driver_enable
};

#define DRV8711_SPI_CS_HOLD_DELAY 2 //us

// CONFIG_APPLICATION_INIT_PRIORITY is 90 in autoconf.h
#define DRV8711_DEVICE_DEFINE(inst)                                             \
    static struct drv8711_data drv8711_data_##inst;                             \
    static struct drv8711_config drv8711_config_##inst = {                      \
        .spi = SPI_DT_SPEC_INST_GET(                                            \
            inst,                                                               \
            SPI_OP_MODE_MASTER | SPI_TRANSFER_MSB | SPI_WORD_SET(8),            \
            DRV8711_SPI_CS_HOLD_DELAY                                           \
        ),                                                                      \
        .cs_gpio = SPI_CS_GPIOS_DT_SPEC_INST_GET(inst),                         \
        .spi_max_frequency = DT_INST_PROP(inst, spi_max_frequency),             \
    };                                                                          \
                                                                                \
    DEVICE_DT_INST_DEFINE(                                                      \
        inst,                                                                   \
        drv8711_driver_init,                                                           \
        NULL,                                                                   \
        &drv8711_data_##inst,                                                   \
        &drv8711_config_##inst,                                                 \
        POST_KERNEL,                                                            \
        CONFIG_APPLICATION_INIT_PRIORITY,                                       \
        &drv8711_api                                                            \
        );


DT_INST_FOREACH_STATUS_OKAY(DRV8711_DEVICE_DEFINE)