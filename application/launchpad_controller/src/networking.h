#pragma once

#include <zephyr/kernel.h>

#include "networking.h"
#include "protocol.h"


void init_networking(void *p1, void *p2, void *p3);

void send_msg(surtrpb_SurtrMessage *msg);