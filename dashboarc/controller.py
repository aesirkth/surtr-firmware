from constants import *
from integration import *
from model import *
from view import *
from graph import *


# =========================================================================	
# Controller:
class Controller:
    def __init__(self, view: View, model: Model, integration: Integration, eventQueue: queue.Queue, port: str):
        self.view = view
        self.model = model
        self.integration = integration
        
        self.stopGraphEvent = threading.Event()
        self.eventQueue = eventQueue

        # ------------ Event Queue ------------- #
        # store eventQueue in model in order for observer to indirectly update UI.
        self.model.connection.eventQueue    = eventQueue
        self.model.adc.eventQueue           = eventQueue
        self.model.actuation.eventQueue     = eventQueue
        self.model.config.eventQueue        = eventQueue
        self.model.surtrTime.eventQueue     = eventQueue


        # ------------ Observers --------------- #
        # Observer SW_STATE -> SW_VIEW
        self.model.actuation.attach(self.view.actuation.switch.update)

        # Observer ADC_STATE -> ADC_Transform -> ADC_VIEW
        self.model.adc.attach(self.transformAdc)

        # Observer CONN_STATE -> CONN_VIEW
        self.model.connection.attach(self.view.connection.update)

        # Observer CONFIG ADC -> ADC_VIEW
        # Observer CONFIG SW -> SW_VIEW
        # Observer CONFIG CONFIG -> CONFIG_VIEW
        self.model.config.attach(self.view.config.update)
        self.model.config.attach(self.updateAdcLabels)
        self.model.config.attach(self.view.actuation.switch.update_labels)

        # Observer TIME SURTR/GUI -> TIME_VIEW
        self.model.surtrTime.attach(self.view.time.update)
        

        # ------------ Functions --------------- #
        self.view.config.func = lambda: self.importConfig()
        self.view.connection.func = self.openPhysicalConnection

        for i in range(12):
            self.view.adc0.channel[i].func = lambda i=i: self.startGraph(ADC0_TAG, i)
            self.view.adc1.channel[i].func = lambda i=i: self.startGraph(ADC1_TAG, i)

                #crashes surtr firmware. i > numsiwtch
        self.view.actuation.switch.button[0].cmdOn  = lambda: self.actuateSwitch(0, True)
        self.view.actuation.switch.button[0].cmdOff = lambda: self.actuateSwitch(0, False)
        self.view.actuation.switch.button[1].cmdOn  = lambda: self.actuateSwitch(1, True)
        self.view.actuation.switch.button[1].cmdOff = lambda: self.actuateSwitch(1, False)
        self.view.actuation.switch.button[2].cmdOn  = lambda: self.actuateSwitch(2, True)
        self.view.actuation.switch.button[2].cmdOff = lambda: self.actuateSwitch(2, False)
        self.view.actuation.switch.button[3].cmdOn  = lambda: self.actuateSwitch(3, True)
        self.view.actuation.switch.button[3].cmdOff = lambda: self.actuateSwitch(3, False)
        self.view.actuation.switch.button[4].cmdOn  = lambda: self.actuateSwitch(4, True)
        self.view.actuation.switch.button[4].cmdOff = lambda: self.actuateSwitch(4, False)
        self.view.actuation.switch.button[5].cmdOn  = lambda: self.actuateSwitch(5, True)
        self.view.actuation.switch.button[5].cmdOff = lambda: self.actuateSwitch(5, False)
        self.view.actuation.switch.button[6].cmdOn  = lambda: self.actuateSwitch(6, True)
        self.view.actuation.switch.button[6].cmdOff = lambda: self.actuateSwitch(6, False)
        self.view.actuation.switch.button[7].cmdOn  = lambda: self.actuateSwitch(7, True)
        self.view.actuation.switch.button[7].cmdOff = lambda: self.actuateSwitch(7, False)

        # ------------ Begin Operation --------- #
        # --------- Import base config --------- #
        self.loadConfig("dashboard/config.json")

        # ------------ Connection Init --------- #
        self.model.connection.setState(UNPLUGGED)
        self.model.connection.setPort(port)

        # ------------ Logfile init ------------ #
        self.model.savefile.open()
        self.model.savefile.init_logfile()

        # -------Integration Threads Init ------ #
        integration.set(
            self.model.connection, 
            self.model.adc, 
            self.model.actuation, 
            self.model.savefile,
            self.model.surtrTime,
            self.synAck,
            self.transformAdc)
        integration.startThreads()

    # ======================================================================
    # openPhysicalConnection():
    def openPhysicalConnection(self, port):
        try:
            self.integration.stop.set()
            self.model.connection.ser = serial.Serial(port, BAUDRATE, timeout=0.25)
            self.model.connection.setPort(port)
            self.model.connection.setState(PAIRING)
            self.integration.stop.clear()
        except serial.SerialException:
            print("Open Serial Port: ", self.model.connection.port, " failed.")
            return

    # ======================================================================
    # actuateSwitch():
    def actuateSwitch(self, id, state):
        payload = SurtrCmd.switch_command(id, state)
        print("SW[", id, "] = ", state)
        self.integration.requestQueue.put(payload)

    # ======================================================================
    # synAck():
    def synAck(self):
        payload = SurtrCmd.syn_ack_command()
        self.integration.requestQueue.put(payload)

    # ======================================================================
    # startGraph():
    def startGraph(self, adcId, channelId):
        gr = IntegrationGraph(
            adcId, 
            channelId, 
            self.model.savefile.filename, 
            self.model.config.json,
            self.stopGraphEvent
        )
        gr.livePlot()
        #self.model.graph.list.append(gr)

    # ======================================================================
    # stopAllGraphs():
    def stopAllGraphs(self):
        self.stopGraphEvent.set()

    # ======================================================================
    # drawGraphs():
    def drawGraphs(self):
        self.eventQueue.put(lambda: plt.pause(1))

    # ======================================================================
    # calculateAdc():
    #   Reads in raw adc values from model.adc
    #   Reads in scale and offset from model.config
    #   Calculates applied ADC values and calls view.adc.update()
    #   This method is placed is attached to adc observer.
    #   (adc: Adc) argument has to be here because observer(self)
    #   requires that argument is the subject we are expecting.
    def transformAdc(self, adc_val: list[int]):
        adc_applied = [0]*24
        adc_raw = adc_val
        self.model.adc.adc = adc_val
        adc_scale = self.model.config.adc["scale"]
        adc_offset = self.model.config.adc["offset"]

        for i in range(0, ADC0_CHANNEL_VOLTAGE_END):
            adc_v = SurtrMath.adc_to_voltage(adc_raw[i])
            adc_v_norm = SurtrMath.normalize_voltage(adc_v)
            adc_v_scaled = adc_v_norm * adc_scale[i] + adc_offset[i]
            adc_applied[i] = adc_v_scaled
        for i in range(ADC0_CHANNEL_VOLTAGE_END, ADC0_CHANNEL_CURRENT_END):
            adc_v = SurtrMath.adc_to_current(adc_raw[i])
            adc_v_norm = SurtrMath.normalize_current(adc_v)
            adc_v_scaled = adc_v_norm * adc_scale[i] + adc_offset[i]
            adc_applied[i] = adc_v_scaled
        for i in range(ADC0_CHANNEL_CURRENT_END, ADC1_CHANNEL_VOLTAGE_END):
            adc_v = SurtrMath.adc_to_voltage(adc_raw[i])
            adc_v_norm = SurtrMath.normalize_voltage(adc_v)
            adc_v_scaled = adc_v_norm * adc_scale[i] + adc_offset[i]
            adc_applied[i] = adc_v_scaled
        for i in range(ADC1_CHANNEL_VOLTAGE_END, ADC1_CHANNEL_CURRENT_END):
            print("i: ", i)
            adc_v = SurtrMath.adc_to_current_bipolar(adc_raw[i])
            print("adc_v: ", adc_v)
            adc_vv = SurtrMath.adc_to_voltage(adc_raw[i])
            print("adc_volt: ", adc_vv)
            adc_v_norm = SurtrMath.normalize_current(adc_v)
            print("adc_v_norm: ", adc_v_norm)
            #adc_v_scaled = adc_v_norm * adc_scale[i] + adc_offset[i]
            adc_v_scaled = adc_v * adc_scale[i] + adc_offset[i]
            print("adc_v_scaled: ", adc_v_scaled, " scale: ", adc_scale[i], " offset: ", adc_offset[i])
            adc_applied[i] = adc_v_scaled

        self.view.adc0.update(adc_applied[0:12])
        self.view.adc1.update(adc_applied[12:24])

    # ======================================================================
    # updateAdcLabels():
    #   Intermediate function for updating ADC0 and ADC1 labels 
    #   Splits the adc labels into half and distributes.
    #   (config: Config) argument has to be here because observer(self)
    #   requires that argument is the subject we are expecting.
    def updateAdcLabels(self, config: Config):
        adcLabels = self.model.config.adc["label"]
        self.view.adc0.update_labels(adcLabels[0:12])
        self.view.adc1.update_labels(adcLabels[12:24])

    # ======================================================================
    # importConfig():
    #   Opens up pop-up where config file is chosen,
    #   Then tries to open this file and if succesful 
    #   set new config in model.config
    def importConfig(self):
        # gets filename somehow
        filepathPopUp = filedialog.askopenfilename(
            title="Select Config File",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            #initialdir=os.path.dirname(self.filepath)
        )
        self.loadConfig(filepathPopUp)

    # ======================================================================
    # loadConfig():
    def loadConfig(self, filename):
        try:
            config =  json.load(open(filename, 'r'))
            print("file imported json.")
            self.model.config.filename = filename
            self.model.config.set(config)
        except:
            print("Failed to open config file.")
            return None



