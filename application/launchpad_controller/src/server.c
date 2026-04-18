#include "server.h"

LOG_MODULE_REGISTER(server, LOG_LEVEL_DBG);

/**
 * accept_connection():
 *  Client is initialized here by being assign sockaddr_in address
 *  and int socket.
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
 * handle_request():
 *      This is funciton is called each iteration by "IN THREAD" continously.
 *      Writes payload data to external buffer.
 *      Both buffers are predefined buf[128] and the "p_data_size"
 *      is a pointer to the index tracking actual size of data in buffer.
 *      This way we can extract data payload out of handle_request().
 */
int handle_request(struct Client *client, uint8_t *rx_buf, uint8_t *p_data_buf, int *p_data_size)
{
    int num_bytes = recv(client->socket, rx_buf, 128, 0);
    if (num_bytes < 0)
    {
        LOG_ERR("Socket recv() failed.");
        //close(client->socket);
        return 0;
    }

    *p_data_size = num_bytes;

    if(!retrieve_packet(rx_buf, p_data_buf))
    {
        return 0;
    }

    //close(client->socket);
    return 1;
}

/**
 * send_message():
 *      This is the function used by OUT_THREAD.
 *      Gets message from queue, encodes data into packet, and sends data.
 *      send() does not guarantee that all bytes are sent in one go, so has
 *      to be placed in loop until all bytes are sent.
 * 
 *      Send() takes bytes from TX_BUF and sends then over client->socket
 *      The data in TX_BUF comes from UART. TX_size is set when encoding packet.
 * 
 *      MSGQ -> ENCODE -> UART TX -> NET
 */
int send_message(struct Client *client, uint8_t *tx_buf)
{
    Msg msg;
    int sent_bytes = 0;
    int num_bytes = 0;

    uint8_t encoded_message[128];
    uint8_t tx_size = 0;

    if(!k_msgq_get(&write_msgq, &msg, K_FOREVER))
    {
        LOG_WRN("Message Queue failed to get item.");
        return 0;
    }

    encode_packet(msg.data, encoded_message, msg.length, &tx_size);

    for (int i = 0; i < tx_size; i++)
		uart_poll_out(uart_dev, tx_buf[i]);

    while (sent_bytes < tx_size) {
        num_bytes = send(client->socket, tx_buf + sent_bytes, tx_size - sent_bytes, 0);
        if (num_bytes < 0) 
        {
            LOG_WRN("Send() failed.");
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
 * uart_isr()
 *   Interrupt Service Routine for UART
 *   Reads RX data byte for byte and places in circular buffer.
 *   Call to uart_irq_update() has to be made before uart_irq_rx_ready().
 */
void uart_isr(const struct device *dev, void *circ_buf)
{
    uint8_t byte;
    if(!uart_irq_update(dev))
        return;

    while (uart_irq_rx_ready(dev))
    {
        uart_fifo_read(dev, &byte, 1);
        circ_buf_push(circ_buf, byte);
    }
}


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