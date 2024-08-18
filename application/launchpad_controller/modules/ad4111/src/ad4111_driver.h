#include "ad4111.h"
#include "no_os/ad717x.h"


/* Data struct used to hold instance-specific data that may change at runtime.
 * Each instance of the AD4111 driver will have its own ad4111_data structure,
 * allowing independent operation of multiple instances. */
struct ad4111_config {
    struct spi_dt_spec spi; // This structure holds the SPI configuration for the AD4111 instance. It includes details like the SPI bus, chip select, and maximum frequency. The SPI_DT_SPEC_INST_GET(inst) macro in the AD4111_DEVICE_DEFINE macro fills this structure based on device tree settings.
    struct gpio_dt_spec cs_gpio;
    uint32_t spi_max_frequency;
    uint8_t channels;
};

struct ad4111_data {
    ad717x_dev ad717x;
};