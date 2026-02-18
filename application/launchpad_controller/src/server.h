#pragma once
#ifndef SERVER_H
#define SERVER_H

#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <unistd.h>
#include "packet.h"

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
extern struct k_msgq write_msgq;

/**
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

/**
 * accept_connection():
 *  Client is initialized here by being assign sockaddr_in address
 *  and int socket.
 */
int accept_connection(struct Server *server, struct Client *client);

/**
 * handle_request():
 *      This is funciton is called each iteration by "IN THREAD" continously.
 *      Writes payload data to external buffer.
 *      Both buffers are predefined buf[128] and the "p_data_size"
 *      is a pointer to the index tracking actual size of data in buffer.
 *      This way we can extract data payload out of handle_request().
 */
int handle_request(struct Client *client, uint8_t *rx_buf, uint8_t *p_data_buf, int *p_data_size);

/**
 * send_message():
 *      This is the function used by OUT_THREAD.
 *      Gets message from queue, encodes data into packet, and sends data.
 *      send() does not guarantee that all bytes are sent in one go, so has
 *      to be placed in loop until all bytes are sent.
 */
int send_message(struct Client *client, uint8_t *tx_buf);

#endif