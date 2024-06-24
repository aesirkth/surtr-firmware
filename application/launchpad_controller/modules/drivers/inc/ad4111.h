/*	
 * Generic Subsystem Driver API which can be used for initializing, configuring and programming various peripherals.
 * Specifically made to be used for the AD4111 Analog to Digital Converter (ADC) driver
 *
 *	Author: Love Mitteregger
 *	Created: 10 June 2024
 *
 */

/* Preprocessor directive, if not defined then define... */
#ifndef SUBSYSTEM_DRIVER_API_H
#define SUBSYSTEM_DRIVER_API_H

#include <zephyr/device.h>

/* Typedef declarations, functioning as aliases to their specific function pointer */
typedef int (*subsystem_init_t) (const struct device *dev);
typedef int (*subsystem_reset_t) (const struct device *dev);
typedef int (*subsystem_config_channel_t) (const struct device *dev, int channel, int config);
typedef int (*subsystem_write_register_t) (const struct device *dev, uint8_t reg, uint16_t value);
typedef int (*subsystem_read_register_t) (const struct device *dev, uint8_t reg, uint16_t *value);
typedef int (*subsystem_read_data_t) (const struct device *dev, int channel, int *value);
typedef void (*subsystem_config_irq_t) (const struct device *dev);
typedef void (*subsystem_handle_isr_t) (const struct device *dev);

/* A structure that functions as a device-independent-subsystem-API, 
 * applications will be able to program to this generic API */
struct subsystem_api{
    subsystem_init_t init;                     // Initialize ADC
    subsystem_reset_t reset;                   // Reset ADC
    subsystem_config_channel_t config_channel; // Enable/Disable ADC channel
    subsystem_write_register_t write_register; // Write to ADC register
    subsystem_read_register_t read_register;   // Read from ADC register
    subsystem_read_data_t read_data;           // Read from ADC data register
    subsystem_config_irq_t config_irq;         // Configurate IRQ
    subsystem_handle_isr_t handle_isr;         // Handle ADC interrupt service routine
};

/* Subsystem functions that can be called on by the device via the API */
static inline int subsystem_init(const struct device *dev) {
    struct subsystem_api *api;
    api = (struct subsystem_api *)dev->api;
    return api->init(dev);
}

static inline int subsystem_reset(const struct device *dev) {
    struct subsystem_api *api;
    api = (struct subsystem_api *)dev->api;
    return api->reset(dev);
}

static inline int subsystem_channel(const struct device *dev, int channel, int config) {
    struct subsystem_api *api;
    api = (struct subsystem_api *)dev->api;
    return api->config_channel(dev, channel, config);
}

static inline int subsystem_write_register(const struct device *dev, uint8_t reg, uint16_t value) {
    struct subsystem_api *api;
    api = (struct subsystem_api *)dev->api;
    return api->write_register(dev, reg, value);
}

static inline int subsystem_read_register(const struct device *dev, uint8_t reg, uint16_t *value) {
    struct subsystem_api *api;
    api = (struct subsystem_api *)dev->api;
    return api->read_register(dev, reg, value);
}

static inline int subsystem_read_data(const struct device *dev, int channel, int *value) {
    struct subsystem_api *api;
    api = (struct subsystem_api *)dev->api;
    return api->read_data(dev, channel, value);
}

static inline void subsystem_config_irq(const struct device *dev) {
    struct subsystem_api *api;
    api = (struct subsystem_api *)dev->api;
    api->config_irq(dev);
}
static inline void subsystem_handle_isr(const struct device *dev) {
    struct subsystem_api *api;
    api = (struct subsystem_api *)dev->api;
    api->handle_isr(dev);
}

#endif  // SUBSYSTEM_DRIVER_API_H
