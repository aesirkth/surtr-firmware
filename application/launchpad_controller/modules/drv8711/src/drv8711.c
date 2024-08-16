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

#define DT_DRV_COMPAT ti_drv8711

#include <zephyr/drivers/spi.h>
#include <zephyr/input/input.h>
#include <zephyr/kernel.h>

#include <zephyr/logging/log.h>
#include "drv8711.h"
LOG_MODULE_REGISTER(drv8711);

struct drv8711_data {
    uint16_t currentLimitMa;
    uint16_t ctrl;
    uint16_t torque;
    uint16_t off;
    uint16_t blank;
    uint16_t decay;
    uint16_t stall;
    uint16_t drive;
};

struct drv8711_config {
    struct spi_dt_spec spi;
    struct gpio_dt_spec cs_gpio;
    uint32_t spi_max_frequency;
};

// TODO: think about casting address enum to uint8_t
void drv8711_write_reg(const struct device* dev, Drv8711Reg address, uint16_t value) {
    const struct drv8711_config* config = dev->config;
    const struct drv8711_data* data = dev->data;

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
    spi_write_dt(&drv8711_spi_dt_spec, &spi_tx_buf_set);
}

uint16_t drv8711_read_reg(const struct device* dev, Drv8711Reg address) {
    const struct drv8711_config* config = dev->config;
    const struct drv8711_data* data = dev->data;

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
    return result;
}


void applyDefaultSettingsDrv8711(const struct device* dev) {
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

    drv8711_write_reg(dev, CTRL, ctrl);
    drv8711_write_reg(dev, TORQUE, torque);
    drv8711_write_reg(dev, OFF, off);
    drv8711_write_reg(dev, BLANK, blank);
    drv8711_write_reg(dev, DECAY, decay);
    drv8711_write_reg(dev, STALL, stall);
    drv8711_write_reg(dev, DRIVE, drive);

    struct drv8711_data* data = dev->data;
    data->ctrl = ctrl;
    data->torque = torque;
    data->off = off;
    data->blank = blank;
    data->decay = decay;
    data->stall = stall;
    data->drive = drive;
}

// return false if the registers on DRV8711 don't match what's currently in RAM
bool verifySettingsDrv8711(const struct device* dev) {
    const struct drv8711_data* data = dev->data;
    uint16_t ctrl = drv8711_read_reg(dev, CTRL);
    uint16_t torque = drv8711_read_reg(dev, TORQUE);
    uint16_t off = drv8711_read_reg(dev, OFF);
    uint16_t blank = drv8711_read_reg(dev, BLANK);
    uint16_t decay = drv8711_read_reg(dev, DECAY);
    uint16_t stall = drv8711_read_reg(dev, STALL);
    uint16_t drive = drv8711_read_reg(dev, DRIVE);

    return (
        (ctrl == data->ctrl) &&
        (torque == data->torque) &&
        (off == data->off) &&
        (blank == data->blank) &&
        (decay == data->decay) &&
        (stall == data->stall) &&
        (drive == data->drive)
    );
}

void enableDriverDrv8711(const struct device* dev) {
    struct drv8711_data* data = dev->data;
    uint16_t ctrl = data->ctrl;
    ctrl |= 1; // enable bit
    drv8711_write_reg(dev, CTRL, ctrl);
}

void disableDriverDrv8711(const struct device* dev) {
    struct drv8711_data* data = dev->data;
    uint16_t ctrl = data->ctrl;
    ctrl &= (~0x0001); // enable bit
    drv8711_write_reg(dev, CTRL, ctrl);
}

void rotateDrv8711(const struct device* dev, int steps, uint8_t direction) {
    // TODO: Figure out how to get the STEP and DIR pins in the device tree,
    // then we can just stick em in the config struct
}

void setStepResolutionDrv8711(const struct device* dev, MicrostepResolution resolution) {
    struct drv8711_data* data = dev->data;
    uint16_t ctrl = data->ctrl;
    ctrl = (ctrl & 0xff87) | ((resolution & 0x0f) << 3);
    drv8711_write_reg(dev, CTRL, ctrl);
    data->ctrl = ctrl;
}

void setCurrentMilliamps36v4(const struct device* dev, uint16_t current) {
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
    drv8711_write_reg(dev, CTRL, ctrl);
    torque = (torque & 0b111100000000) | torqueBits;
    drv8711_write_reg(dev, TORQUE, torque);

    data->ctrl = ctrl;
    data->torque = torque;
    data->currentLimitMa = current;
}

void setDecayModeDrv8711(const struct device* dev, DecayMode decayMode) {
    struct drv8711_data* data = dev->data;
    uint16_t decay = data->decay;

    decay &= 0xf8ff; // clear bits 10=8
    decay |= ((decayMode & 0b111) << 8);
    drv8711_write_reg(dev, DECAY, decay);
    data->decay = decay;
}

// TODO: consider adding maxCurrentMilliamp to the data struct
// CONFIG_APPLICATION_INIT_PRIORITY is 90 in autoconf.h
#define DRV8711_DEVICE_DEFINE(inst)                                             \
    static struct drv8711_data drv8711_data_##inst;                             \
    drv8711_data_##inst.currentLimitMa = DT_INST_PROP(inst, current_limit_ma);  \
    static struct drv8711_config drv8711_config_##inst = {                      \
        .spi = SPI_DT_SPEC_INST_GET(                                            \
            inst,                                                               \
            SPI_OP_MODE_MASTER | SPI_TRANSFER_MSB | SPI_WORD_SET(8),            \
            DRV8711_SPI_CS_HOLD_DELAY                                           \
        ),                                                                      \
        .cs_gpio = SPI_CS_GPIOS_DT_SPEC_INST_GET(inst),                         \
        .spi_max_frequency = DT_INST_PROP(inst, spi_max_frequency),             \
    };                                                                          \
    DEVICE_DT_INST_DEFINE(inst,                                                 \
        drv8711_init,                                                           \
        NULL,                                                                   \
        drv8711_data_##inst,                                                    \
        drv8711_config_##inst,                                                  \
        POST_KERNEL, CONFIG_APPLICATION_INIT_PRIORITY,                          \
        &drv8711_driver_api                                                     \
        );


DT_INST_FOREACH_STATUS_OKAY(DRV8711_DEVICE_DEFINE)
