import os, sys
#import serial.tools.list_ports
#Cannot have dependencies in installer.
# Install and probe usb have to be separate scripts.

WINDOWS = "nt"

REQUIREMENTS = "dashboard/requirements.txt"
MAIN         = "dashboard/main.py"

standardPython  = sys.executable
venvPython      = None
port            = None

if os.name == WINDOWS:
    venvPython = os.path.join("venv", "Scripts", "python.exe")
else:
    venvPython = os.path.join("venv", "bin", "python")


if not os.path.isdir("venv"):

    print("Python venv not found.\nCreating new venv.")
    os.system(f"{standardPython} -m venv venv")
    print("New venv created.")

    print("Begin installing requirements.")
    os.system(f"{venvPython} -m pip install -r {REQUIREMENTS}")
    print("Requirements installed.")


#SYN_COMMAND = ""


#def probe_ports():
#    for port_info in serial.tools.list_ports.comports():
#        port = port_info.device
#        try:
#            ser_con = serial.Serial(port, 115200, timeout=0.2)
#            ser_con.write()
#            response = ser_con.read()
#        except Exception:
#            return None



print("Enter USB port name")
print("(Linux: /dev/ttyUSB*)")
print("(Windows: COM*)")
port = input("Enter port: ")
print(f"Port: {port}")

print("Starting Application.")
os.system(f"{venvPython} {MAIN} {port}")





