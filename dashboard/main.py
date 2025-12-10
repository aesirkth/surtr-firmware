from parser import SurtrParser
import sys
import time
from widgets import TextLastValue, TimeLastValue
import tkinter as tk
from tkinter import font
import traceback

#! The labels should be based on a sensor config file in the future!

#! Right, so this is where we send the messages, which get picked up and decoded by Surtr.
#! Ideally, we would want a nicer GUI for this, but also an automatic sequence
#! It looks like the scaffolding is here, so I should be able to easily buld upon it.
#! Maybe the first test could simply be to call "send_message" from a new button click.
#! Then, I can try to get that button to trigger a sequence.
#! Lastly, I can incorporate multiple outputs into this sequence.
#! The final thing would be to receive messages form the GCS. But honestly, we don't need brage for that (I think)
#! because there is a transceiver already in the plastic box. But the transceiver should send to GCS, not som laptop (unless we are debugging).

# Initialize the parser with the COM port as an argument.
if len(sys.argv) > 1: # sys.argv[0] is the path
    parser = SurtrParser(sys.argv[1])
else:
    parser = SurtrParser(None)

root = tk.Tk()
large_font = font.Font(size=14)
root.option_add("*Font", large_font)

switch_panel = tk.Frame(root)
ADC0_panel = tk.Frame(root)
ADC1_panel = tk.Frame(root)
send_panel = tk.Frame(root)



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

status_label = tk.Label(root, text="")
status_label.grid(row=0, column=2, padx=5, sticky="ew")

ADC0_label = tk.Label(ADC0_panel, text="ADC readings 1")
ADC0_label.grid(row=0, column=0, columnspan=2, padx=20, pady=10)
ADC1_label = tk.Label(ADC1_panel, text="ADC readings 2")
ADC1_label.grid(row=0, column=0, columnspan=2, padx=20, pady=10)

# First ADC #! What about the zeroth channel?
ADC10 = TextLastValue(ADC0_panel, "1: ", lambda: get_display_data(parser, "value10", lambda x: 69 * (x - v_start) / (v_end - v_start))) #! I'm guessing these are for the thermocouples
ADC20 = TextLastValue(ADC0_panel, "2: ", lambda: get_display_data(parser, "value20", lambda x: 69 * (x - v_start) / (v_end - v_start))) #! I'm guessing these are for the thermocouples
ADC30 = TextLastValue(ADC0_panel, "3: ", lambda: get_display_data(parser, "value30", lambda x: 69 * (x - v_start) / (v_end - v_start))) #! I'm guessing these are for the thermocouples
ADC40 = TextLastValue(ADC0_panel, "4: ", lambda: get_display_data(parser, "value40", lambda x: 69 * (x - v_start) / (v_end - v_start))) #! I'm guessing these are for the thermocouples
ADC50 = TextLastValue(ADC0_panel, "5: ", lambda: get_display_data(parser, "value50", lambda x: 69 * (x - v_start) / (v_end - v_start)))
ADC60 = TextLastValue(ADC0_panel, "6: ", lambda: get_display_data(parser, "value60", lambda x: x))
ADC70 = TextLastValue(ADC0_panel, "7: ", lambda: get_display_data(parser, "value70", lambda x: 69 * (x - v_start) / (v_end - v_start)))
ADC80 = TextLastValue(ADC0_panel, "8: ", lambda: get_display_data(parser, "value80", lambda x: 250 * (x - c_start) / (c_end - c_start)))
ADC90 = TextLastValue(ADC0_panel, "9: ", lambda: get_display_data(parser, "value90", lambda x: 250 * (x - c_start) / (c_end - c_start)))
ADC100 = TextLastValue(ADC0_panel, "10: ", lambda: get_display_data(parser, "value100", lambda x: 100 * (x - c_start) / (c_end - c_start)))
ADC110 = TextLastValue(ADC0_panel, "11: ", lambda: get_display_data(parser, "value110", lambda x: 100 * (x - c_start) / (c_end - c_start)))

# Second ADC
ADC11 = TextLastValue(ADC1_panel, "1: ", lambda: get_display_data(parser, "value11", lambda x: 200 * (x - v_start) / (v_end - v_start))) #! I'm guessing these are for the thermocouples
ADC21 = TextLastValue(ADC1_panel, "2: ", lambda: get_display_data(parser, "value21", lambda x: 200* (x - v_start) / (v_end - v_start))) #! I'm guessing these are for the thermocouples
ADC31 = TextLastValue(ADC1_panel, "3: ", lambda: get_display_data(parser, "value31", lambda x: 200* (x - v_start) / (v_end - v_start))) #! I'm guessing these are for the thermocouples
ADC41 = TextLastValue(ADC1_panel, "4: ", lambda: get_display_data(parser, "value41", lambda x: 200* (x - v_start) / (v_end - v_start))) #! I'm guessing these are for the thermocouples
ADC51 = TextLastValue(ADC1_panel, "5: ", lambda: get_display_data(parser, "value51", lambda x: 69 * (x - v_start) / (v_end - v_start)))
ADC61 = TextLastValue(ADC1_panel, "6: ", lambda: get_display_data(parser, "value61", lambda x: 69 * (x - v_start) / (v_end - v_start)))
ADC71 = TextLastValue(ADC1_panel, "7: ", lambda: get_display_data(parser, "value71", lambda x: 69 * (x - v_start) / (v_end - v_start)))
ADC81 = TextLastValue(ADC1_panel, "8: ", lambda: get_display_data(parser, "value81", lambda x: 250 * (x - c_start) / (c_end - c_start)))
ADC91 = TextLastValue(ADC1_panel, "9: ", lambda: get_display_data(parser, "value91", lambda x: 250 * (x - c_start) / (c_end - c_start)))
ADC101 = TextLastValue(ADC1_panel, "10: ", lambda: get_display_data(parser, "value101", lambda x: 100 * (x - c_start) / (c_end - c_start)))
ADC111 = TextLastValue(ADC1_panel, "11: ", lambda: get_display_data(parser, "value111", lambda x: 100 * (x - c_start) / (c_end - c_start)))

ADC10.grid(row=1,column=0, padx=20, pady=10, sticky="w")
ADC20.grid(row=1,column=1, padx=20, pady=10, sticky="w")
ADC30.grid(row=2,column=0, padx=20, pady=10, sticky="w")
ADC40.grid(row=2,column=1, padx=20, pady=10, sticky="w")
ADC50.grid(row=3,column=0, padx=20, pady=10, sticky="w")
ADC60.grid(row=3,column=1, padx=20, pady=10, sticky="w")
ADC70.grid(row=4,column=0, padx=20, pady=10, sticky="w")
ADC80.grid(row=4,column=1, padx=20, pady=10, sticky="w")
ADC90.grid(row=5,column=0, padx=20, pady=10, sticky="w")
ADC100.grid(row=5,column=1, padx=20, pady=10, sticky="w")
ADC110.grid(row=6,column=0, padx=20, pady=10, sticky="w")

ADC11.grid(row=1,column=0, padx=20, pady=10, sticky="w")
ADC21.grid(row=1,column=1, padx=20, pady=10, sticky="w")
ADC31.grid(row=2,column=0, padx=20, pady=10, sticky="w")
ADC41.grid(row=2,column=1, padx=20, pady=10, sticky="w")
ADC51.grid(row=3,column=0, padx=20, pady=10, sticky="w")
ADC61.grid(row=3,column=1, padx=20, pady=10, sticky="w")
ADC71.grid(row=4,column=0, padx=20, pady=10, sticky="w")
ADC81.grid(row=4,column=1, padx=20, pady=10, sticky="w")
ADC91.grid(row=5,column=0, padx=20, pady=10, sticky="w")
ADC101.grid(row=5,column=1, padx=20, pady=10, sticky="w")
ADC111.grid(row=6,column=0, padx=20, pady=10, sticky="w")

# Switch status indicators
switch_status_frame = tk.LabelFrame(switch_panel, text="Switch States")
num_switch_status = 8
for switch_id in range(1, num_switch_status + 1):
    row = (switch_id - 1) // 2
    col = (switch_id - 1) % 2
    label = TextLastValue(
        switch_status_frame,
        f"sw{switch_id}: ",
        lambda: get_display_data(parser, f"sw{switch_id}"),
        padx=20,
        pady=10
    )
    label.grid(row=row, column=col, sticky="w")
switch_status_frame.grid(row=0, column=0, columnspan=2, sticky="ew")

# Stepper status indicators
step_status_frame = tk.LabelFrame(switch_panel, text="Stepper States")
num_step_status = 3
for step_id in range(1, num_step_status + 1):
    row = (step_id - 1) // 2
    col = (step_id - 1) % 2
    label = TextLastValue(
        step_status_frame,
        f"step{step_id}: ",
        lambda: get_display_data(parser, f"step{step_id}"),
        padx=20,
        pady=10
    )
    label.grid(row=row, column=col, sticky="w")
step_status_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))



# ACTUATION

# Parser command wrapper with error handling
def execute_parser_command(action):
    if not parser.connected:
        status_label.config(text="not connected")
        return
    try:
        action()
    except Exception as e:
        traceback.print_exc()
        print(e)
        status_label.config(text="error")
    else:
        status_label.config(text="ok")

def send_switch_command(switch_id, state):
    execute_parser_command(lambda: parser.toggle_switch(switch_id, state))

def send_ignition_command():
    # The ignition password is currently hardcoded to 0.
    execute_parser_command(lambda: parser.ignite(0))

def send_step_command(stepper_id, delta):
    execute_parser_command(lambda: parser.motor_step(stepper_id, int(delta)))

send_panel.grid_columnconfigure(0, weight=1)
send_panel.grid_columnconfigure(1, weight=1)

# Switches
switch_frame = tk.LabelFrame(send_panel, text="Switches")
num_switches = 8
switches_per_column = 4
for switch_id in range(1, num_switches + 1):
    row = (switch_id - 1) % switches_per_column
    col = (switch_id - 1) // switches_per_column
    tk.Label(switch_frame, text=f"SW {switch_id}").grid(row=row, column=col*3+0, padx=5, pady=2, sticky="w")
    tk.Button(switch_frame, text="On", command=lambda i=switch_id: send_switch_command(i, True)).grid(row=row, column=col*3+1, padx=5, pady=2, sticky="ew")
    tk.Button(switch_frame, text="Off", command=lambda i=switch_id: send_switch_command(i, False)).grid(row=row, column=col*3+2, padx=5, pady=2, sticky="ew")
switch_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=(10, 0))

# Steppers
step_frame = tk.LabelFrame(send_panel, text="Steppers")
for step_id in range(1, 4):
    row = step_id - 1
    tk.Label(step_frame, text=f"Stepper {step_id}").grid(row=row, column=0, padx=5, pady=4, sticky="w")
    entry = tk.Entry(step_frame, width=8)
    entry.grid(row=row, column=1, padx=5, pady=4, sticky="ew")
    tk.Button(step_frame, text="Send", command=lambda i=step_id, e=entry: send_step_command(i, e.get())).grid(row=row, column=2, padx=5, pady=4, sticky="ew")
step_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=(10, 0))

# Ignition
ignition_frame = tk.LabelFrame(send_panel, text="Ignition")
tk.Button(ignition_frame, text="Ignite", command=send_ignition_command).pack(fill="x", padx=10, pady=5)
ignition_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=30, pady=10)

time = TimeLastValue(root, "time: ", lambda: get_display_data(parser, "us_since_boot", lambda x: x / 1e6))
time.grid(row=0, column=0)

ADC0_panel.grid(row=1, column=0, padx=30, pady=10)
ADC1_panel.grid(row=1, column=1, padx=30, pady=10)
switch_panel.grid(row=1, column=2, padx=30, pady=10)
send_panel.grid(row=2, column=0, columnspan=2, pady=20)
root.mainloop() # GUI main loop.


# time.sleep(3)
