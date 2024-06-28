#include <zephyr/drivers/spi.h>
#include <zephyr/logging/log.h>

LOG_MODULE_REGISTER(mock_spi);

static int mock_spi_transceive(const struct device *dev,
                               const struct spi_config *config,
                               const struct spi_buf_set *tx_bufs,
                               const struct spi_buf_set *rx_bufs) {
    LOG_INF("Mock SPI transceive called");
    // Simulate data transfer
    if (rx_bufs && rx_bufs->buffers && rx_bufs->buffers->buf) {
        memset(rx_bufs->buffers->buf, 0xAB, rx_bufs->buffers->len);
    }
    return 0;
}

static int mock_spi_release(const struct device *dev, const struct spi_config *config) {
    LOG_INF("Mock SPI release called");
    return 0;
}

static const struct spi_driver_api mock_spi_api = {
    .transceive = mock_spi_transceive,
    .release = mock_spi_release,
};

DEVICE_DEFINE(mock_spi, "mock_spi", NULL, NULL, NULL, NULL,
              POST_KERNEL, CONFIG_KERNEL_INIT_PRIORITY_DEVICE, &mock_spi_api);