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
typedef int (*ad4111_read_volt_t) (const struct device *dev, int channel);
typedef int (*ad4111_read_current_t) (const struct device *dev, int channel);

/* A structure that functions as a device-independent-adc-API,
 * applications will be able to program to this generic API */
struct ad4111_api{
    ad4111_read_volt_t read_volt;
    ad4111_read_current_t read_current;
};

/* Configuration structure for each ADC instance */
struct adc_config{
    struct spi_dt_spec spi;
    struct gpio_dt_spec cs_gpio;
    uint32_t spi_max_frequency;
};


static inline int ad411_read_volt(const struct device *dev, int channel) {

}

static inline int ad411_read_current(const struct device *dev, int channel) {

}

#endif  // ADC_DRIVER_API_H#ifndef ADC_DRIVER_API_H