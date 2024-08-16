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

void networking_thread(void *p1, void *p2, void *p3);



K_MSGQ_DEFINE(network_msgq, sizeof(struct surtr_message), 64, 4);

K_THREAD_DEFINE(networking_tid, 4096, networking_thread, NULL, NULL, NULL, 5, 0, 0);

void init_networking(void *p1, void *p2, void *p3) {

}

void networking_thread(void *p1, void *p2, void *p3) {
    LOG_INF("Hello networking!");

	int serv, ret;
	struct sockaddr_in bind_addr = {
		.sin_family = AF_INET,
		.sin_addr = { .s_addr = htonl(INADDR_ANY) },
		.sin_port = htons(BIND_PORT),
	};

	serv = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
	if (serv < 0) {
		LOG_ERR("error: socket: %d\n", errno);
		exit(1);
	}

	if (bind(serv, (struct sockaddr *)&bind_addr, sizeof(bind_addr)) < 0) {
		LOG_ERR("error: bind: %d\n", errno);
		exit(1);
	}

	if (listen(serv, 5) < 0) {
		LOG_ERR("error: listen: %d\n", errno);
		exit(1);
	}

	LOG_INF("Waiting for connection on port %d...\n", BIND_PORT);

    while(true) {
        struct sockaddr_in client_addr;
        socklen_t client_addr_len = sizeof(client_addr);
        char addr_str[32];

        int client = accept(serv, (struct sockaddr *)&client_addr,
                    &client_addr_len);
        if (client < 0) {
            printk("Error in accept: %d - continuing\n", errno);
            k_msleep(100);
            continue;
        }
        inet_ntop(client_addr.sin_family, &client_addr.sin_addr,
            addr_str, sizeof(addr_str));
        printk("Connection from %s\n", addr_str);

        while (1) {
			ssize_t r;
			char c;

			r = recv(client, &c, 1, 0);
			if (r < 0) {
				if (errno == EAGAIN || errno == EINTR) {
					continue;
				}

				printk("Got error %d when receiving from "
					"socket\n", errno);
				goto close_client;
			}
		}

		close_client:
		ret = close(client);
		if (ret == 0) {
			printk("Connection from %s closed\n", addr_str);
		} else {
			printk("Got error %d while closing the "
			       "socket\n", errno);

		}
	}
}