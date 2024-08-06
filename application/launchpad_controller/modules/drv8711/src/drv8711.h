#include <stdint.h>

#define DRV8711_SPI_CS_HOLD_DELAY 2 //us

typedef enum MicrostepResolution {
    MICROSTEP1 = 0b0000,
    MICROSTEP2 = 0b0001,
    MICROSTEP4 = 0b0010,
    MICROSTEP8 = 0b0011,
    MICROSTEP16 = 0b0100,
    MICROSTEP32 = 0b0101,
    MICROSTEP64 = 0b0110,
    MICROSTEP128 = 0b0111,
    MICROSTEP256 = 0b1000
} MicrostepResolution;

typedef enum DecayMode {
    DECAY_SLOW = 0b000,
    DECAY_SLOW_INC_MIXED_DEC = 0b001,
    DECAY_FAS = 0b010,
    DECAY_MIXED = 0b011,
    DECAY_SLOW_INC_AUTO_MIXED_DEC = 0b100,
    DECAY_AUTO_MIXED = 0b101
} DecayMode;

int drv8711_init(const struct device* dev);
// void resetSettingsDrv8711(const struct device* dev);

bool verifySettingsDrv8711(const struct device* dev);
void applyDefaultSettingsDrv8711(const struct device* dev);
void enableDriverDrv8711(const struct device* dev);
void disableDriverDrv8711(const struct device* dev);

void rotateDrv8711(const struct device* dev, int steps, uint8_t direction);

void setStepResolutionDrv8711(const struct device* dev, MicrostepResolution resolution);
void setCurrentMilliamps36v4(const struct device* dev, uint16_t current);
void setDecayModeDrv8711(const struct device* dev, DecayMode decayMode);

// optional, can be implemented later
uint8_t readStatusDrv8711(const struct device* dev);
void clearStatusDrv8711(const struct device* dev);
uint8_t readFaultsDrv8711(const struct device* dev);
void clearFaultsDrv8711(const struct device* dev);
