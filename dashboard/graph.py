
from constants import *
import time as t


WINDOW 				= 1
WINDOW2				= 2
WINDOW_WIDTH 		= 20
WINDOW_HEIGHT 		= 10
STATIC_ROWS			= 1
STATIC_COLUMNS		= 2

# ===============================================================
#  ADC GRAPH PLOT
# ===============================================================
# main():
#   Open CSV data file that has outline:
#   | time | adc0 | adc1 | .... | adc23 |
#   save all adc columns into individual lists and plot them all
#   together on a single line chart.
#   Y-AXIS: adc0-23
#   X-AXIS: time
#
#   Could potentially be quite memory unefficient to save all data
#   into memory.
#	Using plt.show() here directly will make this the only window.
def plot_adc_graph_static(filepath, configfile):
	
	file = open(filepath, "r")
	config = json.load(open(configfile, 'r'))
	
	time = []
	adc = [[] for _ in range(24)]

    # Read first row with labels
	if file.readline() == EOF:
		return

	while(True):
		line = file.readline()
		if line == EOF:
			break
		getRow(line, time, adc)

	fig = plt.figure(WINDOW, (WINDOW_WIDTH, WINDOW_HEIGHT))

    # VOLTAGE SUBPLOT ADC0 0-7 ADC1 0-7
	# Index 1 out of 2, 1st of 2 columns.
	ax1 = plt.subplot(STATIC_ROWS, STATIC_COLUMNS, 1)
	ax1.set_title("Voltage (V) in ADCs over time (t)")
	ax1.set_ylabel("Voltage (V)")
	ax1.set_xlabel("time (t) (seconds)")
	voltage_subplot(time, adc, config)
	plt.legend()

    # CURRENT SUBPLOT ADC0 8-11 ADC1 8-11
	ax2 = plt.subplot(STATIC_ROWS, STATIC_COLUMNS, 2)
	ax2.set_title("Current (I) in ADCs over time (t)")
	ax2.set_ylabel("Current (I)")
	ax2.set_xlabel("time (t) (seconds)")
	current_subplot(time, adc, config)
	plt.legend()

	plt.tight_layout()
	#plt.show()

# ===============================================================
# plot_adc_graph_static_separate():
# 	Plots all graphs that have valid label and values
#	as an individual graph instead of combined.
def plot_adc_graph_static_separate(filepath, configfile):

	file = open(filepath, "r")
	config = json.load(open(configfile, 'r'))
	time = []
	adc = [[] for _ in range(24)]
	subplots = []

	plt.figure(WINDOW2, (WINDOW_WIDTH, WINDOW_HEIGHT))
	subplots = collect_subplots(config)

    # Read first row with labels
	# Read in all data from .csv file into adc[[]]
	if file.readline() == EOF:
		return
	while(True):
		line = file.readline()
		if line == EOF:
			break
		getRow(line, time, adc)

	# Create a Grid of subplots 
	subplots_length = len(subplots)
	rows = math.ceil(subplots_length / STATIC_COLUMNS)

	for i,sbp in enumerate(subplots, start=1):

		ax = plt.subplot(rows, STATIC_COLUMNS, i)
		if(isVoltageADC(sbp["num"])):
			ax.set_title("Voltage (V) in ADCs over time (t)")
			ax.set_ylabel("Voltage (V)")
			ax.set_label("time (t) (seconds)")
		else:
			ax.set_title("Current (I) in ADCs over time (t)")
			ax.set_ylabel("Current (I)")
			ax.set_xlabel("time (t) (seconds)")
		plt.plot(time, adc[sbp["num"]], label=sbp["label"])
		plt.legend()

	plt.tight_layout()
	#plt.show()

# ===============================================================
# plot_single_graph_live():
#	Creates a figure for singular ADC value and label. 
#	Contiously reads from .csv file for new data.
# 	plt.pause() will initially make plot interactive (live)
# 	and will continously update and redraw graph.
#	Have to restate label each time plt.plot is called.
#	If .csv data file has no data then EXIT.
#	
def plot_single_graph_live(adc_id, adc_num, filepath: str, configfile: str):
	config = json.load(open(configfile, 'r'))
	file = open(filepath, "r")
	adc_val = []
	time = []

	plt.figure(adc_num, (WINDOW_WIDTH, WINDOW_HEIGHT))
	if(adc_id == ADC0_TAG):
		label = config["ADC0"][f"channel{adc_num+1}"]["label"]
	else:
		label = config["ADC1"][f"channel{adc_num+1}"]["label"]

	if(isVoltageADC(adc_num)):
		plt.title("Voltage (V) in ADCs over time (t)")
		plt.ylabel("Voltage (V)")
		plt.xlabel("time (t) (seconds)")
	else:
		plt.title("Current (I) in ADCs over time (t)")
		plt.ylabel("Current (I)")
		plt.xlabel("time (t) (seconds)")

    # Read first row with labels
	# Place file pointer to start of row 2.
	# if row 2 is empty then invalid graph CANCEL.
	# Go back to row2 if graph was valid.
	if file.readline() == EOF:
		plt.close(adc_num)
		file.close()
		return

	filepos = file.tell()
	if file.readline() == EOF:
		plt.close(adc_num)
		file.close()
		return

	file.seek(filepos)
	
	# IF window is exited we break from loop.
	# and destroy figure.
	while(True):

		if(not plt.fignum_exists(adc_num)):
			plt.close(adc_num)
			file.close()
			return

		# Read in all new data and update file position.
		while(True):
			file.seek(filepos)
			line = file.readline()
			if line == EOF:
				t.sleep(1)
				break

			column = line.strip().split(",")
			time.append(float(column[0]))

			if(adc_id == ADC0_TAG):
				adc_val.append(float(column[adc_num+1]))
			else:
				adc_val.append(float(column[adc_num+1+NUM_CHANNELS_PER_ADC]))

			filepos = file.tell()

		plt.cla()
		plt.plot(time, adc_val, label=label)
		plt.legend()
		plt.tight_layout()
		plt.pause(1)

# ===============================================================
# getRow():
#	splits row of .csv data into their equivalent column adc.
#	| time | adc01 | adc02 | ....
def getRow(line, time, adc):
	column = line.strip().split(",")
	time.append(float(column[0]))

	for i in range(24):
		adc[i].append(float(column[i+1]))

# ===============================================================
# voltage_subplot():
#	Left side voltage subplot.
#	Collects and plots adc values for all adcs which have a defined label in config file. 
def voltage_subplot(time, adc, config):
	for i in range(0, ADC0_CHANNEL_VOLTAGE_END):
		label = config["ADC0"][f"channel{i+1}"]["label"]
		if label != ADC_NOTUSED:
			plt.plot(time, adc[i], label=label)
	for i in range(ADC0_CHANNEL_CURRENT_END, ADC1_CHANNEL_VOLTAGE_END):
		label = config["ADC1"][f"channel{i+1-ADC0_CHANNEL_CURRENT_END}"]["label"]
		if label != ADC_NOTUSED:
			plt.plot(time, adc[i], label=label)

# ===============================================================
# current_subplot():
#	Right side voltage subplot.
#	Collects and plots adc values for all adcs which have a defined label in config file. 
def current_subplot(time, adc, config):
	for i in range(ADC0_CHANNEL_VOLTAGE_END, ADC0_CHANNEL_CURRENT_END):
		label = config["ADC0"][f"channel{i+1}"]["label"]
		if label != ADC_NOTUSED:
			plt.plot(time, adc[i], label=label)

	for i in range(ADC1_CHANNEL_VOLTAGE_END, ADC1_CHANNEL_CURRENT_END):
		label = config["ADC1"][f"channel{i+1-12}"]["label"]
		if label != ADC_NOTUSED:
			plt.plot(time, adc[i], label=label)

# ===============================================================
# collect_subplots():
# 	Iterate through all ADC and collect all valid with label into 
#	list of subplots {num, label}
def collect_subplots(config):
	subplots = []

	for i in range(0, ADC0_CHANNEL_VOLTAGE_END):
		label = config["ADC0"][f"channel{i+1}"]["label"]
		if label != ADC_NOTUSED:
			sbp = {"num": i, "label": label}
			subplots.append(sbp)

	for i in range(ADC0_CHANNEL_CURRENT_END, ADC1_CHANNEL_VOLTAGE_END):
		label = config["ADC1"][f"channel{i+1-ADC0_CHANNEL_CURRENT_END}"]["label"]
		if label != ADC_NOTUSED:
			sbp = {"num": i, "label": label}
			subplots.append(sbp)

	for i in range(ADC0_CHANNEL_VOLTAGE_END, ADC0_CHANNEL_CURRENT_END):
		label = config["ADC0"][f"channel{i+1}"]["label"]
		if label != ADC_NOTUSED:
			sbp = {"num": i, "label": label}
			subplots.append(sbp)

	for i in range(ADC1_CHANNEL_VOLTAGE_END, ADC1_CHANNEL_CURRENT_END):
		label = config["ADC1"][f"channel{i+1-12}"]["label"]
		if label != ADC_NOTUSED:
			sbp = {"num": i, "label": label}
			subplots.append(sbp)

	return subplots

# ===============================================================
# isVoltageADC():
#	Voltage:	0-7 && 12-20 
#	Current:	8-11 && 21-24 
def isVoltageADC(adc_num):
	if ((adc_num < ADC0_CHANNEL_VOLTAGE_END) or
		(adc_num >= ADC0_CHANNEL_CURRENT_END and 
   		 adc_num < ADC1_CHANNEL_VOLTAGE_END)):
		return True
	return False

# Can be run as executable. In that case it is not live.
# In order to have multiple windows, plt.show() can only be run once.
# So it has to be placed here instead of specific functions.
# ===============================================================
if __name__ == "__main__":
	if len(sys.argv) < 3:
		print("Usage: graph.py <csv.file> <json.config>")
		sys.exit(1)
	
	plot_adc_graph_static(sys.argv[1], sys.argv[2])
	plot_adc_graph_static_separate(sys.argv[1], sys.argv[2])
	plt.show()