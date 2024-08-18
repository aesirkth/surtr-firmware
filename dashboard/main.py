from parser import SurtrParser
import sys
import time
from widgets import TextLastValue, TimeLastValue
import tkinter as tk
from tkinter import font
import traceback
parser = SurtrParser(sys.argv[1])

root = tk.Tk()
large_font = font.Font(size=20)
root.option_add("*Font", large_font)

switch_panel = tk.Frame(root)
pressure_panel = tk.Frame(root)
send_panel = tk.Frame(root)


switch1 = TextLastValue(switch_panel, "sw1: ", parser.data["sw1"], padx=30, pady=10)
switch2 = TextLastValue(switch_panel, "sw2: ", parser.data["sw2"], padx=30, pady=10)
switch3 = TextLastValue(switch_panel, "sw3: ", parser.data["sw3"], padx=30, pady=10)
switch4 = TextLastValue(switch_panel, "sw4: ", parser.data["sw4"], padx=30, pady=10)
step1 = TextLastValue(switch_panel, "step1: ", parser.data["step1"], padx=30, pady=10)
step2 = TextLastValue(switch_panel, "step2: ", parser.data["step2"], padx=30, pady=10)

switch1.grid(row=0,column=0)
switch2.grid(row=0,column=1)
switch3.grid(row=1,column=0)
switch4.grid(row=1,column=1)
step1.grid(row=2, column=0, columnspan=2)
step2.grid(row=3, column=0, columnspan=2)
pt1 = TextLastValue(pressure_panel, "pt1: ", parser.data["value01"])
pt2 = TextLastValue(pressure_panel, "pt2: ", parser.data["value11"])
pt3 = TextLastValue(pressure_panel, "pt3: ", parser.data["value21"])
pt4 = TextLastValue(pressure_panel, "pt4: ", parser.data["value31"])
pt5 = TextLastValue(pressure_panel, "pt5: ", parser.data["value41"])
pt6 = TextLastValue(pressure_panel, "pt6: ", parser.data["value51"])
pt7 = TextLastValue(pressure_panel, "pt7: ", parser.data["value61"])
pt8 = TextLastValue(pressure_panel, "pt8: ", parser.data["value71"])

pt1.grid(row=0,column=0, padx=20, pady=10)
pt2.grid(row=0,column=1, padx=20, pady=10)
pt3.grid(row=1,column=0, padx=20, pady=10)
pt4.grid(row=1,column=1, padx=20, pady=10)
pt5.grid(row=2,column=0, padx=20, pady=10)
pt6.grid(row=2,column=1, padx=20, pady=10)
pt7.grid(row=3,column=0, padx=20, pady=10)
pt8.grid(row=3,column=1, padx=20, pady=10)

def send_message():
    user_input = input_field.get()
    error = False
    try:
        args = user_input.split(" ")
        if args[0] == "sw":
            id = int(args[1])
            state = False
            if args[2] == "on":
                state = True
            elif args[2] == "off":
                state = False
            else:
                raise Exception()
            parser.toggle_switch(id, state)

        elif args[0] == "ignition":
            key = int(args[1])
            parser.ignite(key)

        elif args[0] == "step":
            id = int(args[1])
            delta = int(args[2])
            parser.motor_step(id, delta)
        else:
            error = True
    except Exception as e:
        traceback.print_exc()
        print(e)
        error = True

    if error:
        status_label.config(text="error")
    else:
        status_label.config(text="ok")
    input_field.delete(0, tk.END)  # Clear the input field after sending

input_field = tk.Entry(send_panel)
input_field.bind("<Return>", lambda event: send_message())
send_button = tk.Button(send_panel, text="Send", command=send_message)
status_label = tk.Label(send_panel, text="")

input_field.grid(row=0, column=0, padx=5)
send_button.grid(row=0, column=1, padx=5)
status_label.grid(row=0, column=2, padx=5)

time = TimeLastValue(root, "time: ", parser.data["sw1"])

time.grid(row=0, column=0)
pressure_panel.grid(row=1, column=0, padx=30, pady=10)
switch_panel.grid(row=1, column=1, padx=30, pady=10)
send_panel.grid(row=2, column=0, columnspan=2, pady=20)

root.mainloop()
