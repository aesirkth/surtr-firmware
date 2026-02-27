from adc import ADC
from config import Config
from constants import *
from actuation import Actuation
from graph import plot_adc_graph_live
import re
try:
	from gs_usb.gs_usb import GsUsb
	from gs_usb.gs_usb_frame import GsUsbFrame
	from gs_usb.constants import CAN_EFF_FLAG
	import usb.util
	_GS_USB_AVAILABLE = True
except Exception:
	_GS_USB_AVAILABLE = False

GS_CAN_MODE_NORMAL = 0


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
#	GRAPH
# 	TIME
#} Dashboard;
# =================================================================
class Dashboard(ctk.CTk):
	def __init__(self, initial_port_arg=None):
		super().__init__()

		self.SAVEFILE 		= get_logfile_name()
		self.SAVEFILE_WHANDLE = init_logfile(self.SAVEFILE)

		self.ADC0 = ADC(
			self,
			ADC0_TAG,
			"ADC0",
			""
		)
		self.ADC1 = ADC(
			self,
			ADC1_TAG,
			"ADC1",
			""
		)

		self.ACTUATION 	= Actuation(
			self,
			lambda: ignition_command(0),
			switch_command,
			None,
			self.send_can_switch_command
		)

		self.CONFIG = Config(
			self, 
			self.config_apply_labels,
			get_default_config_path()
		)
		self.config_apply_labels()

		self.GRAPH = self.Graph(
			self,
			lambda: plot_adc_graph_live(self.SAVEFILE, self.CONFIG.filepath)
		)
		self.SIDEBAR = ctk.CTkFrame(self, fg_color="transparent")
		self.CONNECTION = self.Connection(
			self.SIDEBAR,
			lambda: self.reconnect_serial(self.CONNECTION.port_var.get()),
			initial_port_arg
		)
		self.CAN_COMMAND = self.CanCommand(
			self.SIDEBAR,
			lambda: self.send_can_command(self.CAN_COMMAND.can_id_entry.get(), self.CAN_COMMAND.message_entry.get())
		)
		self.CAN_RECOVERY = self.CanRecovery(
			self.SIDEBAR,
			self.recover_can_connection
		)

		self.TIME = self.Time(self.SIDEBAR, "-", time.time())
		self.adc_temp_buffer = [0]*NUM_CHANNELS_TOTAL
		self.serial_connection = None
		self.serial_stop_event = None
		self.reading_thread = None
		self.writing_thread = None
		self.connection_lock = threading.Lock()
		self.can_lock = threading.Lock()
		self.ui_alive = True
		self.can_device = None
		self.can_bitrate = 500000
		self.update_connection_status(False)
	
		
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

		for i in range(0,NUM_CHANNELS_PER_ADC):
			ch_id = i + 1
			label = self.CONFIG.get_adc_channel_label(ADC1_TAG, ch_id)
			self.ADC1.channel[i].update_label(label)
			self.ADC1.channel[i].set_disabled(self.CONFIG.get_adc_channel_disabled(ADC1_TAG, ch_id))
		self.ADC1.update_range_label(self.CONFIG.config["ADC1"]["range_label"])

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

		for i in range(4):
			can_switch_id = i + 1
			can_switch_button = self.ACTUATION.can_switch.button[i]
			can_switch_button.update_label(self.CONFIG.get_can_switch_label(can_switch_id))
			can_switch_button.update_state_labels(
				self.CONFIG.get_can_switch_on_label(can_switch_id),
				self.CONFIG.get_can_switch_off_label(can_switch_id)
			)
			can_switch_button.set_disabled(self.CONFIG.get_can_switch_disabled(can_switch_id))

	def _normalize_port_arg(self, raw_port):
		if raw_port is None:
			return None
		port = str(raw_port).strip()
		return port if port else None

	def reconnect_serial(self, raw_port):
		port = self._normalize_port_arg(raw_port)

		self.disconnect_serial()

		try:
			ser_con = serial.Serial(port, BAUDRATE, timeout=0.25)
		except serial.SerialException as exc:
			print(f"Reconnect failed for port '{port}': {exc}")
			self.update_connection_status(False)
			return

		self.serial_connection = ser_con
		self.serial_stop_event = threading.Event()
		self.reading_thread = threading.Thread(target=serial_connection_read, args=(ser_con, self, self.serial_stop_event), daemon=True)
		self.writing_thread = threading.Thread(target=serial_connection_write, args=(ser_con, self, self.serial_stop_event), daemon=True)
		self.reading_thread.start()
		self.writing_thread.start()
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

			self.serial_connection = None
			self.serial_stop_event = None
			self.reading_thread = None
			self.writing_thread = None

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

	def _parse_can_id(self, can_id_text: str):
		raw = can_id_text.strip()
		if raw == "":
			raise ValueError("CAN ID is empty.")
		return int(raw, 16)

	def _parse_two_hex_bytes(self, text: str):
		msg = text.strip()
		if msg == "":
			raise ValueError("CAN message is empty.")

		if " " in msg or "," in msg:
			tokens = [tok for tok in msg.replace(",", " ").split() if tok]
			if len(tokens) != 2:
				raise ValueError("CAN message must be exactly two bytes.")
			return bytes(int(tok, 16) for tok in tokens)

		msg = msg.replace("0x", "").replace("0X", "")
		if len(msg) != 4:
			raise ValueError("CAN message must be exactly 4 hex chars (2 bytes).")
		return bytes(int(msg[i:i+2], 16) for i in range(0, len(msg), 2))

	def _get_can_device(self):
		if self.can_device is not None:
			return self.can_device
		if not _GS_USB_AVAILABLE:
			raise RuntimeError("gs-usb is not installed. Install with: pip install gs-usb==0.3.0")

		try:
			devs = GsUsb.scan()
			if len(devs) == 0:
				raise RuntimeError("No INNO-MAKER usb2can device found.")

			dev = devs[0]
			try:
				dev.stop()
			except Exception:
				pass

			if not dev.set_bitrate(self.can_bitrate):
				raise RuntimeError(f"Failed to set CAN bitrate to {self.can_bitrate}.")

			dev.start(GS_CAN_MODE_NORMAL)
			self.can_device = dev
			print(f"usb2can ready (bitrate={self.can_bitrate}, device_index=0)")
		except Exception as exc:
			if "libusb" in str(exc).lower():
				raise RuntimeError("usb2can requires libusb driver setup (Zadig) and libusb-1.0.dll per INNO-MAKER instructions.") from exc
			raise
		return self.can_device

	def close_can_bus(self):
		if self.can_device is not None:
			try:
				self.can_device.stop()
			except Exception:
				pass
			try:
				usb.util.dispose_resources(self.can_device.gs_usb)
			except Exception:
				pass
			self.can_device = None
			time.sleep(0.1)

	def _simulate_usb_replug_locked(self, raw_usb_dev=None):
		# Best-effort software equivalent of unplug/replug: USB device reset + re-enumeration delay.
		usb_dev = raw_usb_dev
		if usb_dev is None:
			try:
				devs = GsUsb.scan()
				if len(devs) > 0:
					usb_dev = devs[0].gs_usb
			except Exception:
				usb_dev = None

		if usb_dev is None:
			return

		try:
			usb_dev.reset()
			print("Issued USB reset cycle for usb2can device.")
		except Exception as exc:
			print(f"USB reset cycle failed: {exc}")
		time.sleep(1.0)

	def _recover_can_connection_locked(self, max_attempts=3):
		raw_usb_dev = self.can_device.gs_usb if self.can_device is not None else None
		self.close_can_bus()
		self._simulate_usb_replug_locked(raw_usb_dev)
		last_exc = None
		for attempt in range(max_attempts):
			try:
				self._get_can_device()
				return True
			except Exception as exc:
				last_exc = exc
				time.sleep(0.2 * (attempt + 1))
		print(f"CAN recovery failed: {last_exc}")
		return False

	def recover_can_connection(self):
		with self.can_lock:
			print("Recovering CAN backend...")
			if self._recover_can_connection_locked():
				print("CAN recovery successful.")
			return

	def _is_recoverable_can_error(self, exc: Exception):
		msg = str(exc).lower()
		return (
			"timeout error" in msg
			or "_usb_reap_async" in msg
			or "no backend available" in msg
			or "device not found" in msg
			or "resource is in use" in msg
			or "could not claim interface" in msg
		)

	def _send_can_payload(self, can_id: int, payload: bytes, context: str):
		if len(payload) > 8:
			print(f"CAN send failed: payload too long ({len(payload)} bytes).")
			return False
		frame_can_id = can_id | CAN_EFF_FLAG if can_id > 0x7FF else can_id
		frame = GsUsbFrame(can_id=frame_can_id, data=payload)

		with self.can_lock:
			for attempt in range(2):
				try:
					dev = self._get_can_device()
					if dev.send(frame):
						print(f"{context} -> CAN ID 0x{can_id:X}: {payload.hex(' ').upper()}")
						return True
					print(f"{context} failed: device did not accept frame.")
					return False
				except Exception as exc:
					if attempt == 0 and self._is_recoverable_can_error(exc):
						print(f"{context}: CAN backend timeout/error, trying recovery and retry...")
						if self._recover_can_connection_locked():
							continue
					print(f"{context} failed: {exc}")
					return False

			return False

	def send_can_command(self, can_id_text: str, message_text: str):
		try:
			can_id = self._parse_can_id(can_id_text)
		except ValueError as exc:
			print(f"Invalid CAN ID hex: {exc}")
			return
		try:
			payload = self._parse_two_hex_bytes(message_text)
		except ValueError as exc:
			print(f"Invalid CAN message hex: {exc}")
			return
		self._send_can_payload(can_id, payload, "Sent custom CAN")

	def send_can_switch_command(self, switch_id: int, state: bool):
		try:
			can_id_text = self.CAN_COMMAND.can_id_entry.get().strip()
			can_id = self._parse_can_id(can_id_text if can_id_text else "124")
		except ValueError as exc:
			print(f"CAN switch {switch_id} send failed: {exc}")
			return
		payload = bytes([switch_id, 0x01 if state else 0x00])
		state_text = "ON" if state else "OFF"
		self._send_can_payload(can_id, payload, f"Sent CAN switch {switch_id} {state_text}")

	# ==========================================================================
	class Graph:
		def __init__(self, parent, func_plot):
			self.panel = ctk.CTkFrame(parent)
			self.title = ctk.CTkLabel(self.panel, text="Plot", font=DEFAULT_FONT)		
			self.button = ctk.CTkButton(self.panel, text="Plot Graph", command=func_plot, width=150, font=DEFAULT_FONT, corner_radius=0)

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
	class CanCommand:
		def __init__(self, parent, func_send):
			self.panel = ctk.CTkFrame(parent)
			self.title = ctk.CTkLabel(self.panel, text="CAN Command", font=DEFAULT_FONT)
			can_id_vcmd = (self.panel.register(self._validate_can_id), "%P")
			msg_vcmd = (self.panel.register(self._validate_can_message), "%P")
			self.can_id_var = ctk.StringVar(value="124")
			self.can_id_entry = ctk.CTkEntry(
				self.panel,
				width=150,
				font=DEFAULT_FONT,
				corner_radius=0,
				placeholder_text="CAN ID hex",
				textvariable=self.can_id_var,
				validate="key",
				validatecommand=can_id_vcmd,
			)
			self.message_entry = ctk.CTkEntry(
				self.panel,
				width=150,
				font=DEFAULT_FONT,
				corner_radius=0,
				placeholder_text="2 bytes hex",
				validate="key",
				validatecommand=msg_vcmd,
			)
			self.send_button = ctk.CTkButton(
				self.panel,
				text="Send",
				command=func_send,
				width=150,
				font=DEFAULT_FONT,
				corner_radius=0
			)

		def _validate_can_id(self, proposed: str):
			if proposed == "":
				return True
			return re.fullmatch(r"(0[xX])?[0-9a-fA-F]*", proposed) is not None

		def _validate_can_message(self, proposed: str):
			if proposed == "":
				return True
			if re.fullmatch(r"[0-9a-fA-FxX,\s]*", proposed) is None:
				return False

			if " " in proposed or "," in proposed:
				tokens = [tok for tok in re.split(r"[\s,]+", proposed.strip()) if tok]
				if len(tokens) > 2:
					return False
				for tok in tokens:
					if re.fullmatch(r"(0[xX])?[0-9a-fA-F]{0,2}", tok) is None:
						return False
				return True

			return re.fullmatch(r"(0[xX])?[0-9a-fA-F]{0,4}", proposed) is not None

	# ==========================================================================
	class CanRecovery:
		def __init__(self, parent, func_recover):
			self.panel = ctk.CTkFrame(parent)
			self.title = ctk.CTkLabel(self.panel, text="CAN Recovery", font=DEFAULT_FONT)
			self.button = ctk.CTkButton(
				self.panel,
				text="Recover CAN",
				command=func_recover,
				width=150,
				font=DEFAULT_FONT,
				corner_radius=0
			)

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
			
		def update_time(self, val):
				self.time_pgt = math.ceil(time.time() - self.start_time)
				self.time_srt = math.ceil(val)
				self.label_pgt.configure(True, text=f"Time (program): " + self.convert_to_min_sec(self.time_pgt))
				self.label_srt.configure(True, text=f"Time (Surtr): " + self.convert_to_min_sec(self.time_srt))
# =============================================================================


# ===============================================================
# GLOBALS
# ===============================================================
write_queue = queue.Queue()
CONNECTION_LOST_TIMEOUT_S = 2.0

# ===============================================================
# MAIN FUNCTION
# ===============================================================
def main():

	port = sys.argv[1] if len(sys.argv) == 2 else None
	root = Dashboard(port)

	setup_dashboard(root)
	root.reconnect_serial(port)

	root.mainloop()
	root.ui_alive = False
	root.disconnect_serial(update_ui=False)
	root.close_can_bus()


# ===============================================================
# SERIAL COM CONNECTION
# ===============================================================
# serial_connection_read():
# 	Blocking on read() until data is received. 
# 	Dissect message by checking Alignment and checksum CRC.
# 	Checksum bytes received: |low|high| so have to swap |high|low|.
# 	se_con.read(1)[0] where [0] converts byte to integer.
def serial_connection_read(ser_con: serial.Serial, root: Dashboard, stop_event: threading.Event):
	try:
		last_rx_time = time.monotonic()
		while not stop_event.is_set():
			align_byte = ser_con.read(1)
			if len(align_byte) != 1:
				if time.monotonic() - last_rx_time > CONNECTION_LOST_TIMEOUT_S:
					root.handle_connection_loss("no incoming data")
					return
				continue
			last_rx_time = time.monotonic()
			if align_byte[0] != ALIGNMENT_BYTE:
				continue

			length_byte = ser_con.read(1)
			if len(length_byte) != 1:
				if time.monotonic() - last_rx_time > CONNECTION_LOST_TIMEOUT_S:
					root.handle_connection_loss("incomplete packet header")
					return
				continue

			length = length_byte[0]
			data = ser_con.read(length)
			if len(data) != length:
				if time.monotonic() - last_rx_time > CONNECTION_LOST_TIMEOUT_S:
					root.handle_connection_loss("incomplete packet payload")
					return
				continue

			crc_bytes = ser_con.read(2)
			if len(crc_bytes) != 2:
				if time.monotonic() - last_rx_time > CONNECTION_LOST_TIMEOUT_S:
					root.handle_connection_loss("incomplete packet checksum")
					return
				continue
			crc = crc_bytes[0] + (crc_bytes[1] << 8)
			packet = bytes([ALIGNMENT_BYTE, length]) + data

			if(crc != crc16(CRC_POLY, CRC_SEED, packet)):
				continue
				
			parse_command_protobuf(data, root)

	except serial.SerialException as exc:
		if not stop_event.is_set():
			root.handle_connection_loss(str(exc))
		return
	
# serial_connection_write():
# 	blocking here on a any form of outgoing update occurs.
#	 write queue() blocks while empty.
def serial_connection_write(ser_con: serial.Serial, root: Dashboard, stop_event: threading.Event):
	try:
		while not stop_event.is_set():
			try:
				data = write_queue.get(timeout=0.25)
			except queue.Empty:
				continue

			packet = prepare_packet(data)
			ser_con.write(packet)

			msg = schema.SurtrMessage()
			msg.ParseFromString(data)
			match msg.WhichOneof("command"):
				case "sw_ctrl":
					switch_id = msg.sw_ctrl.id
					switch_label = root.CONFIG.get_switch_label(switch_id)
					state_text = "ON" if msg.sw_ctrl.state else "OFF"
					print(f"Sent switch {switch_id} ({switch_label}): {state_text} to Surtr")
				case _:
					pass

	except serial.SerialException as exc:
		if not stop_event.is_set():
			root.handle_connection_loss(str(exc))
		return
	

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

# prepare_packet():
# 	Adds protocol Aligment, length, and CRC checksum to packet.
#	| Align | len | DATA | checksum |
# 	Returns valid packet ready to be sent.
def prepare_packet(data: bytes):
	align = ALIGNMENT_BYTE
	length = len(data)

	temp = bytes([align, length]) + data
	crc = crc16(CRC_POLY, CRC_SEED, temp)
	crc_low = crc & 0x00FF
	crc_high = (crc >> 8) & 0x00FF

	packet = temp + bytes([crc_low, crc_high])
	return packet

# writeRow():
# 	Writes a row into storage data file .csv in the following format:
# 	time | adc_val0 | adc_val1 | adc_val2 | adc_val3 | .... | adc_val23 |
def writeRow(file, time, adc_values):
	line = str(time) + "," + ",".join(str(v) for v in adc_values) + "\n"
	file.write(line)
	file.flush()

# switch_command():
#	Converts switch execution into surtr message and places in write queue.
#	SerializeToString actually makes msg into 'bytes' object.
def switch_command(id, state):
	msg = schema.SurtrMessage()
	control_msg = schema.SwitchControl()
	control_msg.id = id
	control_msg.state = state
	msg.sw_ctrl.CopyFrom(control_msg)
	write_queue.put(msg.SerializeToString())

# ignition_command():
#	Converts ignition execution into sutr message and places in write queue.
#	Password is "42"
def ignition_command(password):
	msg = schema.SurtrMessage()
	ignition_msg = schema.Ignition()
	ignition_msg.password = password
	msg.ignition.CopyFrom(ignition_msg)
	write_queue.put(msg.SerializeToString())

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

# parse_command_protobuf():
#	Uses protobuf protocol and derives operation from real message in packet.
#	CASE ADC_MEASUREMENTS=4
#	{
#		'usSinceBoot': '',
#		'adcMeasurements': 
#		{
#			'id': int,
#			'value0': int
#			...
#			'value11: int
#			
#		}
#	}
#	CASE SWITCHSTATE=6
#	{
#		'usSinceBoot': '',
#		'switchStates': 
#		{
#			'sw1': Bool
#			.....
#			'sw7': Bool
#			'step1': int
#			'step2': int
#		}
#	}
#
# We also write data to a data .csv file that has the following layout:
# time | adc00 | adc01 | adc02 | adc03 | adc04 | adc05 | adc06 | adc07 | adc08 | adc09 |
#  		adc010 | adc011 | adc10 | adc11 | adc12 | adc13 | adc14 | adc15 | adc16| adc17 | 
# 		 adc18 | adc19 | adc110 | adc111
# 
# 	Only ADC is written because recordings of switch states are never used
# 	requires that ADC0 and ADC1 data be sent in sync.
#
#	always_print_fields_with_no_presence makes fields that have no value be 
# 	set to 0 or "" (instead of nothing).
#
# TEMPORARY SOLUTION:
# 	Before making changes to protobuf this temporary solution
# 	works by having a buffer [24] that where ADC0 (0-11) and ADC1 (12-23).
# 	ADC0 and ADC1 comes as separate packets which messes up timing of data.
# 	Time used for graph is ADC1 for both the ADC0 and ADC1 value
# 	Both ADCs are then written to data storage file together as one.
def parse_command_protobuf(message: bytes, root: Dashboard):
	msg = schema.SurtrMessage()
	msg.ParseFromString(message)
	time = (msg.us_since_boot / 1e6)

	data = json_format.MessageToDict(msg, always_print_fields_with_no_presence=True)

	# Due to inconsistencies with the protobuf messages delivered
	# we check if "id" is mentioned in message.
	# It is only mentioned for ADC1.
	match msg.WhichOneof("command"):
		case "adc_measurements": 
			def update_adc_from_packet(adc_tag: int):
				start_index = 0 if adc_tag == ADC0_TAG else NUM_CHANNELS_PER_ADC
				for channel_num in range(1, NUM_CHANNELS_PER_ADC + 1):
					value_key = f"value{channel_num - 1}"
					adc_value = data["adcMeasurements"][value_key]

					if channel_num <= NUM_CHANNELS_ADC_VOLTAGE:
						scaled_value = adc_to_scaled_normalized_voltage(root, adc_tag, channel_num, adc_value)
					else:
						scaled_value = adc_to_scaled_normalized_current(root, adc_tag, channel_num, adc_value)

					root.adc_temp_buffer[start_index + (channel_num - 1)] = scaled_value

			# ADC0 because "id" not mentioned in protobuf message.
			if not data["adcMeasurements"]["id"]:
				update_adc_from_packet(ADC0_TAG)
				root.ADC0.update_channels(root.adc_temp_buffer[0:NUM_CHANNELS_PER_ADC])

			# ADC1 because "id=1". Structurally: ADC1 [id] [0-11].
			else:
				update_adc_from_packet(ADC1_TAG)
				writeRow(root.SAVEFILE_WHANDLE, time, root.adc_temp_buffer)
				root.ADC1.update_channels(root.adc_temp_buffer[NUM_CHANNELS_PER_ADC:NUM_CHANNELS_TOTAL])
			
			# Update usSinceBoot Surtr time.
			root.TIME.update_time(math.ceil(time))

			return
		case "switch_states":
			for i in range(NUM_SWITCHES):
				state = getattr(msg.switch_states, f"sw{i+1}")
				root.ACTUATION.switch.button[i].set_state(state)
			return
		case _:
			raise Exception("Invalid SURTR command.")
		


	
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
		col = (i%2)*2
		root.ADC0.channel[i].label.grid(row=row, column=col, padx=4, pady=4, sticky="ew")
		root.ADC0.channel[i].value.grid(row=row, column=col+1, padx=4, pady=4, sticky="ew")
		root.ADC1.channel[i].label.grid(row=row, column=col, padx=4, pady=4, sticky="ew")
		root.ADC1.channel[i].value.grid(row=row, column=col+1, padx=4, pady=4, sticky="ew")

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

	root.ACTUATION.can_switch.panel.grid(row=0, column=3, sticky="nw", padx=6, pady=6)
	root.ACTUATION.can_switch.title.grid(row=0, column=0, columnspan=3, pady=4, sticky="w")
	for i in range(4):
		root.ACTUATION.can_switch.button[i].label.grid(row=i+1, column=0, padx=2, pady=1, sticky="w")
		root.ACTUATION.can_switch.button[i].on.grid(row=i+1, column=1, padx=2, pady=1, sticky="w")
		root.ACTUATION.can_switch.button[i].off.grid(row=i+1, column=2, padx=2, pady=1, sticky="w")

	root.CONFIG.path_entry.grid(row=0, column=1, padx=4, pady=4, sticky="ew")
	root.CONFIG.panel.grid_columnconfigure(1, weight=1)
	root.CONFIG.panel.grid(row=0, column=0, columnspan=2, sticky="ew", padx=8, pady=4)
	root.CONFIG.import_button.grid(row=0, column=0, padx=4, pady=4)
	
	root.GRAPH.panel.grid(row=0, column=2, sticky="nw", padx=6, pady=6)
	root.GRAPH.title.grid(row=0, column=0, pady=4)
	root.GRAPH.button.grid(row=1, column=0, padx=6, pady=3, sticky="w")

	root.SIDEBAR.grid(row=1, column=2, sticky="nw", padx=6, pady=3)

	root.CONNECTION.panel.grid(row=0, column=0, sticky="nw", padx=0, pady=0)
	root.CONNECTION.title.grid(row=0, column=0, pady=4)
	root.CONNECTION.port_entry.grid(row=1, column=0, padx=6, pady=3, sticky="w")
	root.CONNECTION.reconnect_button.grid(row=2, column=0, padx=6, pady=3, sticky="w")
	root.CONNECTION.status_label.grid(row=3, column=0, padx=6, pady=(0, 3), sticky="w")

	root.CAN_COMMAND.panel.grid(row=1, column=0, sticky="nw", padx=0, pady=(4, 0))
	root.CAN_COMMAND.title.grid(row=0, column=0, pady=4)
	root.CAN_COMMAND.can_id_entry.grid(row=1, column=0, padx=6, pady=3, sticky="w")
	root.CAN_COMMAND.message_entry.grid(row=2, column=0, padx=6, pady=3, sticky="w")
	root.CAN_COMMAND.send_button.grid(row=3, column=0, padx=6, pady=3, sticky="w")

	root.CAN_RECOVERY.panel.grid(row=2, column=0, sticky="nw", padx=0, pady=(4, 0))
	root.CAN_RECOVERY.title.grid(row=0, column=0, pady=4)
	root.CAN_RECOVERY.button.grid(row=1, column=0, padx=6, pady=3, sticky="w")

	root.TIME.panel.grid(row=3, column=0, padx=0, pady=(4, 0), sticky="nw")
	root.TIME.label_pgt.grid(row=0, column=0, padx=6, pady=(3, 1), sticky="w")
	root.TIME.label_srt.grid(row=1, column=0, padx=6, pady=(0, 3), sticky="w")


def get_logfile_name():
	os.makedirs("data", exist_ok=True)
	savefile = "data/" + datetime.now().strftime("data_%Y_%m_%d_%H_%M_%S.csv")
	return savefile

def init_logfile(filename):
	savefile_whandle = open(filename, "w")
	savefile_whandle.write("time," + ",".join(f"adc{i:02d}" for i in range(NUM_CHANNELS_TOTAL)) + "\n")
	savefile_whandle.flush()
	return savefile_whandle

def get_default_config_path():
		return os.path.join(os.path.dirname(__file__), "config.json")


if __name__ == "__main__":
    main()
