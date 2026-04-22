#ifndef SERVER_H
#define SERVER_H

#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include <zephyr/drivers/uart.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <unistd.h>
#include "packet.h"
#include "circbuf.h"

#define IPV4 AF_INET
#define TCP SOCK_STREAM
#define IP 		0
#define PORT 	80
#define BACKLOG 8

struct Client {

    struct sockaddr_in address;
    int socket;

};

struct Server {
	
	int domain;
	int service;
	int protocol;
	unsigned long interface;
	int port;
	int backlog;

	struct sockaddr_in address;

	int socket;

};

/* Write Message Queue declared in main. */
extern struct k_msgq request_msgq;

/**
 * ==========================================================
 * accept_connection():
 *  	Client is initialized here by being assign sockaddr_in address
 *  	and int socket.
 */
int accept_connection(struct Server *server, struct Client *client);

/**
 * ==========================================================
 * ethernet_handle_request():
 *      Blocking read on recv() until a request has been received.
 *      Retrieve payload out of packet received.
 *      Place payload data on the request Queue.
 */
int ethernet_handle_request(struct Client *client);

/**
 * ==========================================================
 * ethernet_send_message():
 *     Tries to send message until entire TX_BUFFER has been passed.
 */
int ethernet_send_message(struct Client *client, uint8_t *tx_buffer, const uint8_t tx_size);

/**
 * ==========================================================
 * server_constructor():
 *      Initializes a server struct.
 *      DOMAIN IPV4
 *      SERVICE TCP
 *      PROTOCOL IP
 *      INTERFACE INADDR_ANY: binds all available network interfaces 
 *				to 0.0.0.0 accepting connections from any ip.
 *      BACKLOG is the amount of max queued oncoming connections waiting.
 *      Bind is used for server side in order for socket to listen to port.
 */
int server_constructor(struct Server *server, int domain, int service, int protocol,
	unsigned long interface, int port, int backlog);

#endif