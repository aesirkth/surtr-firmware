from constants import *
from model import *
from threading import Timer

# ===============================================================
# Watchdog:
class Watchdog:
    def __init__(self, timeout, userHandler):
        self.timeout = timeout
        self.handler = userHandler
        self.timer = Timer(self.timeout, self.onTimeout)
        self.timer.start()

    def reset(self):
        self.timer.cancel()
        self.timer = Timer(self.timeout, self.onTimeout)
        self.timer.start()

    def stop(self):
        self.timer.cancel()

    def onTimeout(self):
        print("Watchdog Timeout....")
        self.handler()
        self.reset()

# ===============================================================
# PendingRequest:
class PendingRequest:
    def __init__(self):
        self.map = {}
        self.lock = threading.Lock()
        self.count = 0
    
    def getId(self):
        with self.lock:
            return self.count

    def lookup(self, id):
        with self.lock:
            return self.map.get(id)

    def add(self, packet: Packet):
        with self.lock:
            self.map[packet.id] = packet
            self.count += 1

    def remove(self, id):
        with self.lock:
            self.map.pop(id)
            self.count -= 1

    def print(self):
        with self.lock:
            print("================.")
            for id, t in self.map.items():
                print("id: ", id, " t: ", t)
            print("================.")

    def cleanup(self, timeout):
        with self.lock:
            now = int(time.time() * 1000)
            for id, packet in list(self.map.items()):
                if ((now - packet.t_send) >= timeout):
                    self.map.pop(id)
                    print("Packet Dropped: id: ", packet.id, " cmd: ", packet.data[0])

    

# ===============================================================
# Integration:
class Integration:
    def __init__(self):

        self.writing_thread: threading.Thread = None
        self.reading_thread: threading.Thread = None
        self.communication_thread: threading.Thread = None
        self.response_handler: threading.Thread = None
        self.time_thread: threading.Thread = None

        self.connection: Connection = None
        self.requestQueue = queue.Queue()
        self.responseQueue = queue.Queue()
        self.pendingRequest = PendingRequest()

        self.stop = threading.Event()
        self.ackReceived = threading.Event()
        self.serialFail = threading.Event()

    def set(self, connection, adc, actuation, savefile, surtrTime, synAck, calculateAdc):
        self.connection = connection

        self.writing_thread = threading.Thread(
            target=uart_write_thread_main, 
            args=(self.stop, self.connection, self.requestQueue, self.pendingRequest), 
            daemon=True)
        self.reading_thread = threading.Thread(
            target=uart_read_thread_main, 
            args=(self.stop, self.serialFail, self.connection, self.responseQueue, self.pendingRequest), 
            daemon=True)

        self.communication_thread = threading.Thread(
            target=communication_thread_main, 
            args=(self.ackReceived, self.serialFail, self.connection, self.pendingRequest, synAck), 
            daemon=True)

        self.response_handler = threading.Thread(
            target=response_handler_thread_main, 
            args=(
                self.ackReceived, 
                self.connection, 
                self.responseQueue, 
                self.pendingRequest, 
                adc, 
                actuation, 
                savefile, 
                surtrTime,
                calculateAdc), 
            daemon=True)

        self.time_thread = threading.Thread(
            target=time_thread_main,
            args=(surtrTime,),
            daemon=True
        )

    def startThreads(self):
        self.stop.set()
        self.communication_thread.start()
        self.response_handler.start()
        self.writing_thread.start()
        self.reading_thread.start()
        self.time_thread.start()

# ===============================================================
# crc16():
#	Checksum CRC 16 Bytes. 
def crc16(poly, seed, buf):
        crc = seed
        for byte in buf:
            crc ^= (byte << 8)
            for _ in range(8):
                if crc & 0x8000:
                    crc = (crc << 1) ^ poly
                else:
                    crc = crc << 1
        return crc & 0xFFFF	


# ===============================================================
# timeout():
def timeout(start: float, timeout: float):
    return (time.time() - start) >= timeout

# ===============================================================
# communication_thread_main():
# 	State Machine for establishing UART connection
#   PHYSICAL:
#		Attempts to open a serial port continously
#		Failure here means there is no physical wire connection
#		If any serial.SerialException occurs then phyiscal fault,
#		go back to OPEN_SERIAL
#	ESTABLISH:
#		Send a new SYN-ACK request and wait 1000 ms for an ACK back 
#		which is set by global "connection" boolean.
# 		If no response then repeat. 
#	CONNECTED:
#		Send a new SYN-ACK request and wait 1000 ms for an ACK back 
#		which is set by global "connection" boolean.
# 		If no response then go back to TRY_CONNECT. 
def communication_thread_main(
    ackReceived: threading.Event, 
    serialFail: threading.Event,
    connection: Connection, 
    pendingRequest: PendingRequest,
    synAck
    ):
    
    def connectionTimeout():
        print("Connection Timeout()")
        #if connection.ser == None:
        #    print("Connection Timeout() is serial is None")
        #    return
        connection.setState(PAIRING),
        connection.setPing(None)

    watchdog = Watchdog(
        2, 
        lambda: connectionTimeout()
    )

    while True:
        if serialFail.is_set():
            print("DEBUG: SERIAL FAIL")
            connection.close()
            connection.setPing(None)
            connection.setState(UNPLUGGED)
            serialFail.clear()
            ackReceived.clear()
            watchdog.reset()
            time.sleep(1)
            pendingRequest.cleanup(5000)
            continue

        if connection.ser == None:
            watchdog.reset()
        if connection.ser != None:
            #print("DEBUG: COM THREAD send SYN")
            synAck()

        if ackReceived.is_set():
            # edge case with stale receiveAck signal 
            # when connection is plugged out.
            if serialFail.is_set():
                print("DEBUG: ACK RECV SERIALFAIL ---- ")
                ackReceived.clear()
            else:
                watchdog.reset()
                connection.setState(CONNECTED)
                ackReceived.clear()

        time.sleep(1)
        pendingRequest.cleanup(5000)



# ===============================================================
# uart_write_thread_main():
#	Blocking wait until a request (payload) is placed on queue.
#	Places request on pending_request map for history of requests.
#	Appends Metadata in following format:
#		1			1		 1			1		8		x		2
#	| ALIGN | LEN(payload) | ID | UART/ETH | TIME | PAYLOAD | CRC |
#	
#	Waits for access to serial object and then sends packet. 
#	Includes match case for debug purposes.
def uart_write_thread_main(
    stop: threading.Event, 
    connection: Connection,
    requestQueue: queue.Queue,
    pendingRequest: PendingRequest
    ):

    while True:
        try:
            if stop.is_set():
                time.sleep(2)
                continue

            requestPacket: Packet = requestQueue.get(timeout=0.25)
            alignment = ALIGNMENT_BYTE
            uniqueId  = pendingRequest.getId()
            t_send    = (int(time.time()*1000))
            method    = METHOD_UART


            payload = bytes([uniqueId]) 
            payload += bytes([method]) 
            payload += t_send.to_bytes(8, byteorder="little")
            payload += requestPacket.data

            length = len(payload)

            temp = bytes([alignment, length])
            temp += payload

            crc = crc16(CRC_POLY, CRC_SEED, temp)
            crc_low = crc & 0x00FF
            crc_high = (crc >> 8) & 0x00FF
            packet = temp + bytes([crc_low, crc_high])

            requestPacket.alignment = alignment
            requestPacket.length    = length
            requestPacket.id        = uniqueId
            requestPacket.method = method
            requestPacket.t_send = t_send
            requestPacket.crc = crc

            pendingRequest.add(requestPacket)

            connection.ser.write(packet)

        except queue.Empty:
            continue

        except serial.SerialException:
            stop.set()


# ===============================================================
# uart_read_thread_main():
#	When reading message, expect that TAGS must match.
#	Same command sent as same command received, otherwise keep reading.
#	If waiting too long give timeout.
def uart_read_thread_main(
    stop: threading.Event, 
    serialFail: threading.Event,
    connection: Connection,
    responseQueue: queue.Queue,
    pendingRequest: PendingRequest
    ):
    
    deadline = 0.1 # 100 ms timeout for handling each packet
    method = METHOD_UART

    while True:

        if stop.is_set():
            time.sleep(2)
            continue

        start = time.time()

        try: 
            #print("DEBUG: UART begin interation.\n")
            #if (timeout(start, deadline)):
            #	continue

            # ------------ Alignment Byte -------------- #
            align_byte = connection.ser.read(1)
            #print("DEBUG: RX Alignment byte.\n")
            if (len(align_byte) == 0):
                #print("DEBUG: RX Alignment 0.\n")
                continue
            
            if (align_byte[0] != ALIGNMENT_BYTE):
                print("DEBUG: RX Alignment Fail.\n")
                continue
            
            #if (timeout(start, deadline)):
            #	continue
            
            #print("DEBUG: UART READ receiving packet...")
            # ------------ Length Byte ------------------ #
            length_byte = connection.ser.read(1)
            #print("DEBUG: RX Length byte.")
            length = length_byte[0]
            if (len(length_byte) == 0):
                continue
            
            #if (timeout(start, deadline)):
            #	continue

            # ------------ Payload Bytes ----------------- #
            payload = connection.ser.read(length)
            #print("DEBUG: RX Payload byte.")
            if (len(payload) != length):
                continue
            
            #if (timeout(start, deadline)):
            #	continue
            
            # ------------ CRC check --------------------- #
            crc_bytes = connection.ser.read(2)
            #print("DEBUG: RX CRC.")
            if (len(crc_bytes) != 2):
                continue

            crc = crc_bytes[0] + (crc_bytes[1] << 8)
            packet = bytes([ALIGNMENT_BYTE, length]) + payload
            crc2 = crc16(CRC_POLY, CRC_SEED, packet)
            #if(crc != crc16(CRC_POLY, CRC_SEED, packet)):
            if(crc != crc2):
                print("DEBUG: RX CRC mismatch: ", crc, " : ", crc2)
                continue

            #if (timeout(start, deadline)):
            #	continue
            
            # ----- Response Unique ID Comparison -------- #
            #print("DEBUG: Unique ID comparison.")
            response_id = payload[0]
            #print("DEBUG: ID: ", response_id)
            #pendingRequest.print()
            if (response_id != MEASUREMENT_ID):
                if (pendingRequest.lookup(response_id) == None):
                    print("DEBUG: Unique ID fail.")
                    continue
            
            # ------------ Method Byte (UART/ETH) -------- #
            response_method = payload[1]
            #print("DEBUG: Response Method: ", response_method)
            if (response_method != method):
                print("DEBUG: Response fail.")
                continue

            # ---- Valid Response has been recieved ------ #
            responseQueue.put(payload)
            #print("DEBUG: RX placed on response queue.")

            # ---- Remove stale requests (>= 5000 ms) ---- #
            #pending_request.cleanup(5000)

        except serial.SerialException as exc:
            print("DEBUG: RX Serial exception.")
            serialFail.set()
            stop.set()
        
        # end while 
    #end while 
    print("DEBUG: UART READ THREAD DIE.\n")
 

 # ===============================================================
 # PARSE SURTR COMMAND
 # Unpacks message and updates data accordingly.
 # MSG TYPE		ENUM	TIME (us)		RAW DATA
 # ===============================================================
 # SYN_ACK			0					| ACK |
 # SW CTRL		    1					| ID | STATE |
 # STEP CTRL		2					| ID | MOTOR DELTA |
 # SW STATE		    3					| SW[8] 
 # ADC STATE		4					| VALUE[24] |
 # IGNITION		    5					| PASSWORD |
# ===============================================================
# response_handler_thread_main():
#	The time received from SURTR is time since boot not unix epoch (Real Time).
#	There is RTC on SURTR foud in device tree but not enabled.
def response_handler_thread_main(
    ackReceived: threading.Event, 
    connection: Connection,
    responseQueue: queue.Queue,
    pendingRequest: PendingRequest,
    adc: Adc, 
    actuation: Actuation, 
    savefile: SaveFile,
    surtrTime: Time,
    calculateAdc
    ):
    
    print("DEBUG: RESPONSE HANDLER START.\n")

    while True:

        payload = responseQueue.get()
        uniqueId = payload[0]

        requestPacket: Packet = pendingRequest.lookup(uniqueId)
        if uniqueId != MEASUREMENT_ID:
            if (requestPacket == None):
                print("packet id: ", uniqueId, " stale Ack.")
                continue
            else:
                pendingRequest.remove(uniqueId)
                t_received = int(time.time()*1000)
                t_served = t_received - requestPacket.t_send

        surtr_command = payload[10]
        t_surtr_boot = int.from_bytes(payload[2:10], "little") / 1000
        #surtrTime.setSurtrTime(t_surtr_boot)

        match surtr_command:

            # ---- SURTR SYN-ACK RESPONSE -------- #
            # ----- Set ACK received flag -------- #
            # ----- Update latest ping (ms) ------ #
            case 0:
                response_ack = payload[11]
                if(response_ack != 0xFF):
                    print("Reponse: SYN ACK: ACK is negative.\n")
                ackReceived.set()
                connection.setPing(t_served)
                print("Request: SYN-ACK id: ", uniqueId, " served in: ", t_served, " ms.")

            # ---- SURTR SW CTRL RESPONSE -------- #
            case 1: 
                response_ack = payload[11]
                if(response_ack != 0xFF):
                    print("Request: SW CTRL failed.\n")
                print("Request: SW-CTRL id: ", uniqueId, " served in: ", t_served, " ms.")

            # ---- SURTR STEP CTRL RESPONSE ------ #
            case 2: 
                response_ack = payload[11]
                if(response_ack != 0xFF):
                    print("Request: STEP CTRL failed.\n")
                print("Request: STEP-CTRL id: ", uniqueId, " served in: ", t_served, " ms.")

            # ---- SURTR ADC/SW STATE RESPONSE ------- #
            # -- Update ADC SW and store in Savefile - #
            case 3:
                adc_val: list[int] = [0]*NUM_CHANNELS_TOTAL
                sw_val: list[int]  = [0]*NUM_SWITCHES

                response_ack = payload[11]
                if(response_ack != 0xFF):
                    print("Request: Get SW state failed.\n")
                    continue

                for i in range(0, NUM_CHANNELS_TOTAL):
                    index = i*4 + 12
                    adc_val[i] = int.from_bytes(payload[index:index+4], "little")

                for i in range(0, NUM_SWITCHES):
                    sw_val[i] = payload[i+108]

                print("adc integration list:")
                print(adc_val)

                calculateAdc(adc_val)
                actuation.set(sw_val)
                savefile.writeRow(t_surtr_boot, adc_val, sw_val)

            case _:
                raise Exception("Invalid SURTR command.")


# ===============================================================
# time_thread_main():
#   Small thread that updates current GUI time since boot each second.
def time_thread_main(surtrTime: Time):
    time.sleep(10)
    while True:
        surtrTime.setGuiTime(time.time())
        time.sleep(1)


# ===============================================================
# prepare_packet():
#		1			1		 1			1		8		x		2
#	| ALIGN | LEN(payload) | ID | UART/ETH | TIME | PAYLOAD | CRC |
def prepare_packet(req_payload: bytes, method: int, unique_id: int, t_send: bytes):

    payload = bytes([unique_id]) 
    payload += bytes([method]) 
    payload += t_send 
    payload += req_payload

    align = ALIGNMENT_BYTE
    length = len(payload)

    temp = bytes([align, length])
    temp += payload

    crc = crc16(CRC_POLY, CRC_SEED, temp)
    crc_low = crc & 0x00FF
    crc_high = (crc >> 8) & 0x00FF

    print("prepare packet: id: ", unique_id)
    print("prepare packet: len: ", length)
    print("prepare packet: CRC: ", crc)

    packet = temp + bytes([crc_low, crc_high])
    print(list(packet))
    return packet
