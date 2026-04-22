#include "server.h"

LOG_MODULE_REGISTER(server, LOG_LEVEL_DBG);


/**
 * ==========================================================
 * accept_connection():
 *      Client is initialized here by being assign sockaddr_in address
 *      and int socket.
 */
int accept_connection(struct Server *server, struct Client *client)
{
    char incoming_ip[32];
    socklen_t addr_len = sizeof(struct sockaddr_in);

    client->socket = accept(
        server->socket, 
        (struct sockaddr*)&client->address, 
        (socklen_t*)&addr_len);

    if (client->socket < 0)
    {
        LOG_ERR("Accept Failed.");
        return 0;
    }

    inet_ntop(IPV4, &client->address, incoming_ip, sizeof(incoming_ip));

    return 1;
}

/**
 * ==========================================================
 * ethernet_handle_request():
 *      Blocking read on recv() until a request has been received.
 *      Retrieve payload out of packet received.
 *      Place payload data on the request Queue.
 */
int ethernet_handle_request(struct Client *client)
{
    uint8_t rx_buffer[MSG_SIZE];
    uint8_t payload_buffer[MSG_SIZE];
    uint8_t payload_size;

    while(1)
    {
        int num_bytes = recv(client->socket, rx_buffer, MSG_SIZE, 0);
        if (num_bytes < 0)
        {
            LOG_ERR("Ethernet: Socket recv() failed.");
            return 0;
        }
        if(num_bytes == 0)
        {
           // Do Nothing. 
            LOG_ERR("Ethernet: Socket recv() NumBytes == 0.");
        }

        if(!retrieve_packet(rx_buffer, payload_buffer))
        {
            LOG_WRN("Ethernet: failed to retrieve packet.");
            return 0;
        }

        if(k_msgq_put(&request_msgq, payload_buffer, K_NO_WAIT) != 0)
        {
            LOG_WRN("Ethernet: Message could not be placed on queue.");
            return 0;
        }
    }

    return 1;
}



/**
 * ==========================================================
 * ethernet_send_message():
 *     Tries to send message until entire TX_BUFFER has been passed.
 */
int ethernet_send_message(struct Client *client, uint8_t *tx_buffer, const uint8_t tx_size)
{
    uint8_t sent_bytes = 0;
    uint8_t num_bytes = 0;

    while (sent_bytes < tx_size) {
        num_bytes = send(client->socket, tx_buffer + sent_bytes, tx_size - sent_bytes, 0); //timeout?
        if (num_bytes < 0) 
        {
            LOG_WRN("Ethernet: Send() failed.");
            return 0;
        } 
        else if (num_bytes > 0)
            sent_bytes += num_bytes;
        else
            break;
    }

    return 1;
}



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
int server_constructor(
    struct Server* server,
    int domain, 
    int service, 
    int protocol,
	unsigned long interface, 
    int port, 
    int backlog)
{
	server->domain = domain;
	server->service = service;
	server->protocol = protocol;
	server->interface = interface;
	server->port = port;
	server->backlog = backlog;
	server->address.sin_family = domain;
	server->address.sin_port = htons(port);
	server->address.sin_addr.s_addr = htonl(interface);
	server->socket = socket(domain, service, protocol);
	if(server->socket == 0) {
		LOG_ERR("Failed to connect socket..\n");
		return 0;
	}
	if((bind(server->socket, (struct sockaddr*)&server->address, sizeof(server->address))) < 0) {
		LOG_ERR("Failed to bind socket...\n");
        return 0;
	}
	if((listen(server->socket, server->backlog)) < 0) {
		LOG_ERR("Failed to start listening...\n");
		return 0;
	}
	

    return 1;
}