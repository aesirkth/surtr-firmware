from parser import SurtrParser
import sys
import time
import json
import os
from widgets import TextLastValue, TimeLastValue
import tkinter as tk
import customtkinter as ctk
from tkinter import filedialog
import traceback

# Excuse the vibe coding. Please don't judge me.

# Initialize the parser with the COM port as an argument.
if len(sys.argv) > 1: # sys.argv[0] is the path
    parser = SurtrParser(sys.argv[1])
else:
    parser = SurtrParser(None)

# Load IBM Plex Mono font using customtkinter
font_path = os.path.join(os.path.dirname(__file__), "resources", "IBMPlexMono-Regular.ttf")
ctk.FontManager.load_font(font_path)
font_name = "IBM Plex Mono"
default_font = (font_name, 15)

# Set appearance mode and color theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

root = ctk.CTk()
root.title("Surtr Dashboard")
# Set minimum window size to prevent panel overlap
root.minsize(900, 600)

ADC0_panel = ctk.CTkFrame(root, border_width=1)
ADC1_panel = ctk.CTkFrame(root, border_width=1)
send_panel = ctk.CTkFrame(root, border_width=1)

# ADC panel titles
ADC0_title = ctk.CTkLabel(ADC0_panel, text="ADC0 readings", font=(font_name, 14, "bold"))
ADC0_title.grid(row=0, column=0, columnspan=4, padx=16, pady=8)
ADC1_title = ctk.CTkLabel(ADC1_panel, text="ADC1 readings", font=(font_name, 14, "bold"))
ADC1_title.grid(row=0, column=0, columnspan=4, padx=16, pady=8)

# SENSORS

# Wrapper that can handle an unconnected parser
def get_display_data(parser, id_str, conversion=lambda x: x, unconnected_value = "-"):
    if parser.connected:
        try:
            return conversion(parser.data[id_str][1][-1]) # Take the latest value #! Why the [1] in the middle?
        except:
            pass
    return unconnected_value

# What is "v" and "c" in the following code?
v_start = 0.9
v_end = 4.5
c_start = 4
c_end = 20

# Config manager class
class ConfigManager:
    def __init__(self, initial_path):
        self._path = initial_path
        self._config = self._load_config(initial_path)
    
    def _load_config(self, path):
        """Load ADC config from JSON file"""
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: ADC config file not found at {path}. Using default values.")
            default_config = {
                "ADC0": {f"channel{i}": {"scale": 1.0, "label": ""} for i in range(1, 13)},
                "ADC1": {f"channel{i}": {"scale": 1.0, "label": ""} for i in range(1, 13)}
            }
            default_config["ADC0"]["range_label"] = ""
            default_config["ADC1"]["range_label"] = ""
            return default_config
        except json.JSONDecodeError as e:
            print(f"Error: Failed to parse ADC config file: {e}. Using default values.")
            default_config = {
                "ADC0": {f"channel{i}": {"scale": 1.0, "label": ""} for i in range(1, 13)},
                "ADC1": {f"channel{i}": {"scale": 1.0, "label": ""} for i in range(1, 13)}
            }
            default_config["ADC0"]["range_label"] = ""
            default_config["ADC1"]["range_label"] = ""
            return default_config
    
    def get_config(self):
        """Get the current config"""
        return self._config
    
    def get_path(self):
        """Get the current config path"""
        return self._path
    
    def load_from_path(self, path):
        """Load config from a new path"""
        self._path = path
        self._config = self._load_config(path)
        print(f"Config loaded from: {path}")

# Initialize config manager
initial_config_path = os.path.join(os.path.dirname(__file__), "adc_config.json")
config_manager = ConfigManager(initial_config_path)

# Helper function to build label text from channel number and config
def build_channel_label(channel_num, label_text):
    """Build label string: 'N. label: ' if label exists, 'N: ' if empty"""
    if label_text:
        return f"{channel_num}. {label_text}: "
    else:
        return f"{channel_num}: "

# Config import panel at the top
config_panel = ctk.CTkFrame(root, fg_color="transparent")
config_path_var = tk.StringVar(value=config_manager.get_path())
config_path_entry = ctk.CTkEntry(config_panel, textvariable=config_path_var, state="readonly", width=400, font=default_font)
config_path_entry.grid(row=0, column=1, padx=4, pady=4, sticky="ew")
config_panel.grid_columnconfigure(1, weight=1)

# Store ADC widgets for refreshing labels (label_widget, value_widget, adc_name, channel_num)
adc_widgets = []
# Store range label widgets for refreshing
range_label_widgets = []

def refresh_adc_labels():
    """Update all ADC widget labels and range labels from the current config"""
    adc_config = config_manager.get_config()
    for label_widget, value_widget, adc_name, channel_num in adc_widgets:
        channel_key = f"channel{channel_num}"
        label_text = adc_config[adc_name][channel_key]["label"]
        label_widget.configure(text=build_channel_label(channel_num, label_text))
    # Update range labels with equal row counts
    range_text_0 = adc_config["ADC0"].get("range_label", "")
    range_text_1 = adc_config["ADC1"].get("range_label", "")
    
    # Count newlines in each label
    newlines_0 = range_text_0.count('\n')
    newlines_1 = range_text_1.count('\n')
    
    # Add newlines to the shorter label to match the longer one
    if newlines_0 < newlines_1:
        range_text_0 += '\n' * (newlines_1 - newlines_0)
    elif newlines_1 < newlines_0:
        range_text_1 += '\n' * (newlines_0 - newlines_1)
    
    # Update the range label widgets
    for range_label_widget, adc_name in range_label_widgets:
        if adc_name == "ADC0":
            range_label_widget.configure(text=range_text_0)
        else:
            range_label_widget.configure(text=range_text_1)

def import_config():
    """Open file dialog to select and load a new config file"""
    current_path = config_manager.get_path()
    file_path = filedialog.askopenfilename(
        title="Select ADC Config File",
        filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        initialdir=os.path.dirname(current_path) if os.path.exists(current_path) else os.path.dirname(__file__)
    )
    if file_path:
        config_manager.load_from_path(file_path)
        config_path_var.set(config_manager.get_path())
        refresh_adc_labels()

import_button = ctk.CTkButton(config_panel, text="Import Config", command=import_config, font=default_font, corner_radius=0)
import_button.grid(row=0, column=0, padx=4, pady=4)
config_panel.grid(row=0, column=0, columnspan=2, sticky="ew", padx=8, pady=4)

status_label = ctk.CTkLabel(root, text="", font=default_font)
status_label.grid(row=1, column=1, padx=4, sticky="ew")

# Helper function to create ADC widget pair (label + value) and store reference
def create_adc_widget(panel, channel_num, adc_name, value_id, use_c_start=False):
    """Create label and value widgets for an ADC channel and store them for later updates"""
    adc_config = config_manager.get_config()
    channel_key = f"channel{channel_num}"
    label_text = adc_config[adc_name][channel_key]["label"]
    
    if use_c_start:
        conversion = lambda x: config_manager.get_config()[adc_name][channel_key]["scale"] * (x - c_start) / (c_end - c_start)
    else:
        conversion = lambda x: config_manager.get_config()[adc_name][channel_key]["scale"] * (x - v_start) / (v_end - v_start)
    
    # Create separate label widget
    label_widget = ctk.CTkLabel(panel, text=build_channel_label(channel_num, label_text), font=default_font)
    
    # Create value widget (TextLastValue with empty text prefix)
    value_widget = TextLastValue(panel, "", lambda: get_display_data(parser, value_id, conversion), font=default_font)
    
    adc_widgets.append((label_widget, value_widget, adc_name, channel_num))
    return label_widget, value_widget

# First ADC #! What about the zeroth channel?
ADC10_label, ADC10_value = create_adc_widget(ADC0_panel, 1, "ADC0", "value10") #! I'm guessing these are for the thermocouples
ADC20_label, ADC20_value = create_adc_widget(ADC0_panel, 2, "ADC0", "value20") #! I'm guessing these are for the thermocouples
ADC30_label, ADC30_value = create_adc_widget(ADC0_panel, 3, "ADC0", "value30") #! I'm guessing these are for the thermocouples
ADC40_label, ADC40_value = create_adc_widget(ADC0_panel, 4, "ADC0", "value40") #! I'm guessing these are for the thermocouples
ADC50_label, ADC50_value = create_adc_widget(ADC0_panel, 5, "ADC0", "value50")
ADC60_label, ADC60_value = create_adc_widget(ADC0_panel, 6, "ADC0", "value60")
ADC70_label, ADC70_value = create_adc_widget(ADC0_panel, 7, "ADC0", "value70")
ADC80_label, ADC80_value = create_adc_widget(ADC0_panel, 8, "ADC0", "value80", use_c_start=True) # Current sensing
ADC90_label, ADC90_value = create_adc_widget(ADC0_panel, 9, "ADC0", "value90", use_c_start=True) # Current sensing
ADC100_label, ADC100_value = create_adc_widget(ADC0_panel, 10, "ADC0", "value100", use_c_start=True) # Current sensing
ADC110_label, ADC110_value = create_adc_widget(ADC0_panel, 11, "ADC0", "value110", use_c_start=True) # Current sensing

# Second ADC
ADC11_label, ADC11_value = create_adc_widget(ADC1_panel, 1, "ADC1", "value11") #! I'm guessing these are for the thermocouples
ADC21_label, ADC21_value = create_adc_widget(ADC1_panel, 2, "ADC1", "value21") #! I'm guessing these are for the thermocouples
ADC31_label, ADC31_value = create_adc_widget(ADC1_panel, 3, "ADC1", "value31") #! I'm guessing these are for the thermocouples
ADC41_label, ADC41_value = create_adc_widget(ADC1_panel, 4, "ADC1", "value41") #! I'm guessing these are for the thermocouples
ADC51_label, ADC51_value = create_adc_widget(ADC1_panel, 5, "ADC1", "value51")
ADC61_label, ADC61_value = create_adc_widget(ADC1_panel, 6, "ADC1", "value61")
ADC71_label, ADC71_value = create_adc_widget(ADC1_panel, 7, "ADC1", "value71")
ADC81_label, ADC81_value = create_adc_widget(ADC1_panel, 8, "ADC1", "value91", use_c_start=True) # Current sensing. OBS: Flipped from 81 to 91 due to weird board wiring
ADC91_label, ADC91_value = create_adc_widget(ADC1_panel, 9, "ADC1", "value81", use_c_start=True) # Current sensing. OBS: Flipped from 91 to 81 due to weird board wiring
ADC101_label, ADC101_value = create_adc_widget(ADC1_panel, 10, "ADC1", "value101", use_c_start=True) # Current sensing. 
ADC111_label, ADC111_value = create_adc_widget(ADC1_panel, 11, "ADC1", "value111", use_c_start=True) # Current sensing. 

# Grid layout: label | value | label | value (2 channels per row, 4 columns per row)
# ADC0
ADC10_label.grid(row=1, column=0, padx=4, pady=4, sticky="w")
ADC10_value.grid(row=1, column=1, padx=4, pady=4, sticky="w")
ADC20_label.grid(row=1, column=2, padx=4, pady=4, sticky="w")
ADC20_value.grid(row=1, column=3, padx=4, pady=4, sticky="w")

ADC30_label.grid(row=2, column=0, padx=4, pady=4, sticky="w")
ADC30_value.grid(row=2, column=1, padx=4, pady=4, sticky="w")
ADC40_label.grid(row=2, column=2, padx=4, pady=4, sticky="w")
ADC40_value.grid(row=2, column=3, padx=4, pady=4, sticky="w")

ADC50_label.grid(row=3, column=0, padx=4, pady=4, sticky="w")
ADC50_value.grid(row=3, column=1, padx=4, pady=4, sticky="w")
ADC60_label.grid(row=3, column=2, padx=4, pady=4, sticky="w")
ADC60_value.grid(row=3, column=3, padx=4, pady=4, sticky="w")

ADC70_label.grid(row=4, column=0, padx=4, pady=4, sticky="w")
ADC70_value.grid(row=4, column=1, padx=4, pady=4, sticky="w")
ADC80_label.grid(row=4, column=2, padx=4, pady=4, sticky="w")
ADC80_value.grid(row=4, column=3, padx=4, pady=4, sticky="w")

ADC90_label.grid(row=5, column=0, padx=4, pady=4, sticky="w")
ADC90_value.grid(row=5, column=1, padx=4, pady=4, sticky="w")
ADC100_label.grid(row=5, column=2, padx=4, pady=4, sticky="w")
ADC100_value.grid(row=5, column=3, padx=4, pady=4, sticky="w")

ADC110_label.grid(row=6, column=0, padx=4, pady=4, sticky="w")
ADC110_value.grid(row=6, column=1, padx=4, pady=4, sticky="w")

# Pressure transducer range labels
adc_config = config_manager.get_config()
range_text_0 = adc_config["ADC0"].get("range_label", "")
range_text_1 = adc_config["ADC1"].get("range_label", "")

# Count newlines in each label
newlines_0 = range_text_0.count('\n')
newlines_1 = range_text_1.count('\n')

# Add newlines to the shorter label to match the longer one
if newlines_0 < newlines_1:
    range_text_0 += '\n' * (newlines_1 - newlines_0)
elif newlines_1 < newlines_0:
    range_text_1 += '\n' * (newlines_0 - newlines_1)

PT_range_label0 = ctk.CTkLabel(ADC0_panel, text=range_text_0, font=default_font, justify="center") #! Rename
PT_range_label0.grid(row=7, column=0, columnspan=4, padx=16, pady=8)
range_label_widgets.append((PT_range_label0, "ADC0"))

# ADC1
ADC11_label.grid(row=1, column=0, padx=4, pady=4, sticky="w")
ADC11_value.grid(row=1, column=1, padx=4, pady=4, sticky="w")
ADC21_label.grid(row=1, column=2, padx=4, pady=4, sticky="w")
ADC21_value.grid(row=1, column=3, padx=4, pady=4, sticky="w")

ADC31_label.grid(row=2, column=0, padx=4, pady=4, sticky="w")
ADC31_value.grid(row=2, column=1, padx=4, pady=4, sticky="w")
ADC41_label.grid(row=2, column=2, padx=4, pady=4, sticky="w")
ADC41_value.grid(row=2, column=3, padx=4, pady=4, sticky="w")

ADC51_label.grid(row=3, column=0, padx=4, pady=4, sticky="w")
ADC51_value.grid(row=3, column=1, padx=4, pady=4, sticky="w")
ADC61_label.grid(row=3, column=2, padx=4, pady=4, sticky="w")
ADC61_value.grid(row=3, column=3, padx=4, pady=4, sticky="w")

ADC71_label.grid(row=4, column=0, padx=4, pady=4, sticky="w")
ADC71_value.grid(row=4, column=1, padx=4, pady=4, sticky="w")
ADC81_label.grid(row=4, column=2, padx=4, pady=4, sticky="w")
ADC81_value.grid(row=4, column=3, padx=4, pady=4, sticky="w")

ADC91_label.grid(row=5, column=0, padx=4, pady=4, sticky="w")
ADC91_value.grid(row=5, column=1, padx=4, pady=4, sticky="w")
ADC101_label.grid(row=5, column=2, padx=4, pady=4, sticky="w")
ADC101_value.grid(row=5, column=3, padx=4, pady=4, sticky="w")

ADC111_label.grid(row=6, column=0, padx=4, pady=4, sticky="w")
ADC111_value.grid(row=6, column=1, padx=4, pady=4, sticky="w")

# Pressure transducer range labels
PT_range_label1 = ctk.CTkLabel(ADC1_panel, text=range_text_1, font=default_font, justify="center")
PT_range_label1.grid(row=7, column=0, columnspan=4, padx=16, pady=8)
range_label_widgets.append((PT_range_label1, "ADC1"))

# Configure ADC panels to have wider value columns (columns 1 and 3)
ADC0_panel.grid_columnconfigure(1, minsize=120)
ADC0_panel.grid_columnconfigure(3, minsize=120)
ADC1_panel.grid_columnconfigure(1, minsize=120)
ADC1_panel.grid_columnconfigure(3, minsize=120)



# ACTUATION

# Parser command wrapper with error handling
def execute_parser_command(action):
    if not parser.connected:
        status_label.configure(text="not connected")
        return
    try:
        action()
    except Exception as e:
        traceback.print_exc()
        print(e)
        status_label.configure(text="error")
    else:
        status_label.configure(text="ok")

def send_switch_command(switch_id, state):
    execute_parser_command(lambda: parser.toggle_switch(switch_id, state))

def send_ignition_command():
    # The ignition password is currently hardcoded to 0.
    execute_parser_command(lambda: parser.ignite(0))

def send_step_command(stepper_id, delta):
    execute_parser_command(lambda: parser.motor_step(stepper_id, int(delta)))

send_panel.grid_columnconfigure(0, weight=0)  # Switches - don't expand
send_panel.grid_columnconfigure(1, weight=0)  # Steppers - don't expand
send_panel.grid_columnconfigure(2, weight=1)  # Ignition - fill remaining space

# Switches
switch_frame = ctk.CTkFrame(send_panel)
switch_title = ctk.CTkLabel(switch_frame, text="Switches", font=(font_name, 14, "bold"))
switch_title.grid(row=0, column=0, columnspan=6, pady=4)
num_switches = 8
switches_per_column = 4
for switch_id in range(1, num_switches + 1):
    row = (switch_id - 1) % switches_per_column + 1  # +1 to account for title
    col = (switch_id - 1) // switches_per_column
    ctk.CTkLabel(switch_frame, text=f"SW {switch_id}", font=default_font).grid(row=row, column=col*3+0, padx=4, pady=2, sticky="w")
    ctk.CTkButton(switch_frame, text="On", command=lambda i=switch_id: send_switch_command(i, True), width=50, font=default_font, corner_radius=0).grid(row=row, column=col*3+1, padx=4, pady=2, sticky="ew")
    ctk.CTkButton(switch_frame, text="Off", command=lambda i=switch_id: send_switch_command(i, False), width=50, font=default_font, corner_radius=0).grid(row=row, column=col*3+2, padx=4, pady=2, sticky="ew")
switch_frame.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)

# Steppers
step_frame = ctk.CTkFrame(send_panel)
step_title = ctk.CTkLabel(step_frame, text="Steppers", font=(font_name, 14, "bold"))
step_title.grid(row=0, column=0, columnspan=3, pady=4)
stepper_entries = []
for step_id in range(1, 4):
    row = step_id  # +1 offset handled by starting at 1
    ctk.CTkLabel(step_frame, text=f"Stepper {step_id}", font=default_font).grid(row=row, column=0, padx=4, pady=3, sticky="w")
    entry = ctk.CTkEntry(step_frame, width=60, font=default_font)
    entry.grid(row=row, column=1, padx=4, pady=3, sticky="ew")
    stepper_entries.append(entry)
    ctk.CTkButton(step_frame, text="Send", command=lambda i=step_id, e=entry: send_step_command(i, e.get()), width=60, font=default_font, corner_radius=0).grid(row=row, column=2, padx=4, pady=3, sticky="ew")
step_frame.grid(row=0, column=1, sticky="nsew", padx=12, pady=12)

# Ignition
ignition_frame = ctk.CTkFrame(send_panel)
ignition_title = ctk.CTkLabel(ignition_frame, text="Ignition", font=(font_name, 14, "bold"))
ignition_title.pack(pady=4)
ctk.CTkButton(ignition_frame, text="Ignite", command=send_ignition_command, width=150, font=default_font, corner_radius=0).pack(fill="x", padx=24, pady=6)
ignition_frame.grid(row=0, column=2, sticky="nsew", padx=12, pady=12)

# Configure root window grid to center content when resized
root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)

time_label = TimeLastValue(root, "time: ", lambda: get_display_data(parser, "us_since_boot", lambda x: x / 1e6), font=default_font)
time_label.grid(row=1, column=0)

ADC0_panel.grid(row=2, column=0, padx=(24, 12), pady=8, sticky="n")
ADC1_panel.grid(row=2, column=1, padx=(12, 24), pady=8, sticky="n")
send_panel.grid(row=3, column=0, columnspan=2, pady=16, padx=24)
root.mainloop() # GUI main loop.


# time.sleep(3)
