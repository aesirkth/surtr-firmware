import customtkinter as ctk, os, sys, serial, threading
import queue, socket, struct, json, time, math, array
from google.protobuf import json_format
from datetime import datetime
from tkinter import filedialog
import matplotlib.pyplot as plt

# ===============================================================
# CONSTANTS
# ===============================================================
ALIGNMENT_BYTE 	= 0x34
CRC_POLY		= 0x1011
CRC_SEED 		= 0x35
BAUDRATE 		= 115200

VREF 	= 2.5
ADCBITSIZE = (1 << 24)
ADCRESISTANCE = 50

V_START = 0.9
V_END 	= 4.5
I_START = 4
I_END 	= 20

NUM_CHANNELS_PER_ADC	    = 12
NUM_CHANNELS_ADC_VOLTAGE    = 8
NUM_CHANNELS_TOTAL	 	    = 24
ADC0_CHANNEL_VOLTAGE_END    = 8
ADC0_CHANNEL_CURRENT_END    = 12
ADC1_CHANNEL_VOLTAGE_END    = 20
ADC1_CHANNEL_CURRENT_END    = 24
NUM_SWITCHES			= 8
NUM_STEPPERS			= 3

ADC0_TAG				= 0
ADC1_TAG				= 1

MS1000                  = 1
MS100                   = 0.1

METHOD_UART             = 0
MEASUREMENT_ID          = 0xFF

UNPLUGGED   = 1
PAIRING     = 2
CONNECTED   = 3

SURTR_REQUEST_SYN_ACK       = 0
SURTR_REQUEST_SW_CTRL       = 1
SURTR_REQUEST_STEP_CTRL     = 2
SURTR_REQUEST_SW_STATE      = 3
SURTR_REQUEST_ADC_STATE     = 4
SURTR_REQUEST_IGNITION      = 5

EOF 			= ""
ADC_NOTUSED 	= ""

DEFAULT_FONT = ("IBM Plex Mono", 15)
DEFAULT_FONT_BOLD = ("IBM Plex Mono", 15, "bold")