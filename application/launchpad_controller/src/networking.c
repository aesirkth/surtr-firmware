#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>


#include <stdio.h>
#include <stdlib.h>
#include <errno.h>



#include <zephyr/net/net_if.h>
#include <zephyr/net/net_core.h>
#include <zephyr/net/net_context.h>
#include <zephyr/net/net_mgmt.h>

#include <netinet/in.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <unistd.h>


#include "protocol.h"
#include "networking.h"

#define BIND_PORT 1337

LOG_MODULE_REGISTER(networking, CONFIG_APP_LOG_LEVEL);

void networking_thread(void *p1, void *p2, void *p3);
void sender_thread(void *p1, void *p2, void *p3);


K_MSGQ_DEFINE(network_msgq, sizeof(surtrpb_SurtrMessage), 64, 4);

K_THREAD_DEFINE(networking_tid, 4096, networking_thread, NULL, NULL, NULL, 5, 0, 1000);
K_THREAD_DEFINE(sender_tid, 4096, sender_thread, NULL, NULL, NULL, 5, 0, 1000);

#define DHCP_OPTION_NTP (42)

int volatile client_socket = -1;

static uint8_t ntp_server[4];

static struct net_mgmt_event_callback mgmt_cb;

static struct net_dhcpv4_option_callback dhcp_cb;

static void handler(struct net_mgmt_event_callback *cb,
		    uint32_t mgmt_event,
		    struct net_if *iface)
{
	int i = 0;

	if (mgmt_event != NET_EVENT_IPV4_ADDR_ADD) {
		return;
	}

	for (i = 0; i < NET_IF_MAX_IPV4_ADDR; i++) {
		char buf[NET_IPV4_ADDR_LEN];

		if (iface->config.ip.ipv4->unicast[i].ipv4.addr_type !=
							NET_ADDR_DHCP) {
			continue;
		}

		LOG_INF("   Address[%d]: %s", net_if_get_by_iface(iface),
			net_addr_ntop(AF_INET,
			    &iface->config.ip.ipv4->unicast[i].ipv4.address.in_addr,
						  buf, sizeof(buf)));
		LOG_INF("    Subnet[%d]: %s", net_if_get_by_iface(iface),
			net_addr_ntop(AF_INET,
				       &iface->config.ip.ipv4->unicast[i].netmask,
				       buf, sizeof(buf)));
		LOG_INF("    Router[%d]: %s", net_if_get_by_iface(iface),
			net_addr_ntop(AF_INET,
						 &iface->config.ip.ipv4->gw,
						 buf, sizeof(buf)));
		LOG_INF("Lease time[%d]: %u seconds", net_if_get_by_iface(iface),
			iface->config.dhcpv4.lease_time);
	}
}

static void option_handler(struct net_dhcpv4_option_callback *cb,
			   size_t length,
			   enum net_dhcpv4_msg_type msg_type,
			   struct net_if *iface)
{
	char buf[NET_IPV4_ADDR_LEN];

	LOG_INF("DHCP Option %d: %s", cb->option,
		net_addr_ntop(AF_INET, cb->data, buf, sizeof(buf)));
}



static void start_dhcpv4_client(struct net_if *iface, void *user_data)
{
	ARG_UNUSED(user_data);

	LOG_INF("Start on %s: index=%d", net_if_get_device(iface)->name,
		net_if_get_by_iface(iface));
	net_dhcpv4_start(iface);
}

void init_networking(void *p1, void *p2, void *p3) {
	LOG_INF("init networking");
	net_mgmt_init_event_callback(&mgmt_cb, handler,
				     NET_EVENT_IPV4_ADDR_ADD);
	net_mgmt_add_event_callback(&mgmt_cb);

	net_dhcpv4_init_option_callback(&dhcp_cb, option_handler,
					DHCP_OPTION_NTP, ntp_server,
					sizeof(ntp_server));

	int e = net_dhcpv4_add_option_callback(&dhcp_cb);
	if (e) {
		LOG_ERR("add option failed with %d", e);
	}
	net_if_foreach(start_dhcpv4_client, NULL);
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
		return;
	}

	if (bind(serv, (struct sockaddr *)&bind_addr, sizeof(bind_addr)) < 0) {
		LOG_ERR("error: bind: %d\n", errno);
		return;
	}

	if (listen(serv, 5) < 0) {
		LOG_ERR("error: listen: %d\n", errno);
		return;
	}

	LOG_INF("Waiting for connection on port %d...", BIND_PORT);

    while(true) {
        struct sockaddr_in client_addr;
        socklen_t client_addr_len = sizeof(client_addr);
        char addr_str[32];

        client_socket = accept(serv, (struct sockaddr *)&client_addr,
                    &client_addr_len);
        if (client_socket < 0) {
            LOG_ERR("Error in accept: %d - continuing", errno);
            k_msleep(100);
            continue;
        }
        inet_ntop(client_addr.sin_family, &client_addr.sin_addr,
            addr_str, sizeof(addr_str));
        LOG_INF("Connection from %s", addr_str);

		struct protocol_state protocol_state;
		reset_protocol_state(&protocol_state);
        while (1) {
			ssize_t r;
			uint8_t rx_buf[1024];

			r = recv(client_socket, rx_buf, sizeof(rx_buf), 0);
			LOG_DBG("recv returned %d", r);
			if (r < 0) {
				if (errno == EAGAIN || errno == EINTR) {
					continue;
				}

				LOG_WRN("Got error %d when receiving from socket", errno);
				goto close_client;
			}

			for (int i = 0; i < r; i++) {
				surtrpb_SurtrMessage msg;
				int ret = parse_protocol_message(&protocol_state, rx_buf[i], &msg);
				if (ret < 0) {
					LOG_WRN("Got invalid byte");
					reset_protocol_state(&protocol_state);
				}
				if (ret > 0) {
					LOG_INF("received msg");
					handle_message(&msg);
					reset_protocol_state(&protocol_state);
				}
			}
		}

		close_client:
		ret = close(client_socket);
		client_socket = -1;
		if (ret == 0) {
			LOG_INF("Connection from %s closed\n", addr_str);
		} else {
			LOG_ERR("Got error %d while closing the "
			       "socket\n", errno);

		}
	}
}

void sender_thread(void *p1, void *p2, void *p3) {
	while (true) {
		surtrpb_SurtrMessage msg;
		int ret = k_msgq_get(&network_msgq, &msg, K_FOREVER);
		if (ret == 0) {
			if (client_socket == -1) {
				continue;
			}
			LOG_DBG("Sending msg");
			uint8_t tx_buf[PROTOCOL_BUFFER_LENGTH];
			int len = encode_surtr_message(&msg, tx_buf);
			int sent = 0;
			while (sent < len) {
				ret = send(client_socket, tx_buf + sent, len - sent, 0);
				if (ret <= 0) {
					break;
				}
				sent += ret;
			}
		}
	}
}

void send_msg(surtrpb_SurtrMessage *msg) {
	int ret = k_msgq_put(&network_msgq, msg, K_NO_WAIT);
	if (ret) {
		LOG_WRN("Couldn't put message (code %d)", ret);
	}
}