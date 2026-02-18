#pragma once
#ifndef DHCP_H
#define DHCP_H

#include <zephyr/logging/log.h>
#include <zephyr/kernel.h>
#include <zephyr/linker/sections.h>
#include <errno.h>
#include <stdio.h>

#include <zephyr/net/net_if.h>
#include <zephyr/net/net_core.h>
#include <zephyr/net/net_context.h>
#include <zephyr/net/net_mgmt.h>

#define DHCP_OPTION_NTP (42)

static uint8_t ntp_server[4];

static struct net_mgmt_event_callback mgmt_cb;

static struct net_dhcpv4_option_callback dhcp_cb;

/**
 * initialize_dchp():
 *      This routine is directly taken from zephyr DCHP example.
 *      Small changes have been applied. See dhcp.c
 *      We need DCHP for dynamic IP.
 */
int initialize_dchp(void);

#endif