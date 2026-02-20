
from constants import *
import time as t


WINDOW 				= 1
WINDOW_WIDTH 		= 10
WINDOW_HEIGHT 		= 5
HALF_WINDOW_WIDTH 	= 2
EQUAL_WINDOW_HEIGHT = 1

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

	init_plot()
    # VOLTAGE SUBPLOT ADC0 0-7 ADC1 0-7
	plt.subplot(1, 2, 1)
	voltage_subplot(time, adc, config)
	plt.legend()

    # CURRENT SUBPLOT ADC0 8-11 ADC1 8-11
	plt.subplot(1, 2, 2)
	current_subplot(time, adc, config)
	plt.legend()

	plt.tight_layout()
	plt.show()



# ===============================================================
#  ADC GRAPH PLOT LIVE
# ===============================================================
def plot_adc_graph_live(filepath, configfile):

	config = json.load(open(configfile, 'r'))
	time = []
	adc = [[] for _ in range(24)]
	file = open(filepath, "r")

    # Read first row with labels
	if file.readline() == EOF:
		return
	# Place file pointer to start of row 2.
	filepos = file.tell()
	
	# if row 2 is emppty then invalid graph.
	if file.readline() == EOF:
		return

	# Go back to row2 if graph was valid.
	file.seek(filepos)

	init_plot()
	
	while(True):

		# IF window is exited we break from loop.
		if(not plt.fignum_exists(WINDOW)):
			file.close()
			return

		file.seek(filepos)
		line = file.readline()
		if line == EOF:
			t.sleep(1)
			continue

		getRow(line, time, adc)
		filepos = file.tell()

		# VOLTAGE SUBPLOT ADC0 0-7 ADC1 0-7
		plt.subplot(1, 2, 1)
		plt.cla()
		voltage_subplot(time, adc, config)
		plt.legend()


		# CURRENT SUBPLOT ADC0 8-11 ADC1 8-11
		plt.subplot(1, 2, 2)
		plt.cla()
		current_subplot(time, adc, config)
		plt.legend()

		# plt.pause() will initially make plot interactive (live)
		# and will continously update and redraw graph.
		plt.tight_layout()
		plt.pause(1)
	


# getRow():
#	splits row of .csv data into their equivalent column adc.
#	| time | adc01 | adc02 | ....
def getRow(line, time, adc):
	column = line.strip().split(",")
	time.append(float(column[0]))

	for i in range(24):
		adc[i].append(float(column[i+1]))

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

# init_plot():
#	Set Window width, height and labels for all plots.
def init_plot():
	plt.figure(WINDOW, (WINDOW_WIDTH, WINDOW_HEIGHT))
	plt.subplot(WINDOW, HALF_WINDOW_WIDTH, EQUAL_WINDOW_HEIGHT)
	plt.title("Voltage (V) in ADCs over time (t)")
	plt.ylabel("Voltage (V)")
	plt.xlabel("time (t) (seconds)")
	plt.subplot(WINDOW, HALF_WINDOW_WIDTH, EQUAL_WINDOW_HEIGHT)
	plt.title("Current (I) in ADCs over time (t)")
	plt.ylabel("Current (I)")
	plt.xlabel("time (t) (seconds)")


# Can be run as executable. In that case it is not live.
# ===============================================================
if __name__ == "__main__":
	if len(sys.argv) < 3:
		print("Usage: graph.py <csv.file> <json.config>")
		sys.exit(1)
	
	plot_adc_graph_static(sys.argv[1], sys.argv[2])