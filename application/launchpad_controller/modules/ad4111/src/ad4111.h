/*	
 * ADC Subsystem Driver API which can be used for initializing, configuring and programming various peripherals.
 * Specifically made to be used for the AD4111 Analog to Digital Converter (ADC) driver
 *
 *	Author: Love Mitteregger
 *	Created: 10 June 2024
 *
 */

/* Preprocessor directive, if not defined then define... */
/*	
 * ADC Subsystem Driver API which can be used for initializing, configuring and programming various peripherals.
 * Specifically made to be used for the AD4111 Analog to Digital Converter (ADC) driver
 *
 *	Author: Love Mitteregger
 *	Created: 10 June 2024
 *
 */

/* Preprocessor directive, if not defined then define... */
#ifndef ADC_DRIVER_API_H
#define ADC_DRIVER_API_H
#define DT_DRV_COMPAT analog_ad4111 

#include <zephyr/device.h>
#include <zephyr/drivers/spi.h>

/* Typedef declarations, functioning as aliases to their specific function pointer */
typedef int (*adc_init_t) (const struct device *dev);
typedef int (*adc_reset_t) (const struct device *dev);
typedef int (*adc_config_channel_t) (const struct device *dev, int channel, int config);
typedef int (*adc_write_register_t) (const struct device *dev, uint8_t reg, uint16_t value);
typedef int (*adc_read_register_t) (const struct device *dev, uint8_t reg, uint16_t *value);
typedef int (*adc_read_data_t) (const struct device *dev, int channel, int *value);

/* A structure that functions as a device-independent-adc-API, 
 * applications will be able to program to this generic API */
struct adc_api{
    adc_init_t init;                     // Initialize ADC
    adc_reset_t reset;                   // Reset ADC
    adc_config_channel_t config_channel; // Enable/Disable ADC channel
    adc_write_register_t write_register; // Write to ADC register
    adc_read_register_t read_register;   // Read from ADC register
    adc_read_data_t read_data;           // Read from ADC data register
};

/* Configuration structure for each ADC instance */
struct adc_config{
    struct spi_dt_spec spi;
    struct gpio_dt_spec cs_gpio;
    uint32_t spi_max_frequency;
    uint8_t channels;
};

/* Subsystem functions that can be called on by the device via the API */
static inline int adc_init(const struct device *dev) {
    struct adc_api *api;
    api = (struct adc_api *)dev->api;
    return api->init(dev);
}

static inline int adc_reset(const struct device *dev) {
    struct adc_api *api;
    api = (struct adc_api *)dev->api;
    return api->reset(dev);
}

static inline int adc_channel(const struct device *dev, int channel, int config) {
    struct adc_api *api;
    api = (struct adc_api *)dev->api;
    return api->config_channel(dev, channel, config);
}

static inline int adc_write_register(const struct device *dev, uint8_t reg, uint16_t value) {
    struct adc_api *api;
    api = (struct adc_api *)dev->api;
    return api->write_register(dev, reg, value);
}

static inline int adc_read_register(const struct device *dev, uint8_t reg, uint16_t *value) {
    struct adc_api *api;
    api = (struct adc_api *)dev->api;
    return api->read_register(dev, reg, value);
}

static inline int adc_read_data(const struct device *dev, int channel, int *value) {
    struct adc_api *api;
    api = (struct adc_api *)dev->api;
    return api->read_data(dev, channel, value);
}

#endif  // ADC_DRIVER_API_H#ifndef ADC_DRIVER_API_H