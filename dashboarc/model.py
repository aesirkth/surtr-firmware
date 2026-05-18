from constants import *
from observer import Observer


# ===============================================================
# Model:
class Model:
    def __init__(self):
        self.adc = Adc()
        self.actuation = Actuation()
        self.connection = Connection()
        self.savefile = SaveFile()
        self.config = Config()
        self.surtrTime = Time()

# ===============================================================
# Adc extends (Observer)
#   Holds the data for adcs which is uint32 adc[24]
#   ADC0: 0-11 ADC1: 12-23
#   0-7 (V) 8-11 (I) 12-19 (V) 20-23 (I)
#   super() instantiates the Observer
class Adc(Observer):
    def __init__(self):
        super().__init__()
        self.adc = [0]*24

    def set(self, val):
        self.adc = val
        self.notify()


# ===============================================================
# Actuation extends (Observer)
#   Holds the data for Actuation which is uint8 sw[8]
#   super() instantiates the Observer
class Actuation(Observer):
    def __init__(self):
        super().__init__()
        self.sw = [0]*NUM_SWITCHES
    
    def set(self, val):
        self.sw = val
        self.notify()

# ===============================================================
# Connection extends (Observer):
#   super() instantiates the Observer
class Connection(Observer):
    def __init__(self):
        super().__init__()
        self.state = None
        self.ser: serial.Serial = None
        self.port: str = None
        self.ms = None

    def setState(self, state):
        self.state = state
        self.notify()

    def setPort(self, port):
        self.port = port
        print("SETPORT")
        self.notify()

    def close(self):
        if self.ser == None:
            return
        self.ser.close()
        self.ser = None
        self.notify()

    def setPing(self, ms):
        self.ms = ms
        self.notify()
        
# ===============================================================
# Time extends (Observer):
#   super() instantiates the Observer
class Time(Observer):
    def __init__(self):
        super().__init__()
        self.surtrSinceBoot = None
        self.guiSinceBoot = None
        self.guiStartTime = time.time()

    def setSurtrTime(self, surtrSinceBoot):
        self.surtrSinceBoot = surtrSinceBoot
        self.notify()
    
    def setGuiTime(self, guiSinceBoot):
        self.guiSinceBoot = guiSinceBoot - self.guiStartTime
        self.notify()



# ===============================================================
# Config extends (Observer)
#   Holds the data for Config
#   super() instantiates the Observer
class Config(Observer):

    # Initiated by import from config file.
    # use set() for this instead?
    def __init__(self):
        super().__init__()
        self.filename = None
        self.json = None
        self.adc = {
            "label": None,
            "disable": None,
            "scale": None,
            "offset": None
        }
        self.sw = {
            "label": None,
            "on_label": None,
            "off_label": None,
            "disable": None
        }

    # set():
    #   Finds new config file and loads into config.
    #   Notify subscribers that config has changed.
    def set(self, config):
        self.json = config
        self.adc["label"]   = self.extractAdcLabel()
        self.adc["disable"] = self.extractAdcDisable()
        self.adc["scale"]   = self.extractAdcScales()
        self.adc["offset"]  = self.extractAdcOffset()
        self.sw["label"]     = self.extractSWLabel()
        self.sw["disable"]   = self.extractSWDisable()
        self.sw["on_label"]  = self.extractSWOnLabel()
        self.sw["off_label"] = self.extractSWOffLabel()
        print("set successful.")

        self.notify()
        print("notify successful.")

    # extractScales():
    #   Takes all 24 scales for ADC0 + ADC1
    def extractAdcScales(self):
        scales = []
        for adc_key in ["ADC0", "ADC1"]:
            adc = self.json.get(adc_key, {})
            for i in range(1, 13):
                ch = adc.get(f"channel{i}", {})
                scales.append(ch.get("scale", 1.0))
        return scales
    
    # extractOffset():
    #   Takes all 24 offsets for ADC0 + ADC1
    #   If no offset exists then default to 0
    def extractAdcOffset(self):
        offsets = []
        for adc_key in ["ADC0", "ADC1"]:
            adc = self.json.get(adc_key, {})
            for i in range(1, 13):
                ch = adc.get(f"channel{i}", {})
                offsets.append(ch.get("offset", 0.0))
        return offsets

    # extractLabel():
    #   Takes all 24 labels for ADC0 + ADC1
    #   If no label exists then default to 0
    def extractAdcLabel(self):
        labels = []
        for adc_key in ["ADC0", "ADC1"]:
            adc = self.json.get(adc_key, {})
            for i in range(1, 13):
                ch = adc.get(f"channel{i}", {})
                labels.append(ch.get("label", 0.0))
        return labels

    # extractDisable():
    #   Takes all 24 enable/disable for ADC0 + ADC1
    #   If no label exists then default to 0
    def extractAdcDisable(self):
        labels = []
        for adc_key in ["ADC0", "ADC1"]:
            adc = self.json.get(adc_key, {})
            for i in range(1, 13):
                ch = adc.get(f"channel{i}", {})
                labels.append(ch.get("disable", False))
        return labels

    # extractSWLabel()
    def extractSWLabel(self):
        labels = []
        sw = self.json.get("SWITCHES", {})
        for i in range(1, 9):
            s = sw.get(f"switch{i}", {})
            labels.append(s.get("label", ""))
        return labels

    # extractSwDisable()
    def extractSWDisable(self):
        disabled = []
        sw = self.json.get("SWITCHES", {})
        for i in range(1, 9):
            s = sw.get(f"switch{i}", {})
            disabled.append(s.get("disabled", False))
        return disabled

    # extractSwOnLabel()
    def extractSWOnLabel(self):
        on_labels = []
        sw = self.json.get("SWITCHES", {})
        for i in range(1, 9):
            s = sw.get(f"switch{i}", {})
            on_labels.append(s.get("on_label", "On"))
        return on_labels

    # extractSWOffLabel()
    def extractSWOffLabel(self):
        off_labels = []
        sw = self.json.get("SWITCHES", {})
        for i in range(1, 9):
            s = sw.get(f"switch{i}", {})
            off_labels.append(s.get("off_label", "Off"))
        return off_labels

# ===============================================================
# SaveFile:
class SaveFile():
    def __init__(self):
        self.filename = None
        self.handle = None

    def open(self):
        self.filename = self.get_logfile_name()
        self.handle = open(self.filename, "w")

    def init_logfile(self):
        self.handle.write("time," + ",".join(f"adc{i:02d}" for i in range(NUM_CHANNELS_TOTAL)) 
                            + ",".join(f"sw{i:02d}" for i in range(NUM_SWITCHES)) + "\n")
        self.handle.flush()

    def get_logfile_name(self):
        os.makedirs("data", exist_ok=True)
        savefile = "data/" + datetime.now().strftime("data_%Y_%m_%d_%H_%M_%S.csv")
        return savefile

    def writeRow(self, time, adc_raw, switches):
        line = (
            str(time) + "," +
            ",".join(str(v) for v in adc_raw) + "," +
            ",".join(str(v) for v in switches) + "\n"
        )
        self.handle.write(line)
        self.handle.flush()



# ===============================================================
# AD4111 Data Sheet p.29:
# 	The output code for any input voltage is represented as:
#	Code = (2^N * V_in * 0.1) / VREF
#	The output code for any input current is represented as:
#	Code = (2^N * I_in * 50) / VREF
# ===============================================================
class SurtrMath:
    def __init__(self):
        pass

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

    def adc_to_current_bipolar(adc_in):
        return (((adc_in / (ADCBITSIZE>>1))- 1) * VREF*2 / 50)


# ===============================================================
# Packet:
class Packet:
    def __init__(self):
        self.alignment = None
        self.length = None
        self.id = None
        self.method = None
        self.t_send = None
        self.data = None
        self.crc = None

# ===============================================================
# SurtrCmd:
class SurtrCmd:
    def __init__(self):
        pass

    # ===============================================================
    # switch_command():
    #	places SYN-ACK message on Request Queue for send out.
    #	| TIME | CMD | (9 bytes)
    def syn_ack_command():
        packet = Packet()
        packet.data = bytearray(1)
        packet.data[0] = SURTR_REQUEST_SYN_ACK
        return packet

    # ===============================================================
    # switch_command():
    #	Transforms id and state of switch into payload and 
    #	places on Request Queue for send out.
    #	| TIME | CMD | SW | STATE |	(11 bytes)
    def switch_command(id, state):
        packet = Packet()
        packet.data = bytearray(3)
        packet.data[0] = SURTR_REQUEST_SW_CTRL
        packet.data[1] = id
        packet.data[2] = state
        return packet

    # ===============================================================
    # ignition_command():
    #	Converts ignition execution into sutr message and places in write queue.
    #	| TIME | CMD | PASSWD |	(10 bytes)
    def ignition_command(password):
        packet = Packet()
        packet.data = bytearray(2)
        packet.data[0] = SURTR_REQUEST_IGNITION
        packet.data[1] = password
        return packet
        

        