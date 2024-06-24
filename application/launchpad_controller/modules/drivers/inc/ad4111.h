/*	
 *	AD4111 Analog to Digital Converter (ADC) Driver
 *
 *	Author: Love Mitteregger
 *	Created: 10 June 2024
 *
 */

// Preprocessor directive, if not defined then define...
#ifndef ADC_DRIVER_API_H
#define ADC_DRIVER_API_H

#include <zephyr/device.h>

/* Typedef declarations functioning as aliases to their specific function pointer */
typedef int (*adc_init_t) (const struct device *dev);
typedef int (*adc_reset_t) (const struct device *dev);
typedef int (*adc_config_channel_t) (const struct device *dev);
typedef int (*adc_write_register_t) (const struct device *dev);
typedef int (*adc_read_register_t) (const struct device *dev);
typedef int (*adc_read_data_t) (const struct device *dev);
typedef void (*adc_config_irq_t) (const struct device *dev);
typedef void (*adc_isr_t) (const struct device *dev);

/* A structure that functions as a device independent subsystem API, applications will be able to program to this generic API */
struct adc_api{
    adc_init_t init;            // Initialize ADC
    adc_reset_t reset;           // Reset ADC
    adc_config_channel_t config_channel;  // Enable/Disable ADC channel
    adc_write_register_t write_register;  // Write to ADC register
    adc_read_register_t read_register;   // Read from ADC register
    adc_read_data_t read_data;       // Read from ADC data register
    adc_isr_t handle_isr;           // Handle ADC interrupt service routine
};

static inline int adc_init(const struct device *dev) {
    struct adc_api *api;

    api = (struct adc_api *)dev->api;
    return api->init(dev)
}

static inline int adc_reset(const struct device *dev) {
    struct adc_api *api;
}
static inline int adc_config_channel(const struct device *dev, int channel, int config) {}
static inline int adc_write_register(const struct device *dev, uint8_t reg, uint16_t value) {}
static inline int adc_read_register(const struct device *dev, uint8_t reg, uint16_t *value) {}
static inline int adc_read_data(const struct device *dev, int channel, int *value) {}
static inline void adc_config_irq(const struct device *dev) {}
static inline void adc_isr_t(const struct device *dev) {}

#endif  // ADC_DRIVER_API_H
