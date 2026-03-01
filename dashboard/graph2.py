from constants import *
from tkinter import filedialog
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk


WINDOW_WIDTH = 1320
WINDOW_HEIGHT = 820
PLOT_REFRESH_MS = 1000


def _safe_channel_label(label, fallback):
	return label if label != ADC_NOTUSED else fallback


def _read_csv(filepath):
	time_values = []
	adc_values = [[] for _ in range(NUM_CHANNELS_TOTAL)]
	last_raw_time = None
	last_adjusted_time = None
	runtime_offset = 0.0

	with open(filepath, "r", encoding="utf-8") as file:
		if file.readline() == EOF:
			return time_values, adc_values

		for line in file:
			row = line.strip()
			if not row:
				continue
			columns = row.split(",")
			if len(columns) < NUM_CHANNELS_TOTAL + 1:
				continue
			try:
				raw_time = float(columns[0])
				row_adc = [float(columns[i + 1]) for i in range(NUM_CHANNELS_TOTAL)]
			except ValueError:
				continue
			
			# If runtime jumps backwards by more than a second, treat it as a
			# new segment and offset all subsequent runtimes while parsing.
			if last_raw_time is not None and (raw_time - last_raw_time) < -1.0 and last_adjusted_time is not None:
				runtime_offset += last_adjusted_time

			adjusted_time = raw_time + runtime_offset
			time_values.append(adjusted_time)
			for i in range(NUM_CHANNELS_TOTAL):
				adc_values[i].append(row_adc[i])

			last_raw_time = raw_time
			last_adjusted_time = adjusted_time

	return time_values, adc_values


def _build_series_definitions(config):
	series = []

	for idx in range(0, ADC0_CHANNEL_VOLTAGE_END):
		ch = idx + 1
		label = _safe_channel_label(config["ADC0"][f"channel{ch}"]["label"], f"ADC0 CH{ch}")
		series.append(
			{
				"index": idx,
				"label": label,
				"group": "ADC0 Voltage",
				"axis": "voltage",
			}
		)

	for idx in range(ADC0_CHANNEL_VOLTAGE_END, ADC0_CHANNEL_CURRENT_END):
		ch = idx + 1
		label = _safe_channel_label(config["ADC0"][f"channel{ch}"]["label"], f"ADC0 CH{ch}")
		series.append(
			{
				"index": idx,
				"label": label,
				"group": "ADC0 Current",
				"axis": "current",
			}
		)

	for idx in range(ADC0_CHANNEL_CURRENT_END, ADC1_CHANNEL_VOLTAGE_END):
		ch = idx + 1 - ADC0_CHANNEL_CURRENT_END
		label = _safe_channel_label(config["ADC1"][f"channel{ch}"]["label"], f"ADC1 CH{ch}")
		series.append(
			{
				"index": idx,
				"label": label,
				"group": "ADC1 Voltage",
				"axis": "voltage",
			}
		)

	for idx in range(ADC1_CHANNEL_VOLTAGE_END, ADC1_CHANNEL_CURRENT_END):
		ch = idx + 1 - ADC0_CHANNEL_CURRENT_END
		label = _safe_channel_label(config["ADC1"][f"channel{ch}"]["label"], f"ADC1 CH{ch}")
		series.append(
			{
				"index": idx,
				"label": label,
				"group": "ADC1 Current",
				"axis": "current",
			}
		)

	return series


class Graph2App(ctk.CTk):
	def __init__(self, filepath, configfile, live=False):
		super().__init__()
		self.title("Surtr Graph Viewer")
		self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
		self.minsize(1100, 700)

		self.filepath = filepath
		self.configfile = configfile
		self.live = live
		self.job_id = None

		self.config_data = json.load(open(self.configfile, "r", encoding="utf-8"))
		self.series_definitions = _build_series_definitions(self.config_data)
		self.toggle_vars = {}

		self._build_layout()
		self._create_toggles()
		self._draw_plot()
		self.protocol("WM_DELETE_WINDOW", self._on_close)

		if self.live:
			self._schedule_refresh()

	def _build_layout(self):
		self.grid_columnconfigure(1, weight=1)
		self.grid_rowconfigure(1, weight=1)

		self.header = ctk.CTkFrame(self)
		self.header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=12, pady=(12, 6))
		self.header.grid_columnconfigure(1, weight=1)

		self.title_label = ctk.CTkLabel(
			self.header,
			text="Surtr ADC Plotter",
			font=DEFAULT_FONT_BOLD,
		)
		self.title_label.grid(row=0, column=0, padx=8, pady=8, sticky="w")

		self.mode_label = ctk.CTkLabel(
			self.header,
			text="Live Mode" if self.live else "Static Mode",
			font=DEFAULT_FONT,
		)
		self.mode_label.grid(row=0, column=1, padx=8, pady=8, sticky="e")

		self.sidebar = ctk.CTkScrollableFrame(self, width=290, label_text="Enable / Disable Readings")
		self.sidebar.grid(row=1, column=0, sticky="nsew", padx=(12, 6), pady=(6, 12))
		self.sidebar.grid_columnconfigure(0, weight=1)

		self.content = ctk.CTkFrame(self)
		self.content.grid(row=1, column=1, sticky="nsew", padx=(6, 12), pady=(6, 12))
		self.content.grid_columnconfigure(0, weight=1)
		self.content.grid_rowconfigure(0, weight=1)

		self.figure = Figure(figsize=(11, 6), dpi=100)
		self.ax_voltage = self.figure.add_subplot(1, 2, 1)
		self.ax_current = self.figure.add_subplot(1, 2, 2)
		self.figure.subplots_adjust(left=0.07, right=0.98, bottom=0.12, top=0.92, wspace=0.24)

		self.canvas = FigureCanvasTkAgg(self.figure, self.content)
		self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew", padx=8, pady=(8, 0))

		self.toolbar = NavigationToolbar2Tk(self.canvas, self.content, pack_toolbar=False)
		self.toolbar.update()
		self.toolbar.grid(row=1, column=0, sticky="ew", padx=8, pady=(6, 8))

		self.controls = ctk.CTkFrame(self.sidebar, fg_color="transparent")
		self.controls.grid(row=0, column=0, sticky="ew", padx=2, pady=2)
		self.controls.grid_columnconfigure(0, weight=1)

		self.refresh_button = ctk.CTkButton(
			self.header,
			text="Refresh Now",
			command=self._draw_plot,
			font=DEFAULT_FONT,
			width=120,
			corner_radius=0,
		)
		self.refresh_button.grid(row=0, column=2, padx=8, pady=8, sticky="e")

		self.file_button = ctk.CTkButton(
			self.header,
			text="Open CSV",
			command=self._pick_new_csv,
			font=DEFAULT_FONT,
			width=120,
			corner_radius=0,
		)
		self.file_button.grid(row=0, column=3, padx=(0, 8), pady=8, sticky="e")

	def _create_toggles(self):
		groups = {}
		for definition in self.series_definitions:
			groups.setdefault(definition["group"], []).append(definition)

		row = 0
		for group_name, definitions in groups.items():
			group_label = ctk.CTkLabel(self.controls, text=group_name, font=DEFAULT_FONT_BOLD)
			group_label.grid(row=row, column=0, sticky="w", padx=6, pady=(10, 4))
			row += 1

			for definition in definitions:
				key = definition["index"]
				var = ctk.BooleanVar(value=True)
				self.toggle_vars[key] = var
				checkbox = ctk.CTkCheckBox(
					self.controls,
					text=definition["label"],
					variable=var,
					command=self._draw_plot,
					font=("IBM Plex Mono", 13),
				)
				checkbox.grid(row=row, column=0, sticky="w", padx=12, pady=3)
				row += 1

	def _pick_new_csv(self):
		new_path = filedialog.askopenfilename(
			title="Choose CSV file",
			filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
		)
		if new_path:
			self.filepath = new_path
			self._draw_plot()

	def _plot_series(self, time_values, adc_values):
		self.ax_voltage.clear()
		self.ax_current.clear()

		self.ax_voltage.set_xlabel("Time (s)")
		self.ax_voltage.set_ylabel("Voltage")
		self.ax_current.set_xlabel("Time (s)")
		self.ax_current.set_ylabel("Current")

		self.ax_voltage.grid(True, linestyle="--", linewidth=0.5, alpha=0.45)
		self.ax_current.grid(True, linestyle="--", linewidth=0.5, alpha=0.45)

		for i, definition in enumerate(self.series_definitions):
			channel_idx = definition["index"]
			if channel_idx not in self.toggle_vars or not self.toggle_vars[channel_idx].get():
				continue

			if channel_idx >= len(adc_values) or len(adc_values[channel_idx]) != len(time_values):
				continue

			target_axis = self.ax_voltage if definition["axis"] == "voltage" else self.ax_current
			target_axis.plot(
				time_values,
				adc_values[channel_idx],
				label=definition["label"],
				linewidth=1.8,
				alpha=0.95,
			)

		if self.ax_voltage.has_data():
			self.ax_voltage.legend(loc="best", fontsize=8, framealpha=0.8)
		if self.ax_current.has_data():
			self.ax_current.legend(loc="best", fontsize=8, framealpha=0.8)

	def _draw_plot(self):
		try:
			time_values, adc_values = _read_csv(self.filepath)
			self._plot_series(time_values, adc_values)
			self.canvas.draw_idle()
		except Exception as exc:
			print(f"Graph2 plot refresh failed: {exc}")

	def _schedule_refresh(self):
		self.job_id = self.after(PLOT_REFRESH_MS, self._live_refresh)

	def _live_refresh(self):
		self._draw_plot()
		if self.live:
			self._schedule_refresh()

	def _on_close(self):
		self.live = False
		if self.job_id is not None:
			self.after_cancel(self.job_id)
			self.job_id = None
		self.destroy()


def plot_adc_graph_static(filepath, configfile):
	app = Graph2App(filepath, configfile, live=False)
	app.mainloop()


def plot_adc_graph_live(filepath, configfile):
	app = Graph2App(filepath, configfile, live=True)
	app.mainloop()


if __name__ == "__main__":
	if len(sys.argv) < 3:
		print("Usage: graph2.py <csv.file> <json.config> [--live]")
		sys.exit(1)

	live_mode = len(sys.argv) > 3 and sys.argv[3] == "--live"
	if live_mode:
		plot_adc_graph_live(sys.argv[1], sys.argv[2])
	else:
		plot_adc_graph_static(sys.argv[1], sys.argv[2])
