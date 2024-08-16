#include <stdint.h>
#include <zephyr/device.h>

typedef enum {
    MICROSTEP1 = 0b0000,
    MICROSTEP2 = 0b0001,
    MICROSTEP4 = 0b0010,
    MICROSTEP8 = 0b0011,
    MICROSTEP16 = 0b0100,
    MICROSTEP32 = 0b0101,
    MICROSTEP64 = 0b0110,
    MICROSTEP128 = 0b0111,
    MICROSTEP256 = 0b1000
} Drv8711MicrostepResolution_t;

typedef int (*drv8711_set_current_limit_t) (const struct device *dev, uint16_t current_ma);
typedef int (*drv8711_set_microstep_t) (const struct device *dev, Drv8711MicrostepResolution_t resolution);
typedef int (*drv8711_enable_t) (const struct device *dev, bool enable);

struct drv8711_driver_api {
    drv8711_set_current_limit_t set_current_limit;
    drv8711_set_microstep_t set_microstep;
    drv8711_enable_t enable;
};

static inline int drv8711_set_current_limit(const struct device *dev, uint16_t current_ma) {
    const struct drv8711_driver_api *api =
    (const struct drv8711_driver_api *)dev->api;

    return api->set_current_limit(dev, current_ma);
}

static inline int drv8711_set_microstep(const struct device *dev, Drv8711MicrostepResolution_t resolution) {
    const struct drv8711_driver_api *api =
    (const struct drv8711_driver_api *)dev->api;

    return api->set_microstep(dev, resolution);
}

static inline int drv8711_enable(const struct device *dev, bool enable) {
    const struct drv8711_driver_api *api =
    (const struct drv8711_driver_api *)dev->api;

    return api->enable(dev, enable);
}