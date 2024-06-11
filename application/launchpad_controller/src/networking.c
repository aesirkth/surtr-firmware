#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>


#include <stdio.h>
#include <stdlib.h>
#include <errno.h>



#include <netinet/in.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <unistd.h>


#include "protocol.h"
#include "networking.h"

#define BIND_PORT 1337

LOG_MODULE_REGISTER(networking, CONFIG_APP_LOG_LEVEL);

K_MSGQ_DEFINE(network_msgq, sizeof(struct surtr_message), 64, 4);

void networking_thread(void *p1, void *p2, void *p3) {
    LOG_INF("Hello networking!");

    int opt;
	socklen_t optlen = sizeof(int);
	int serv, ret;
	struct sockaddr_in6 bind_addr = {
		.sin6_family = AF_INET6,
		.sin6_addr = IN6ADDR_ANY_INIT,
		.sin6_port = htons(BIND_PORT),
	};
	static int counter;

	serv = socket(AF_INET6, SOCK_STREAM, IPPROTO_TCP);
	if (serv < 0) {
		LOG_ERR("error: socket: %d\n", errno);
		exit(1);
	}

	ret = getsockopt(serv, IPPROTO_IPV6, IPV6_V6ONLY, &opt, &optlen);
	if (ret == 0) {
		if (opt) {
			LOG_INF("IPV6_V6ONLY option is on, turning it off.\n");

			opt = 0;
			ret = setsockopt(serv, IPPROTO_IPV6, IPV6_V6ONLY,
					 &opt, optlen);
			if (ret < 0) {
				LOG_WRN("Cannot turn off IPV6_V6ONLY option\n");
			} else {
				LOG_INF("Sharing same socket between IPv6 and IPv4\n");
			}
		}
	}

	if (bind(serv, (struct sockaddr *)&bind_addr, sizeof(bind_addr)) < 0) {
		LOG_ERR("error: bind: %d\n", errno);
		exit(1);
	}

	if (listen(serv, 5) < 0) {
		LOG_ERR("error: listen: %d\n", errno);
		exit(1);
	}

	LOG_INF("Single-threaded TCP echo server waits for a connection on "
	       "port %d...\n", BIND_PORT);


    while(true) {
        struct surtr_message msg;
		int ret = k_msgq_get(&network_msgq, &msg, K_FOREVER);
        if (ret == 0) {
            //do stuff with msg
        }
    }
}