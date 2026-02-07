from adc import ADC
from config import Config
from constants import *
from actuation import Actuation
from graph import plot_adc_graph_live


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
#	}
#	CONFIG
#	GRAPH
# 	TIME
#} Dashboard;
# =================================================================
class Dashboard(ctk.CTk):
	def __init__(self):
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
			None
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

		self.TIME = self.Time(self, "-", time.time())
		self.adc_temp_buffer = [0]*NUM_CHANNELS_TOTAL
	
		
	# config_apply_labels():
	#	Applies new names for labels defined by config.
	#	Function is passed to "import_config" in Config.
	def config_apply_labels(self):
		for i in range(0,NUM_CHANNELS_PER_ADC):
			label = self.CONFIG.get_adc_channel_label(ADC0_TAG, (i+1))
			self.ADC0.channel[i].update_label(label)
		self.ADC0.update_range_label(self.CONFIG.config["ADC0"]["range_label"])

		for i in range(0,NUM_CHANNELS_PER_ADC):
			label = self.CONFIG.get_adc_channel_label(ADC1_TAG, (i+1))
			self.ADC1.channel[i].update_label(label)
		self.ADC1.update_range_label(self.CONFIG.config["ADC1"]["range_label"])

	# ==========================================================================
	class Graph:
		def __init__(self, parent, func):
			self.panel = ctk.CTkFrame(parent)
			self.title = ctk.CTkLabel(self.panel, text="Graph", font=DEFAULT_FONT_BOLD)		
			self.button = ctk.CTkButton(self.panel, text="Plot Graph", command=func, width=150, font=DEFAULT_FONT, corner_radius=0)
	# ==========================================================================
	class Time:
		def __init__(self, parent, value, start_time):
				self.label_pgt = ctk.CTkLabel(parent, text=value, font=DEFAULT_FONT)
				self.label_srt = ctk.CTkLabel(parent, text=value, font=DEFAULT_FONT)
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
				self.label_pgt.configure(True, text=f"Time (program sinceBoot): " + self.convert_to_min_sec(self.time_pgt))
				self.label_srt.configure(True, text=f"Time (Surtr sinceBoot): " + self.convert_to_min_sec(self.time_srt))
# =============================================================================


# ===============================================================
# GLOBALS
# ===============================================================
write_queue = queue.Queue()

# ===============================================================
# MAIN FUNCTION
# ===============================================================
def main():

	root = Dashboard()
	port = sys.argv[1] if len(sys.argv) == 2 else None

	setup_dashboard(root)

	reading_thread = threading.Thread(target=serial_connection_read, args=(port,root), daemon=True)
	writing_thread = threading.Thread(target=serial_connection_write, args=(port, root), daemon=True)
	reading_thread.start()
	writing_thread.start()

	root.mainloop()


# ===============================================================
# SERIAL COM CONNECTION
# ===============================================================
# serial_connection_read():
# 	Blocking on read() until data is received. 
# 	Dissect message by checking Alignment and checksum CRC.
# 	Checksum bytes received: |low|high| so have to swap |high|low|.
# 	se_con.read(1)[0] where [0] converts byte to integer.
def serial_connection_read(port: str, root: Dashboard):
	try:
		ser_con = serial.Serial(port, BAUDRATE)
		while True:
			
			if(ser_con.read(1)[0] != ALIGNMENT_BYTE):
				continue

			length 	= ser_con.read(1)[0]
			data 	= ser_con.read(length)
			crc 	= ser_con.read(1)[0] + (ser_con.read(1)[0] << 8)
			packet = bytes([ALIGNMENT_BYTE, length]) + data

			if(crc != crc16(CRC_POLY, CRC_SEED, packet)):
				continue
				
			parse_command_protobuf(data, root)

	except serial.SerialException:
		print("Serial port connection failed.")
		return
	
# serial_connection_write():
# 	blocking here on a any form of outgoing update occurs.
#	 write queue() blocks while empty.
def serial_connection_write(port: str, root: Dashboard):
	try:
		ser_con = serial.Serial(port, BAUDRATE)
		while True:
		
			data = write_queue.get()
			packet = prepare_packet(data)
			ser_con.write(packet)

	except serial.SerialException:
		print("Serial port connection failed.")
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
	return adc_to_normalized_voltage(adc_val) * scale

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

			# ADC0 because "id" not mentioned in protobuf message.
			# 0-7 Voltage 8-11 Current
			if not data["adcMeasurements"]["id"]:
				for key, val in data["adcMeasurements"].items():

					if key == "id": 
						continue

					index = int(key.removeprefix("value"))
					if index < NUM_CHANNELS_ADC_VOLTAGE: 
						root.adc_temp_buffer[index] = adc_to_scaled_normalized_voltage(root, ADC0_TAG, (index+1), val)
					else: 
						root.adc_temp_buffer[index] = adc_to_scaled_normalized_current(root, ADC0_TAG, (index+1), val)
				root.ADC0.update_channels(root.adc_temp_buffer[0:(NUM_CHANNELS_PER_ADC)])

			# ADC1 because "id=1". Structurally: ADC1 [id] [0-11] 
			# 0-7 Voltage 8-11 Current
			else:
				for key, val in data["adcMeasurements"].items():

					if key == "id": 
						continue

					index = int(key.removeprefix("value"))
					if index < NUM_CHANNELS_ADC_VOLTAGE: 
						root.adc_temp_buffer[index+NUM_CHANNELS_PER_ADC] = adc_to_scaled_normalized_voltage(root, ADC1_TAG, (index+1), val)
					else: 
						root.adc_temp_buffer[index+NUM_CHANNELS_PER_ADC] = adc_to_scaled_normalized_current(root, ADC1_TAG, (index+1), val)

				writeRow(root.SAVEFILE_WHANDLE, time, root.adc_temp_buffer)
				root.ADC1.update_channels(root.adc_temp_buffer[NUM_CHANNELS_PER_ADC:NUM_CHANNELS_TOTAL])
			
			# Update usSinceBoot Surtr time.
			root.TIME.update_time(math.ceil(time))

			return
		case "switch_states":
			# SWITCHSTATES this is never shown in gui and never used in graph plots...
			# Ignore for now....
			# We control switches from frontend, so only reason we would ever read state
			# of switches from Surtr would be to sync/doublecheck surtr sw state with frontend sw state.
			return
		case _:
			raise Exception("Invalid SURTR command.")
		


	
# ===============================================================
# DASHBOARD GUI SETUP
# ===============================================================
def setup_dashboard(root: Dashboard):

	load_font()
	ctk.set_appearance_mode("dark")
	ctk.set_default_color_theme("dark-blue")
	root.title("Surtr Dashboard")
	root.minsize(900, 600)

	root.grid_columnconfigure(0, weight=1)
	root.grid_columnconfigure(1, weight=1)

	root.ADC0.panel.grid_columnconfigure(1, minsize=120)
	root.ADC0.panel.grid_columnconfigure(3, minsize=120)
	root.ADC1.panel.grid_columnconfigure(1, minsize=120)
	root.ADC1.panel.grid_columnconfigure(3, minsize=120)

	root.ACTUATION.panel.grid_columnconfigure(0, weight=0)  # Switches - don't expand
	root.ACTUATION.panel.grid_columnconfigure(1, weight=0)  # Steppers - don't expand
	root.ACTUATION.panel.grid_columnconfigure(2, weight=1)  # Ignition - fill remaining space

	root.ADC0.panel.grid(row=2, column=0, padx=(24, 12), pady=8, sticky="n")
	root.ADC1.panel.grid(row=2, column=1, padx=(12, 24), pady=8, sticky="n")
	root.ACTUATION.panel.grid(row=3, column=0, columnspan=2, pady=16, padx=24)

	# ADC panel titles
	root.ADC0.title.grid(row=0, column=0, columnspan=4, padx=16, pady=8)
	root.ADC1.title.grid(row=0, column=0, columnspan=4, padx=16, pady=8)

	root.ADC0.label.grid(row=1, column=0, padx=4, pady=4, sticky="w")
	root.ADC1.label.grid(row=1, column=0, padx=4, pady=4, sticky="w")

	for i in range(NUM_CHANNELS_PER_ADC):
		row = (i//2)+1
		col = (i%2)*2
		root.ADC0.channel[i].label.grid(row=row, column=col, padx=4, pady=4, sticky="w")
		root.ADC0.channel[i].value.grid(row=row, column=col+1, padx=4, pady=4, sticky="w")
		root.ADC1.channel[i].label.grid(row=row, column=col, padx=4, pady=4, sticky="w")
		root.ADC1.channel[i].value.grid(row=row, column=col+1, padx=4, pady=4, sticky="w")

	root.ADC0.PT_range_label.grid(row=7, column=0, columnspan=4, padx=16, pady=8)
	root.ADC1.PT_range_label.grid(row=7, column=0, columnspan=4, padx=16, pady=8)
	
	root.ACTUATION.switch.title.grid(row=0, column=0, columnspan=6, pady=4)
	root.ACTUATION.switch.panel.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)

	SW_PER_COL = 4
	for i in range(NUM_SWITCHES):
		row = (i) % SW_PER_COL + 1  # +1 to account for title
		col = (i) // SW_PER_COL
		root.ACTUATION.switch.button[i].label.grid(row=row, column=col*3+0, padx=4, pady=2, sticky="w")
		root.ACTUATION.switch.button[i].sw.grid(row=row, column=col*3+1, padx=4, pady=2, sticky="ew")
		#root.ACTUATION.switch.button[i].off.grid(row=row, column=col*3+2, padx=4, pady=2, sticky="ew")
	
	root.ACTUATION.stepper.title.grid(row=0, column=0, columnspan=3, pady=4)
	root.ACTUATION.stepper.panel.grid(row=0, column=1, sticky="nsew", padx=12, pady=12)

	for i in range(0, NUM_STEPPERS):
		root.ACTUATION.stepper.motor[i].label.grid(row=i+1, column=0, padx=4, pady=3, sticky="w")
		root.ACTUATION.stepper.motor[i].entry.grid(row=i+1, column=1, padx=4, pady=3, sticky="ew")
		root.ACTUATION.stepper.motor[i].button.grid(row=i+1, column=2, padx=4, pady=3, sticky="ew")
	
	root.ACTUATION.ignition.panel.grid(row=0, column=2, sticky="nsew", padx=12, pady=12)
	root.ACTUATION.ignition.title.pack(pady=4)
	root.ACTUATION.ignition.button.pack(fill="x", padx=24, pady=6)

	root.TIME.label_pgt.grid(row=1, column=0, padx=4, pady=4, sticky="w")
	root.TIME.label_srt.grid(row=1, column=1, padx=4, pady=4, sticky="w")

	root.CONFIG.path_entry.grid(row=0, column=1, padx=4, pady=4, sticky="ew")
	root.CONFIG.panel.grid_columnconfigure(1, weight=1)
	root.CONFIG.panel.grid(row=0, column=0, columnspan=2, sticky="ew", padx=8, pady=4)
	root.CONFIG.import_button.grid(row=0, column=0, padx=4, pady=4)
	
	root.GRAPH.panel.grid(row=0, column=2, sticky="nsew", padx=12, pady=12)
	root.GRAPH.title.pack(pady=4)
	root.GRAPH.button.pack(fill="x", padx=24, pady=6)


def load_font():
	ctk.FontManager.load_font(
		os.path.join(os.path.dirname(__file__), 
			"resources", 
			"IBMPlexMono-Regular.ttf"))

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
		return os.path.join(os.path.dirname(__file__), "adc_config.json")






if __name__ == "__main__":
    main()
