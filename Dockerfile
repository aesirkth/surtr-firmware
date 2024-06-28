FROM ubuntu:22.04

# Install dependencies
RUN apt-get update && apt-get install -y \
    git \
    cmake \
    ninja-build \
    gperf \
    dfu-util \
    python3-pip \
    python3-setuptools \
    python3-tk \
    python3-wheel \
    xz-utils \
    file \
    make \
    gcc \
    g++ \
    libc-dev \
    libc++-dev \
    g++-multilib \
    libsdl2-dev \
    wget \
    unzip \
    locales \
    sudo \
    udev \
    xz-utils

# Install Zephyr SDK
RUN wget https://github.com/zephyrproject-rtos/sdk-ng/releases/download/v0.16.0/zephyr-sdk-0.16.0-x86_64-linux-setup.run \
    && chmod +x zephyr-sdk-0.16.0-x86_64-linux-setup.run \
    && ./zephyr-sdk-0.16.0-x86_64-linux-setup.run -- -y

# Set up environment variables
ENV ZEPHYR_TOOLCHAIN_VARIANT=zephyr
ENV ZEPHYR_SDK_INSTALL_DIR=/opt/zephyr-sdk

# Install West
RUN pip3 install west

# Set up Zephyr Project
RUN git clone https://github.com/zephyrproject-rtos/zephyr.git /zephyrproject/zephyr \
    && pip3 install -r /zephyrproject/zephyr/scripts/requirements.txt \
    && west init -l /zephyrproject/zephyr \
    && west update

WORKDIR /workdir

CMD ["/bin/bash"]

