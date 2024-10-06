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
pt1 = TextLastValue(pressure_panel, "pt1: ", parser.data["value40"])
v_start = 0.9
v_end = 4.5
c_start = 4
c_end = 20
m2 = TextLastValue(pressure_panel, "m2: ", parser.data["value50"], conversion = lambda x: 69 * (x - v_start) / (v_end - v_start))
m1 = TextLastValue(pressure_panel, "m1: ", parser.data["value60"], conversion = lambda x : 69 * (x - v_start) / (v_end - v_start))
m3 = TextLastValue(pressure_panel, "m3: ", parser.data["value70"], conversion = lambda x : 69 * (x - v_start) / (v_end - v_start))

e2 = TextLastValue(pressure_panel, "e2: ", parser.data["value80"], conversion = lambda x : 250 * (x - c_start) / (c_end - c_start))
e1 = TextLastValue(pressure_panel, "e1: ", parser.data["value90"], conversion = lambda x : 250 * (x - c_start) / (c_end - c_start))
e3 = TextLastValue(pressure_panel, "e3: ", parser.data["value100"], conversion = lambda x : 100 * (x - c_start) / (c_end - c_start))
e4 = TextLastValue(pressure_panel, "e4: ", parser.data["value110"], conversion = lambda x : 100 * (x - c_start) / (c_end - c_start))

# m2 = TextLastValue(pressure_panel, "m2: ", parser.data["value50"], conversion = lambda x: x)
# m1 = TextLastValue(pressure_panel, "m1: ", parser.data["value60"], conversion = lambda x : x)
# m3 = TextLastValue(pressure_panel, "m3: ", parser.data["value70"], conversion = lambda x : x)
# e2 = TextLastValue(pressure_panel, "e2: ", parser.data["value80"], conversion = lambda x : x)
# e1 = TextLastValue(pressure_panel, "e1: ", parser.data["value90"], conversion = lambda x : x)
# e3 = TextLastValue(pressure_panel, "e3: ", parser.data["value100"], conversion = lambda x : x)
# e4 = TextLastValue(pressure_panel, "e4: ", parser.data["value110"], conversion = lambda x : x)


# pt1.grid(row=0,column=0, padx=20, pady=10)
m1.grid(row=0,column=0, padx=20, pady=10)
m2.grid(row=0,column=1, padx=20, pady=10)
m3.grid(row=1,column=0, padx=20, pady=10)
e1.grid(row=3,column=0, padx=20, pady=10)
e2.grid(row=3,column=1, padx=20, pady=10)
e3.grid(row=4,column=0, padx=20, pady=10)
e4.grid(row=4,column=1, padx=20, pady=10)

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

time.grid(row=0, column=0, columnspan=2)
pressure_panel.grid(row=1, column=0, padx=30, pady=10)
switch_panel.grid(row=1, column=1, padx=30, pady=10)
send_panel.grid(row=2, column=0, columnspan=2, pady=20)

root.mainloop()


# time.sleep(3)

