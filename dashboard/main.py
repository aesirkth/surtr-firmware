from adc import ADC
from config import Config
from constants import *
from actuation import Actuation
from graph import Graph

# ===============================================================
# CLASS DASHBOARD extends CTk
# ===============================================================
# Super() pre-initializes the class so that when "self" is 
# called in __init__ it is actually a real CTk object.
# Struct {
#	ADC0:
#		Channel[12]
#	ADC1:
#		Channel[12]
#	ACTUATION:
#		Switch:
#			button[8]
#		Stepper:
#			motor[3]
#		Ignition
#		CAN
#	}
#	CONFIG
# 	TIME
#} Dashboard;
# =================================================================
class Dashboard(ctk.CTk):
	def __init__(self, initial_port_arg=None):
		super().__init__()

		print("Dashboard initialize.\n")

		self.SAVEFILE 		= get_logfile_name()
		self.SAVEFILE_WHANDLE = init_logfile(self.SAVEFILE)
		
		self.adc_applied_buffer = array.array('i', [0]*NUM_CHANNELS_TOTAL)
		self.adc_raw_buffer 	= array.array('i', [0]*NUM_CHANNELS_TOTAL)
		self.sw_raw_buffer 		= array.array('i', [0]*NUM_SWITCHES)
		
		self.GRAPH = Graph()

		self.ADC0 = ADC(
			self,
			ADC0_TAG,
			"ADC0",
			"",
			self.GRAPH.initialize_live_graph
		)
		self.ADC1 = ADC(
			self,
			ADC1_TAG,
			"ADC1",
			"",
			self.GRAPH.initialize_live_graph
		)

		self.ACTUATION 	= Actuation(
			self,
			lambda: ignition_command(0),
			switch_command,
			None,
		)

		self.CONFIG = Config(
			self, 
			self.config_apply_labels,
			get_default_config_path()
		)
		self.config_apply_labels()

		self.SIDEBAR = ctk.CTkFrame(self, fg_color="transparent")
		self.CONNECTION = self.Connection(
			self.SIDEBAR,
			#lambda: self.reconnect_serial(self.CONNECTION.port_var.get()),
			lambda: syn_ack_command(),
			initial_port_arg
		)

		self.TIME = self.Time(self.SIDEBAR, "-", time.time())


		self.ui_alive = True
		self.update_connection_status(False)
		
		print("Dashboard initialize finish.\n")
	
		
	# config_apply_labels():
	#	Applies new names for labels defined by config.
	#	Function is passed to "import_config" in Config.
	def config_apply_labels(self):
		for i in range(0,NUM_CHANNELS_PER_ADC):
			ch_id = i + 1
			label = self.CONFIG.get_adc_channel_label(ADC0_TAG, ch_id)
			self.ADC0.channel[i].update_label(label)
			self.ADC0.channel[i].set_disabled(self.CONFIG.get_adc_channel_disabled(ADC0_TAG, ch_id))
		self.ADC0.update_range_label(self.CONFIG.config["ADC0"]["range_label"])
		self.ADC0.datafile = self.SAVEFILE
		self.ADC0.configfile = self.CONFIG.filepath

		for i in range(0,NUM_CHANNELS_PER_ADC):
			ch_id = i + 1
			label = self.CONFIG.get_adc_channel_label(ADC1_TAG, ch_id)
			self.ADC1.channel[i].update_label(label)
			self.ADC1.channel[i].set_disabled(self.CONFIG.get_adc_channel_disabled(ADC1_TAG, ch_id))
		self.ADC1.update_range_label(self.CONFIG.config["ADC1"]["range_label"])
		self.ADC1.datafile = self.SAVEFILE
		self.ADC1.configfile = self.CONFIG.filepath

		for i in range(NUM_SWITCHES):
			switch_id = i + 1
			switch_button = self.ACTUATION.switch.button[i]
			switch_button.update_label(self.CONFIG.get_switch_label(switch_id))
			switch_button.update_state_labels(
				self.CONFIG.get_switch_on_label(switch_id),
				self.CONFIG.get_switch_off_label(switch_id)
			)
			switch_button.set_disabled(self.CONFIG.get_switch_disabled(switch_id))

		for i in range(NUM_STEPPERS):
			stepper_id = i + 1
			stepper_motor = self.ACTUATION.stepper.motor[i]
			stepper_motor.update_label(self.CONFIG.get_stepper_label(stepper_id))
			stepper_motor.set_disabled(self.CONFIG.get_stepper_disabled(stepper_id))

		self.ACTUATION.ignition.update_label(self.CONFIG.get_ignition_label())
		self.ACTUATION.ignition.set_disabled(self.CONFIG.get_ignition_disabled())

	def _normalize_port_arg(self, raw_port):
		if raw_port is None:
			return None
		port = str(raw_port).strip()
		return port if port else None

	def reconnect_serial(self, raw_port):
		port = self._normalize_port_arg(raw_port)

		self.disconnect_serial()

		try:
			ser_con = serial.Serial(port, BAUDRATE, timeout=None)
		except serial.SerialException as exc:
			print(f"Reconnect failed for port '{port}': {exc}")
			self.update_connection_status(False)
			return

		print(f"Connected to Surtr on {ser_con.port}.")
		self.update_connection_status(True, ser_con.port)

	def disconnect_serial(self, update_ui=True):
		self._mark_connection_lost()
		if update_ui:
			self.update_connection_status(False)

	def handle_connection_loss(self, reason):
		if self.serial_stop_event is None or self.serial_stop_event.is_set():
			return
		print(f"Serial connection lost: {reason}")
		self._mark_connection_lost()
		self.update_connection_status(False)

	def _mark_connection_lost(self):
		with self.connection_lock:
			if self.serial_stop_event is not None:
				self.serial_stop_event.set()

			if self.serial_connection is not None and self.serial_connection.is_open:
				try:
					self.serial_connection.close()
				except serial.SerialException:
					pass

	def update_connection_status(self, connected, port=None):
		if not self.ui_alive:
			return

		if connected:
			status_text = f"Connected ({port})" if port else "Connected"
			status_color = ("gray35", "gray70")
		else:
			status_text = "Not connected"
			status_color = ("gray50", "gray60")
		try:
			if not self.winfo_exists():
				self.ui_alive = False
				return
			self.CONNECTION.status_label.configure(text=status_text, text_color=status_color)
		except Exception:
			# Window or label may already be destroyed during shutdown.
			self.ui_alive = False

	# ==========================================================================
	class Connection:
		def __init__(self, parent, func_reconnect, initial_port_arg):
			self.panel = ctk.CTkFrame(parent)
			self.title = ctk.CTkLabel(self.panel, text="Connection", font=DEFAULT_FONT)
			self.port_var = ctk.StringVar(value="" if initial_port_arg is None else str(initial_port_arg))
			self.port_entry = ctk.CTkEntry(self.panel, textvariable=self.port_var, width=150, font=DEFAULT_FONT, corner_radius=0)
			self.reconnect_button = ctk.CTkButton(self.panel, text="Reconnect", command=func_reconnect, width=150, font=DEFAULT_FONT, corner_radius=0)
			self.status_label = ctk.CTkLabel(self.panel, text="Not connected", font=("IBM Plex Mono", 12))
	# ==========================================================================

	# ==========================================================================
	class Time:
		def __init__(self, parent, value, start_time):
				self.panel = ctk.CTkFrame(parent, border_width=1)
				self.label_pgt = ctk.CTkLabel(self.panel, text=value, font=("IBM Plex Mono", 12))
				self.label_srt = ctk.CTkLabel(self.panel, text=value, font=("IBM Plex Mono", 12))
				self.start_time = start_time
				self.time_srt = None
				self.time_pgt = None

		def convert_to_min_sec(self, seconds):
			minutes = int(seconds) // 60
			secs = int(seconds) % 60
			return f"{minutes:02d}:{secs:02d}"
			
		def update_time(self, parent):
				val = time.time()
				self.time_pgt = math.ceil(time.time() - self.start_time)
				self.time_srt = math.ceil(val)
				self.label_pgt.configure(True, text=f"Time (program): " + self.convert_to_min_sec(self.time_pgt))
				self.label_srt.configure(True, text=f"Time (Surtr): " + self.convert_to_min_sec(self.time_srt))

				parent.after(1000, self.update_time, parent)
# =============================================================================




class WatchdogTimer:
	def __init__(self, period):
		self.period = period
		self.reset()

	def reset(self):
		self.deadline = time.time() + self.period

	def fail(self):
		return time.time() > self.deadline

class SerialConnection:
	def __init__(self):
		self.serial: serial.Serial = None
		#self.lock = threading.Lock()

	def set(self, new_serial):
		#print("DEBUG: conn.set() requested")
		#with self.lock:
		#print("DEBUG: conn.set() accepted")
		self.serial = new_serial

	def get(self):
		#print("DEBUG: conn.get() requested")
		#with self.lock:
		#print("DEBUG: conn.get() accepted")
		return self.serial

class Connection:
	def __init__(self):
		self.connection = False
		self.state = 0


class PendingRequest:
	def __init__(self):
		self.map = {}
		self.size = 256
		self.lock = threading.Lock()

	def add(self, t):
		with self.lock:
			for id in range(self.size):
				if id not in self.map:
					self.map[id] = t
					return id
			raise LookupError("No free IDs in Pending Request Map.\n")

	def find(self, id):
		with self.lock:
			return id in self.map

	def remove(self, id):
		with self.lock:
			self.map.pop(id)

	def lookup(self, id):
		with self.lock:
			return self.map.get(id)

	def get_unique_id(self):
		with self.lock:
			for i in range(self.size):
				if i not in self.map:
					return i
			raise LookupError("No free IDs in Pending Request Map.\n")

	def print(self):
		with self.lock:
			print("================.")
			for id, t in self.map.items():
				print("id: ", id, " t: ", t)
			print("================.")

	def cleanup(self, timeout):
		with self.lock:
			now = int(time.time() * 1000)
			discard = []
			for id, t in list(self.map.items()):
				if (now - t) >= timeout:
					discard.append(id)
			for id in discard:
				self.map.pop(id)


# ===============================================================
# GLOBALS
# ===============================================================
request_queue = queue.Queue()
response_queue = queue.Queue()
pending_request = PendingRequest()
uart_watchdog = WatchdogTimer(5)
connection = Connection()

CONNECTION_LOST_TIMEOUT_S = 2.0

# ===============================================================
# MAIN FUNCTION
# ===============================================================
def main():

	print("DEBUG: main starting.\n")

	# --- On Startup (assume UART) ------ #
	port = sys.argv[1] if len(sys.argv) == 2 else None
	root = Dashboard(port)
	serial = SerialConnection()

	stop = threading.Event()
	stop.set()
	
	#graph_thread = threading.Thread(target=graph_thread_main, args=(root,), daemon=True) 

	communication_thread = threading.Thread(target=communication_thread_main, args=(stop, serial, port), daemon=True)
	writing_thread = threading.Thread(target=uart_write_thread_main, args=(stop, serial, root), daemon=True)
	reading_thread = threading.Thread(target=uart_read_thread_main, args=(stop, serial), daemon=True)

	response_handler = threading.Thread(target=response_handler_thread_main, args=(stop, root), daemon=True)

	communication_thread.start()
	response_handler.start()
	writing_thread.start()
	reading_thread.start()

	# ------- On Startup ---------------- #
	setup_dashboard(root)
	
	root.after(1000, root.TIME.update_time, root)
	root.mainloop()

	# ------- On Shutdown --------------- #
	root.ui_alive = False
	#root.disconnect_serial(update_ui=False)



	


# ===============================================================
# communication_thread_main():
# 	State Machine for establishing UART connection
#	OPEN_SERIAL:
#		Attempts to open a serial port continously
#		Failure here means there is no physical wire connection
#		If any serial.SerialException occurs then phyiscal fault,
#		go back to OPEN_SERIAL
#	TRY_CONNECT:
#		Send a new SYN-ACK request and wait 1000 ms for an ACK back 
#		which is set by global "connection" boolean.
# 		If no response then repeat. 
#	CONNECTED:
#		Send a new SYN-ACK request and wait 1000 ms for an ACK back 
#		which is set by global "connection" boolean.
# 		If no response then go back to TRY_CONNECT. 
#
#		
def communication_thread_main(stop: threading.Event, conn: SerialConnection, port: str):
	
	print("DEBUG: COM THREAD START.\n")

	open_serial = 0
	try_connect = 1
	connected 	= 2

	connection.state = open_serial

	while True:
		try:
			match connection.state:

				case 0:

					print("DEBUG: COM State: Open Serial.\n")

					#stop.set()
					ser_old = conn.get()
					if ser_old:
						ser_old.close()

					ser_new = serial.Serial(port, BAUDRATE, timeout=None)
					conn.set(ser_new)
					stop.clear()
					connection.state = try_connect

				case 1:

					print("DEBUG: COM State: Try Connect.\n")
					# wipe pending requests
					syn_ack_command()
					 
					if connection.connection:
						connection.state = connected
					time.sleep(5)
					pending_request.cleanup(5000)
					pending_request.print()

				case 2:	
					print("DEBUG: COM State: Connected.\n")
					syn_ack_command()

					#if uart_watchdog.fail():
					#	connection.connection = False
					#	connection.state = try_connect
					#	continue

					time.sleep(5)
					pending_request.cleanup(5000)
					pending_request.print()
				
				case _:
					raise Exception("Communcation FSM invalid state\n.")
	
		except serial.SerialException as exc:
			print("Failed to open Serial port: ", port)
			connection.state = open_serial
			stop.set()
			time.sleep(MS1000)
			print("Exit exception\n")



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
def uart_write_thread_main(stop: threading.Event, conn: SerialConnection, root: Dashboard):

	print("DEBUG: UART WRITE THREAD START.\n")
	while True:

		if stop.is_set():
			time.sleep(5)
			continue

		try:

			req_payload = request_queue.get()
			#print("DEBUG: UART WRITE request received: cmd: ", req_payload[0])

			t_send = int(time.time() * 1000)
			t_send_bytes = t_send.to_bytes(8, byteorder="little")
			unique_id = pending_request.add(t_send)

			packet = prepare_packet(req_payload, METHOD_UART, unique_id, t_send_bytes) 

			ser = conn.get()
			if ser:
				ser.write(packet)
			else:
				# serial was deemed unconnected from somewhere else?
				print("serial write failed.\n")


			# ------- DEBUG SENDER --------------- #
			match req_payload[0]:
				case 1:
					switch_id = req_payload[1]
					switch_label = root.CONFIG.get_switch_label(switch_id)
					state_text = "ON" if req_payload[2] else "OFF"
					print(f"Sent switch {switch_id} ({switch_label}): {state_text} to Surtr")
				case _:
					pass

		except serial.SerialException as exc:
			# Serial connection disconnected physically?
			return

	print("DEBUG: UART WRITE THREAD DIE.\n")
	


# ===============================================================
# uart_read_thread_main():
#	When reading message, expect that TAGS must match.
#	Same command sent as same command received, otherwise keep reading.
#	If waiting too long give timeout.
def uart_read_thread_main(stop: threading.Event, conn: SerialConnection):
	
	print("DEBUG: UART READ THREAD START.\n")
	deadline = 0.1 # 100 ms timeout for handling each packet
	method = METHOD_UART

	while True:

		if stop.is_set():
			continue

		start = time.time()

		try: 
			print("DEBUG: UART begin interation.\n")
			ser = conn.get()
			# if ser 

			#if (timeout(start, deadline)):
			#	continue

			# ------------ Alignment Byte -------------- #
			align_byte = ser.read(1)
			print("DEBUG: RX Alignment byte.\n")
			if (len(align_byte) == 0):
				print("DEBUG: RX Alignment 0.\n")
				continue
			
			if (align_byte[0] != ALIGNMENT_BYTE):
				continue
			
			#if (timeout(start, deadline)):
			#	continue
			
			# ------------ Length Byte ------------------ #
			length_byte = ser.read(1)
			print("DEBUG: RX Length byte.\n")
			length = length_byte[0]
			if (len(length_byte) == 0):
				continue
			
			#if (timeout(start, deadline)):
			#	continue

			# ------------ Payload Bytes ----------------- #
			payload = ser.read(length)
			print("DEBUG: RX Payload byte.\n")
			if (len(payload) != length):
				continue
			
			#if (timeout(start, deadline)):
			#	continue
			
			# ------------ CRC check --------------------- #
			crc_bytes = ser.read(2)
			print("DEBUG: RX CRC.\n")
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
			print("DEBUG: Unique ID comparison.\n")
			response_id = payload[0]
			print("DEBUG: ID: ", response_id)
			pending_request.print()
			if (response_id != MEASUREMENT_ID):
				if (not pending_request.find(response_id)):
					print("DEBUG: Unique ID fail.\n")
					continue
			
			# ------------ Method Byte (UART/ETH) -------- #
			response_method = payload[1]
			print("DEBUG: Response Method: ", response_method)
			if (response_method != method):
				print("DEBUG: Response fail.\n")
				continue

			# ---- Valid Response has been recieved ------ #
			response_queue.put(payload)
			print("DEBUG: RX placed on response queue.\n")
			print(list(payload))

			# ---- Remove stale requests (>= 5000 ms) ---- #
			#pending_request.cleanup(5000)

		except serial.SerialException as exc:
			# Serial connection disconnected physically?
			print("DEBUG: RX Serial exception.\n")
			return
		
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
def response_handler_thread_main(stop: threading.Event, root: Dashboard):
	
	print("DEBUG: RESPONSE HANDLER START.\n")

	while True:

		payload = response_queue.get()
		print("DEBUG: response handle receieved response from queue.\n")
		print(list(payload))
		print("id: ", payload[0], " method: ", payload[1], " time: ", payload[2:10], " cmd: ", payload[10], " ack: ", payload[11])
		
		unique_id = payload[0]
		print("DEBUG: pending request print.\n")
		pending_request.print()
		print("DEBUG: pending request lookup.\n")
		t_send = pending_request.lookup(unique_id)			
		pending_request.remove(unique_id)

		t_received = int(time.time()*1000)
		t_served = t_received - t_send
		
		print("DEBUG: t_received: ", t_received)
		print("DEBUG: t_send: ", t_send)
		print("DEBUG: t_served: ", t_served)


		surtr_command = payload[10]

		match surtr_command:

			# ---- SURTR SYN-ACK RESPONSE -------- #
			# ----- Add +1 second to watchdog. --- #
			case 0:
				response_ack = payload[11]
				if(response_ack != 0xFF):
					print("Reponse: SYN ACK: ACK is negative.\n")

				uart_watchdog.reset()
				connection.connection = True

				print("Request: SYN-ACK id: ", unique_id, " served in: ", t_served, " ms.")

			# ---- SURTR SW CTRL RESPONSE -------- #
			case 1: 
				response_ack = payload[11]
				if(response_ack != 0xFF):
					print("Request: SW CTRL failed.\n")
				
				print("Request: SW-CTRL id: ", unique_id, " served in: ", t_served, " ms.")

			# ---- SURTR STEP CTRL RESPONSE ------ #
			case 2: 
				response_ack = payload[11]
				if(response_ack != 0xFF):
					print("Request: STEP CTRL failed.\n")
				
				print("Request: STEP-CTRL id: ", unique_id, " served in: ", t_served, " ms.")

			# ---- SURTR ADC/SW STATE RESPONSE ------- #
			case 3:
				response_ack = payload[11]
				if(response_ack != 0xFF):
					print("Request: Get SW state failed.\n")
					continue

				root.adc_raw_buffer.frombytes(payload[12:108])
				root.sw_raw_buffer.frombytes(payload[108:116])

				for i in range(0, ADC0_CHANNEL_VOLTAGE_END):
					scaled_value = adc_to_scaled_normalized_voltage(root, ADC0_TAG, (i+1), root.adc_raw_buffer[i])
					root.adc_applied_buffer[i] = scaled_value
				for i in range(ADC0_CHANNEL_VOLTAGE_END, ADC0_CHANNEL_CURRENT_END):
					scaled_value = adc_to_scaled_normalized_current(root, ADC0_TAG, (i+1), root.adc_raw_buffer[i])
					root.adc_applied_buffer[i] = scaled_value
				for i in range(ADC0_CHANNEL_CURRENT_END, ADC1_CHANNEL_VOLTAGE_END):
					scaled_value = adc_to_scaled_normalized_voltage(root, ADC1_TAG, (i+1), root.adc_raw_buffer[i])
					root.adc_applied_buffer[i] = scaled_value
				for i in range(ADC1_CHANNEL_VOLTAGE_END, ADC1_CHANNEL_CURRENT_END):
					scaled_value = adc_to_scaled_normalized_current(root, ADC1_TAG, (i+1), root.adc_raw_buffer[i])
					root.adc_applied_buffer[i] = scaled_value
				
				root.ADC0.update_channels(root.adc_applied_buffer[0:(NUM_CHANNELS_PER_ADC)])
				root.ADC1.update_channels(root.adc_applied_buffer[NUM_CHANNELS_PER_ADC:NUM_CHANNELS_TOTAL])
				root.ACTUATION.switch.update(root.sw_raw_buffer)
				
				writeRow(root.SAVEFILE_WHANDLE, time, root.adc_raw_buffer, root.sw_raw_buffer)
				root.TIME.update_time(math.ceil(time))
		
			case _:
				raise Exception("Invalid SURTR command.")



# ===============================================================
# switch_command():
#	places SYN-ACK message on Request Queue for send out.
#	| TIME | CMD | (9 bytes)
def syn_ack_command():
	print("SYN_ACK issued.\n")
	data = bytearray(1)
	data[0] = SURTR_REQUEST_SYN_ACK
	
	request_queue.put(data)


# ===============================================================
# switch_command():
#	Transforms id and state of switch into payload and 
#	places on Request Queue for send out.
#	| TIME | CMD | SW | STATE |	(11 bytes)
def switch_command(id, state):
	print("SW_CTRL issued.\n")
	data = bytearray(3)
	data[0] = SURTR_REQUEST_SW_CTRL
	data[1] = id
	data[2] = state

	request_queue.put(data)

# ===============================================================
# ignition_command():
#	Converts ignition execution into sutr message and places in write queue.
#	| TIME | CMD | PASSWD |	(10 bytes)
def ignition_command(password):
	data = bytearray(2)
	data[0] = SURTR_REQUEST_IGNITION
	data[1] = password
	
	request_queue.put(data)



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

# ===============================================================
# timeout():
def timeout(start: float, timeout: float):
    return (time.time() - start) >= timeout

# ===============================================================
# writeRow():
# 	Writes a row into storage data file .csv in the following format:
# 	time | adc_val0 | adc_val1 | adc_val2 | adc_val3 | .... | adc_val23 | sw0 | sw1 | .. | sw7
def writeRow(file, time, adc_raw, switches):
	line = (
        str(time) + "," +
        ",".join(str(v) for v in adc_raw) + "," +
        ",".join(str(v) for v in switches) + "\n"
    )
	file.write(line)
	file.flush()


# ===============================================================
# AD4111 Data Sheet p.29:
# 	The output code for any input voltage is represented as:
#	Code = (2^N * V_in * 0.1) / VREF
#	The output code for any input current is represented as:
#	Code = (2^N * I_in * 50) / VREF
# ===============================================================

# normalize_current():
#	Takes current reading from ADC and turns it into a 0-1 range signal.
def normalize_current(i):
	return ((i - I_START) / (I_END - I_START))

# normalize_voltage():
#	Takes voltage reading from ADC and turns it into a 0-1 range signal.
def normalize_voltage(v):
	return ((v - V_START) / (V_END - V_START))

# adc_to_voltage():
# 	Constant 2 is for VREF=2.5 => +/-1.25 so 1.25*2 => +/-2.5
# 	1 < VREF < AVDD=5V so +/-2.5 is in range.
#	Constant 0.1 unknown.	
def adc_to_voltage(adc_in):
	return ((adc_in * VREF * 2) / (ADCBITSIZE * 0.1))

# adc_to_current():
#	I = V / R=50
def adc_to_current(adc_in):
	return ((adc_in * VREF * 2) / (ADCBITSIZE * ADCRESISTANCE))

# adc_to_normalized_voltage():
#
def adc_to_normalized_voltage(adc_in):
	return normalize_voltage(adc_to_voltage(adc_in))

# adc_to_normalized_current():
#
def adc_to_normalized_current(adc_in):
	return normalize_current(adc_to_voltage(adc_in))

# adc_to_scaled_normalized_voltage():
#
def adc_to_scaled_normalized_voltage(root: Dashboard, adc_id, ch_in, adc_val):
	scale = root.CONFIG.get_adc_channel_scale(adc_id, ch_in)
	return adc_to_normalized_voltage(adc_val) * scale

# adc_to_scaled_normalized_current():
#
def adc_to_scaled_normalized_current(root: Dashboard, adc_id, ch_in, adc_val):
	scale = root.CONFIG.get_adc_channel_scale(adc_id, ch_in)
	return adc_to_normalized_current(adc_val) * scale
	
# ===============================================================
# DASHBOARD GUI SETUP
# ===============================================================
def setup_dashboard(root: Dashboard):

	ctk.set_appearance_mode("dark")
	ctk.set_default_color_theme("dark-blue")

	root.title("Surtr Dashboard")
	root.minsize(1500, 600)

	root.grid_columnconfigure(0, weight=1)
	root.grid_columnconfigure(1, weight=1)
	root.grid_columnconfigure(2, weight=0)

	root.ADC0.panel.grid_columnconfigure(1, minsize=160, weight=1)
	root.ADC0.panel.grid_columnconfigure(3, minsize=160, weight=1)
	root.ADC1.panel.grid_columnconfigure(1, minsize=160, weight=1)
	root.ADC1.panel.grid_columnconfigure(3, minsize=160, weight=1)

	root.ACTUATION.panel.grid_columnconfigure(0, weight=0)
	root.ACTUATION.panel.grid_columnconfigure(1, weight=0)
	root.ACTUATION.panel.grid_columnconfigure(2, weight=0)
	root.ACTUATION.panel.grid_columnconfigure(3, weight=0)
	root.ACTUATION.panel.grid_columnconfigure(4, weight=0)

	root.ADC0.panel.grid(row=1, column=0, padx=(16, 8), pady=8, sticky="nsew")
	root.ADC1.panel.grid(row=1, column=1, padx=(8, 16), pady=8, sticky="nsew")
	root.ACTUATION.panel.grid(row=2, column=0, columnspan=2, pady=8, padx=(16, 16), sticky="ew")

	# ADC panel titles
	root.ADC0.title.grid(row=0, column=0, columnspan=4, padx=16, pady=8)
	root.ADC1.title.grid(row=0, column=0, columnspan=4, padx=16, pady=8)

	root.ADC0.label.grid(row=1, column=0, padx=4, pady=4, sticky="ew")
	root.ADC1.label.grid(row=1, column=0, padx=4, pady=4, sticky="ew")

	for i in range(NUM_CHANNELS_PER_ADC):
		row = (i//2)+1
		col = (i%2)*3
		root.ADC0.channel[i].label.grid(row=row, column=col, padx=4, pady=4, sticky="ew")
		root.ADC0.channel[i].value.grid(row=row, column=col+1, padx=4, pady=4, sticky="ew")
		root.ADC0.channel[i].button.grid(row=row, column=col+2, padx=6, pady=3, sticky="ew")
		root.ADC1.channel[i].label.grid(row=row, column=col, padx=4, pady=4, sticky="ew")
		root.ADC1.channel[i].value.grid(row=row, column=col+1, padx=4, pady=4, sticky="ew")
		root.ADC1.channel[i].button.grid(row=row, column=col+2, padx=6, pady=3, sticky="ew")

	root.ADC0.PT_range_label.grid(row=7, column=0, columnspan=4, padx=16, pady=8)
	root.ADC1.PT_range_label.grid(row=7, column=0, columnspan=4, padx=16, pady=8)
	
	root.ACTUATION.switch.title.grid(row=0, column=0, columnspan=6, pady=4)
	root.ACTUATION.switch.panel.grid(row=0, column=0, sticky="nw", padx=6, pady=6)

	SW_PER_COL = 4
	for i in range(NUM_SWITCHES):
		row = (i) % SW_PER_COL + 1  # +1 to account for title
		col = (i) // SW_PER_COL
		root.ACTUATION.switch.button[i].label.grid(row=row, column=col*3+0, padx=2, pady=1, sticky="w")
		root.ACTUATION.switch.button[i].on.grid(row=row, column=col*3+1, padx=2, pady=1, sticky="w")
		root.ACTUATION.switch.button[i].off.grid(row=row, column=col*3+2, padx=2, pady=1, sticky="w")
	
	root.ACTUATION.stepper.title.grid(row=0, column=0, columnspan=3, pady=4)
	root.ACTUATION.stepper.panel.grid(row=0, column=1, sticky="nw", padx=6, pady=6)

	for i in range(0, NUM_STEPPERS):
		root.ACTUATION.stepper.motor[i].label.grid(row=i+1, column=0, padx=2, pady=1, sticky="w")
		root.ACTUATION.stepper.motor[i].entry.grid(row=i+1, column=1, padx=2, pady=1, sticky="w")
		root.ACTUATION.stepper.motor[i].button.grid(row=i+1, column=2, padx=2, pady=1, sticky="w")
	
	root.ACTUATION.ignition.panel.grid(row=0, column=2, sticky="nw", padx=6, pady=6)
	
	root.ACTUATION.ignition.panel.grid_columnconfigure(0, weight=1)
	root.ACTUATION.ignition.title.grid(row=0, column=0, pady=4, sticky="n")
	root.ACTUATION.ignition.button.grid(row=1, column=0, padx=6, pady=3, sticky="w")

	root.CONFIG.path_entry.grid(row=0, column=1, padx=4, pady=4, sticky="ew")
	root.CONFIG.panel.grid_columnconfigure(1, weight=1)
	root.CONFIG.panel.grid(row=0, column=0, columnspan=2, sticky="ew", padx=8, pady=4)
	root.CONFIG.import_button.grid(row=0, column=0, padx=4, pady=4)
	
	root.SIDEBAR.grid(row=1, column=2, sticky="nw", padx=6, pady=3)

	root.CONNECTION.panel.grid(row=0, column=0, sticky="nw", padx=0, pady=0)
	root.CONNECTION.title.grid(row=0, column=0, pady=4)
	root.CONNECTION.port_entry.grid(row=1, column=0, padx=6, pady=3, sticky="w")
	root.CONNECTION.reconnect_button.grid(row=2, column=0, padx=6, pady=3, sticky="w")
	root.CONNECTION.status_label.grid(row=3, column=0, padx=6, pady=(0, 3), sticky="w")

	root.TIME.panel.grid(row=4, column=0, padx=0, pady=(4, 0), sticky="nw")
	root.TIME.label_pgt.grid(row=0, column=0, padx=6, pady=(3, 1), sticky="w")
	root.TIME.label_srt.grid(row=1, column=0, padx=6, pady=(0, 3), sticky="w")

def get_logfile_name():
	os.makedirs("data", exist_ok=True)
	savefile = "data/" + datetime.now().strftime("data_%Y_%m_%d_%H_%M_%S.csv")
	return savefile

def init_logfile(filename):
	savefile_whandle = open(filename, "w")
	savefile_whandle.write("time," + ",".join(f"adc{i:02d}" for i in range(NUM_CHANNELS_TOTAL)) 
						+ ",".join(f"sw{i:02d}" for i in range(NUM_SWITCHES)) + "\n")
	savefile_whandle.flush()
	return savefile_whandle

def get_default_config_path():
		return os.path.join(os.path.dirname(__file__), "config.json")

def gettimeus64():
	return (int(time.time() * 1e6)).to_bytes(8, 'big')
			


if __name__ == "__main__":
    main()
