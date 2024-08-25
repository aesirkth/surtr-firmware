from threading import Thread
import surtr_pb2 as schema
from collections import defaultdict, deque
from google.protobuf import json_format
import sys
import time
import socket
import os
from datetime import datetime
import re
import traceback
import serial

# import hvplot.streamz
# from streamz.dataframe import DataFrame

ALIGNMENT_BYTE = 0x34
CRC_POLY= 0x1011
CRC_SEED = 0x35

class SurtrParser:
    def __init__(self, arg):
        self.stream_is_serial = False
        self.stream_is_tcp = False
        self.stream_is_file = False

        # Check if the argument is an IP address
        if self._is_ip(arg):
            self.stream = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.stream.connect((arg, 1337))  # Assuming port 1337 for example
            self.stream_is_file = False
            self.stream_is_tcp = True
            print("Opened socket connection to", arg)
        else:
            # Assume it's a file path
            if arg.startswith("/dev/"):
                self.stream = serial.Serial(port=arg, baudrate=115200)
                self.stream_is_serial = True
                print("Opened serial", arg)
            else:
                self.stream = open(arg, "rb")
                self.stream_is_file = True
                print("Opened file", arg)


        if not self.stream_is_file:
                # Create a backup file with timestamp
            os.makedirs("data", exist_ok=True)
            now = datetime.now()
            filename = now.strftime("data_%Y_%m_%d_%H_%M_%S.bin")
            self.backup = open("data/" + filename, "wb")

        # Initialize other attributes
        self.data = defaultdict(lambda: ([], []))
        self._reader_t = Thread(target=self._reader_thread)
        self._reader_t.start()

    def _is_ip(self, address):
        # Simple IP address check (IPv4)
        ip_pattern = re.compile(
            r'^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
            r'(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
        )
        return ip_pattern.match(address) is not None


    def _read(self, size):
        out = bytearray()
        while len(out) < size:
            if self.stream_is_file:
                chunk = self.stream.read(size - len(out))
                if chunk == b'':  # End of file
                    break
            elif self.stream_is_tcp:
                chunk = self.stream.recv(size - len(out))
                if not chunk:  # End of stream or connection closed
                    raise IOError("Connection closed or end of stream reached before reading the requested number of bytes")
            elif self.stream_is_serial:
                chunk = self.stream.read(size - len(out))
            out.extend(chunk)
        if len(out) != size:
            time.sleep(1)
            raise IOError("Could not read the requested number of bytes")

        if not self.stream_is_file:
            self.backup.write(out)
        return bytes(out)

    def _write(self, buf):
        total_written = 0
        buf_len = len(buf)
        while total_written < buf_len:
            if self.stream_is_file:
                pass
                # written = self.stream.write(buf[total_written:])
                # if written == 0:  # Handle the case where write does not write any bytes
                #     raise IOError("Write operation did not write any bytes")
            elif self.stream_is_tcp:
                written = self.stream.send(buf[total_written:])
                if written == 0:  # Handle the case where send does not send any bytes
                    raise IOError("Send operation did not send any bytes")
            elif self.stream_is_serial:
                written = self.stream.write(buf[total_written:])
                if written == 0:  # Handle the case where write does not write any bytes
                    raise IOError("Write operation did not write any bytes")
            total_written += written

    def __del__(self):
        self.stream.close()
        if not self.stream_is_file:
            self.backup.close()

    def _write_message(self, msg):
        msg_buf = msg.SerializeToString()
        output_buf = bytes([ALIGNMENT_BYTE, len(msg_buf)]) + msg_buf
        crc = self._crc16(CRC_POLY, CRC_SEED, output_buf)
        output_buf += bytes([crc & 0x00ff, (crc >> 8) & 0x00ff ])
        self._write(output_buf)

    def _reader_thread(self):
        while True:
            try:
                alignment = self._read(1)[0]
                if (alignment != ALIGNMENT_BYTE):
                    print("invalid byte")
                    continue
                length = self._read(1)[0]
                data = self._read(length)
                received_crc = 0
                received_crc = self._read(1)[0]
                received_crc += self._read(1)[0] << 8
                all_bytes = bytes([alignment, length]) + data
                crc = self._crc16(CRC_POLY, CRC_SEED, all_bytes)
                if (crc != received_crc):
                    print("invalid crc", received_crc, crc)
                    continue
                msg = schema.SurtrMessage()
                msg.ParseFromString(data)
                time = msg.us_since_boot / 1e6
                data = json_format.MessageToDict(msg, always_print_fields_with_no_presence=True)
                # print(data)
                if "adcMeasurements" in data.keys():
                    for field in data["adcMeasurements"].keys():
                        if field == "id":
                            continue
                        self.data[field + str(data["adcMeasurements"]["id"])][0].append(time)
                        value = data["adcMeasurements"][field]
                        if data["adcMeasurements"]["id"] < 8:
                            converted = value * 2.5 / ( (1 << 24) * 0.1) * 2# why multiply by 2????
                        else:
                            converted = value * 2.5 / ( (1 << 24) * 50) * 2 # why multiply by 2????

                        self.data[field + str(data["adcMeasurements"]["id"])][1].append(converted)

                elif "switchStates" in data.keys():
                    for field in data["switchStates"].keys():
                        self.data[field][0].append(time)
                        self.data[field][1].append(data["switchStates"][field])
            except Exception as e:
                traceback.print_exc()
                print("shit's fucked yo", e)

    def _crc16(self, poly, seed, buf):
        crc = seed
        for byte in buf:
            crc ^= (byte << 8)
            for _ in range(8):
                if crc & 0x8000:
                    crc = (crc << 1) ^ poly
                else:
                    crc = crc << 1
        return crc & 0xFFFF

    def ignite(self, password):
        msg = schema.SurtrMessage()
        ignition_msg = schema.Ignition()
        ignition_msg.password = password
        msg.ignition.CopyFrom(ignition_msg)
        self._write_message(msg)

    def toggle_switch(self, id, on):
        msg = schema.SurtrMessage()
        control_msg = schema.SwitchControl()
        control_msg.id = id
        control_msg.state = on
        msg.sw_ctrl.CopyFrom(control_msg)
        self._write_message(msg)

    def motor_step(self, id, delta):
        msg = schema.SurtrMessage()
        step_msg = schema.StepperControl()
        step_msg.id = id
        step_msg.motorDelta = delta
        msg.step_ctrl.CopyFrom(step_msg)
        self._write_message(msg)