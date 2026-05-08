from constants import *
from model import *
from PIL import Image

# ===============================================================
# View:
class View:
    def __init__(self):
        self.root = ctk.CTk()
        self.adc0 = AdcView(self.root, ADC0_TAG, "ADC0", "")
        self.adc1 = AdcView(self.root, ADC1_TAG, "ADC1", "")
        self.actuation = ActuationView(self.root)
        self.config = ConfigView(self.root)
        self.sidebar = SideBarView(self.root)
        self.connection = ConnectionView(self.sidebar.panel)
        self.time = TimeView(self.sidebar.panel)

    def build(self):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        self.root.title("Surtr Dashboard")
        self.root.minsize(1500, 600)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_columnconfigure(2, weight=0)

        self.adc0.build(ADC0_TAG)
        self.adc1.build(ADC1_TAG)
        self.actuation.build()
        self.config.build()

        self.sidebar.build()
        self.connection.build()
        self.time.build()


# ===============================================================
# AdcView:
#   Holds GUI View of ADC values.
#   Panel, title, lable, range label.
#   Func is for channel live graph.
class AdcView:
    def __init__(self, parent, id, title, label):
        self.id = id
        self.func = None
        self.panel = ctk.CTkFrame(parent, border_width=1)
        self.title = ctk.CTkLabel(self.panel, text=title, font=DEFAULT_FONT_BOLD)
        self.label = ctk.CTkLabel(self.panel, text=label, font=DEFAULT_FONT)
        self.PT_range_label = ctk.CTkLabel(self.panel, text="range_text_0", font=DEFAULT_FONT, justify="center")
        
        #img = Image.open("dashboarc/graphicon.png").convert("RGBA")
        #self.graphIcon = ctk.CTkImage(
        #    light_image=img,
        #    dark_image=img
        #)

        self.channel: list[ChannelView] = []
        for i in range(0, NUM_CHANNELS_PER_ADC):
            ch = ChannelView(
                self.panel, 
                f"CH {i+1}", 
                "-", 
                self.func,
                None)
            self.channel.append(ch)

    # update():
    #   Wrapper function that updates latest ADC value to each channel
    def update(self, adcApplied: list[int]):
        self.update_channels(adcApplied)

    def update_channels(self, adc_values):
        for i in range(0, NUM_CHANNELS_PER_ADC):
            self.channel[i].update_val(adc_values[i])

    # update_labels():
    #   Updates each channel with latest label given by config.
    def update_labels(self, adcLabels: list[str]):
        for i, label in enumerate(adcLabels):
            self.channel[i].update_label(label)

    # update_labels():
    #   Updates each range label with latest label given by config.
    #def update_range_label(self, config: Config):
        #self.PT_range_label.configure(True, text=label)
    
    def build(self, adcTag):

        self.panel.grid_columnconfigure(1, minsize=160, weight=1)
        self.panel.grid_columnconfigure(3, minsize=160, weight=1)
        if adcTag == ADC0_TAG:
            self.panel.grid(row=1, column=0, padx=(16, 8), pady=8, sticky="nsew")
        else:
            self.panel.grid(row=1, column=1, padx=(8, 16), pady=8, sticky="nsew")
        self.title.grid(row=0, column=0, columnspan=4, padx=16, pady=8)
        self.label.grid(row=1, column=0, padx=4, pady=4, sticky="ew")

        for i in range(NUM_CHANNELS_PER_ADC):
            row = (i//2)+1
            col = (i%2)*3
            self.channel[i].label.grid(row=row, column=col, padx=4, pady=4, sticky="ew")
            self.channel[i].value.grid(row=row, column=col+1, padx=4, pady=4, sticky="ew")
            self.channel[i].button.grid(row=row, column=col+2, padx=6, pady=3, sticky="ew")
		
# =====================================================================
# ChannelView:
class ChannelView:
    
    def __init__(self, parent, label, value, func, graphIcon):
        self.label = ctk.CTkLabel(parent, text=label, font=DEFAULT_FONT)
        self.value = ctk.CTkLabel(parent, text=value, font=DEFAULT_FONT)
        self.graphIcon = graphIcon
        self.func = None
        self.button = ctk.CTkButton(parent, 
                                    text="G",
                                    #image=self.graphIcon,
                                    command=lambda: self.func(), 
                                    width=25, 
                                    font=DEFAULT_FONT, 
                                    corner_radius=0,
                                    )
        self.disabled = False
        self.button.configure(state="normal")

    def update_val(self, val):
        if self.disabled:
            self.value.configure(True, text="-")
            return
        self.value.configure(True, text=f"{val:8.3f}")
    
    def update_label(self, label):
        self.label.configure(True, text=label)

    def set_disabled(self, disabled):
        self.disabled = disabled
        text_color = ("gray60", "gray45") if disabled else ("gray10", "gray90")
        self.label.configure(text_color=text_color)
        self.value.configure(text_color=text_color)
    
# =====================================================================
# ActuationView:
class ActuationView:
    def __init__(self, parent):
        self.func = None #will be set by controller 
        self.panel = ctk.CTkFrame(parent, border_width=1)
        self.switch = SwitchView(self.panel)
        self.stepper = StepperView(self.panel)
        self.ignition = IgnitionView(self.panel)

    def build(self):
        self.panel.grid_columnconfigure(0, weight=0)
        self.panel.grid_columnconfigure(1, weight=0)
        self.panel.grid_columnconfigure(2, weight=0)
        self.panel.grid_columnconfigure(3, weight=0)
        self.panel.grid_columnconfigure(4, weight=0)
        self.panel.grid(row=2, column=0, columnspan=2, pady=8, padx=(16, 16), sticky="ew")
        self.switch.title.grid(row=0, column=0, columnspan=6, pady=4)
        self.switch.panel.grid(row=0, column=0, sticky="nw", padx=6, pady=6)
        self.stepper.title.grid(row=0, column=0, columnspan=3, pady=4)
        self.stepper.panel.grid(row=0, column=1, sticky="nw", padx=6, pady=6)
        SW_PER_COL = 4
        for i in range(NUM_SWITCHES):
            row = (i) % SW_PER_COL + 1  # +1 to account for title
            col = (i) // SW_PER_COL
            self.switch.button[i].label.grid(row=row, column=col*3+0, padx=2, pady=1, sticky="w")
            self.switch.button[i].on.grid(row=row, column=col*3+1, padx=2, pady=1, sticky="w")
            self.switch.button[i].off.grid(row=row, column=col*3+2, padx=2, pady=1, sticky="w")
        
        self.stepper.title.grid(row=0, column=0, columnspan=3, pady=4)
        self.stepper.panel.grid(row=0, column=1, sticky="nw", padx=6, pady=6)

        for i in range(0, NUM_STEPPERS):
            self.stepper.motor[i].label.grid(row=i+1, column=0, padx=2, pady=1, sticky="w")
            self.stepper.motor[i].entry.grid(row=i+1, column=1, padx=2, pady=1, sticky="w")
            self.stepper.motor[i].button.grid(row=i+1, column=2, padx=2, pady=1, sticky="w")
        
        self.ignition.panel.grid(row=0, column=2, sticky="nw", padx=6, pady=6)
        self.ignition.panel.grid_columnconfigure(0, weight=1)
        self.ignition.title.grid(row=0, column=0, pady=4, sticky="n")
        self.ignition.button.grid(row=1, column=0, padx=6, pady=3, sticky="w")
# =====================================================================
# SwitchView:
#   func is ctrl.actuateSwitch()
class SwitchView:
    def __init__(self, parent):
        self.func = None
        self.panel = ctk.CTkFrame(parent)
        self.title = ctk.CTkLabel(self.panel, text="Switches", font=DEFAULT_FONT_BOLD)
        self.button: list[ButtonView] = []
        for i in range(0, NUM_SWITCHES):
            bt = ButtonView(self.panel, i+1, f"SW {i+1}")
            self.button.append(bt)	

    # update():
    #   Updates all Switches with latest values. 
    #   This function is observing acutation model
    def update(self, actuation: Actuation):
        for i in range(0, NUM_SWITCHES):
            self.button[i].set_state(actuation.sw[i])

    # update_labels():
    #   Updates each channel with latest label given by config.
    def update_labels(self, config: Config):
        for i, label in enumerate(config.sw["label"]):
            self.button[i].update_label(label)
        for i, label in enumerate(config.sw["on_label"]):
            self.button[i].update_on_labels(label)
        for i, label in enumerate(config.sw["off_label"]):
            self.button[i].update_off_labels(label)
        for i, disableBool in enumerate(config.sw["disable"]):
            self.button[i].set_disabled(disableBool)



# =====================================================================
# ButtonView:
class ButtonView:
    def __init__(self, parent, id, label):
        self.id = id
        self.label 	= ctk.CTkLabel(parent, text=label, font=DEFAULT_FONT)
        self.disabled = False
        self.current_state = False
        self.cmdOn = None
        self.cmdOff = None
        self.on = ctk.CTkButton(
            parent,
            text="On",
            command=lambda: self.cmdOn(),
            #command=lambda: self.cmdOn(self.id, True),
            width=50,
            font=DEFAULT_FONT,
            corner_radius=0
        )
        self.off = ctk.CTkButton(
            parent,
            text="Off",
            command=lambda: self.cmdOff(),
            #command=lambda: self.cmdOff(self.id, False),
            width=50,
            font=DEFAULT_FONT,
            corner_radius=0
        )
        self.set_state(False)

    def update_label(self, label):
        self.label.configure(True, text=label)

    def update_state_labels(self, on_label, off_label):
        self.on.configure(text=on_label)
        self.off.configure(text=off_label)

    def update_on_labels(self, on_label):
        self.on.configure(text=on_label)
    def update_off_labels(self, off_label):
        self.off.configure(text=off_label)

    def set_disabled(self, disabled):
        self.disabled = disabled
        state = "disabled" if disabled else "normal"
        text_color = ("gray60", "gray45") if disabled else ("gray10", "gray90")
        self.label.configure(text_color=text_color)
        self.on.configure(state=state)
        self.off.configure(state=state)
        self.set_state(self.current_state)

    def set_state(self, state: bool):
        self.current_state = state
        if self.disabled:
            disabled_color = "#4a4a4a"
            self.on.configure(fg_color=disabled_color)
            self.off.configure(fg_color=disabled_color)
            return

        active_color = "#1f6aa5"
        inactive_color = "#3a3a3a"
        if state:
            self.on.configure(fg_color=active_color)
            self.off.configure(fg_color=inactive_color)
        else:
            self.on.configure(fg_color=inactive_color)
            self.off.configure(fg_color=active_color)

# =====================================================================
# StepperView:
#   Func is actuateStepper()
class StepperView:
    def __init__(self, parent):
        self.func = None
        self.panel = ctk.CTkFrame(parent)
        self.title = ctk.CTkLabel(self.panel, text="Steppers", font=DEFAULT_FONT_BOLD)
        self.motor: list[MotorView] = []
        for i in range(0,NUM_STEPPERS):
            bt = MotorView(self.panel, f"STEP {i+1}", self.func)
            self.motor.append(bt)	
    
# =====================================================================
# MotorView:
class MotorView:
    def __init__(self, parent, label, func):
        self.label 	= ctk.CTkLabel(parent, text=label, font=DEFAULT_FONT)
        self.entry  = ctk.CTkEntry(parent, width=60, font=DEFAULT_FONT)
        self.button = ctk.CTkButton(parent, text="Send", command=func, width=60, font=DEFAULT_FONT, corner_radius=0)
        self.disabled = False

    def update_label(self, label):
        self.label.configure(True, text=label)

    def update_state_labels(self, on_label, off_label):
        self.on.configure(text=on_label)
        self.off.configure(text=off_label)

    def set_disabled(self, disabled):
        self.disabled = disabled
        text_color = ("gray60", "gray45") if disabled else ("gray10", "gray90")
        entry_state = "disabled" if disabled else "normal"
        button_state = "disabled" if disabled else "normal"
        self.label.configure(text_color=text_color)
        self.entry.configure(state=entry_state)
        self.button.configure(state=button_state)

# =====================================================================
# IgnitionView:
class IgnitionView:
        def __init__(self, parent):
            self.func = None
            self.panel = ctk.CTkFrame(parent)
            self.title = ctk.CTkLabel(self.panel, text="Ignition", font=DEFAULT_FONT_BOLD)		
            self.button = ctk.CTkButton(
                self.panel, 
                text="Ignite", 
                command=self.func, 
                width=150, 
                font=DEFAULT_FONT, 
                corner_radius=0,
                fg_color="#b22222",
                hover_color="#8b1a1a")
            self.disabled = False

        def update_label(self, label):
            self.button.configure(text=label)

        def set_disabled(self, disabled):
            self.disabled = disabled
            state = "disabled" if disabled else "normal"
            self.button.configure(state=state)

# =====================================================================
# ConfigView:
class ConfigView:
    def __init__(self, parent):
        self.func = None
        self.panel = ctk.CTkFrame(parent, fg_color="transparent")
        self.path_var = ctk.StringVar(value="")
        self.path_entry = ctk.CTkEntry(self.panel, textvariable=self.path_var, state="readonly", width=400, font=DEFAULT_FONT)
        self.import_button = ctk.CTkButton(
            self.panel, 
            text="Import Config", 
            command=lambda: self.func(),
            font=DEFAULT_FONT, 
            corner_radius=0)

    def update(self, config: Config):
        self.path_var.set(config.filename)

    def build(self):
        self.path_entry.grid(row=0, column=1, padx=4, pady=4, sticky="ew")
        self.panel.grid_columnconfigure(1, weight=1)
        self.panel.grid(row=0, column=0, columnspan=2, sticky="ew", padx=8, pady=4)
        self.import_button.grid(row=0, column=0, padx=4, pady=4)

# =====================================================================
# SideBarView:
class SideBarView:
    def __init__(self, parent):
        self.panel = ctk.CTkFrame(parent, fg_color="transparent")

    def build(self):
	    self.panel.grid(row=1, column=2, sticky="nw", padx=6, pady=3)

# =====================================================================
# ConnectionView:
class ConnectionView:
    def __init__(self, parent):
        self.func = None
        self.panel = ctk.CTkFrame(parent)
        self.title = ctk.CTkLabel(self.panel, text="Connection", font=DEFAULT_FONT)
        self.port_var = ctk.StringVar(value="")
        self.port_entry = ctk.CTkEntry(self.panel, textvariable=self.port_var, width=150, font=DEFAULT_FONT, corner_radius=0)
        self.reconnect_button = ctk.CTkButton(
            self.panel, 
            text="Reconnect", 
            command=lambda: self.func(self.port_var.get()), 
            width=150, 
            font=DEFAULT_FONT, 
            corner_radius=0)
        self.status_label = ctk.CTkLabel(self.panel, text="Not connected", font=("IBM Plex Mono", 12))
        self.ping = ctk.CTkLabel(self.panel, text="---- ms", font=("IBM Plex Mono", 12))

    # update():
    #   Updates latest port name.
    #   Updates latest Connection Status (state)
    def update(self, connection: Connection):
        self.port_var.set(connection.port)
        if (connection.state == CONNECTED):
            status_text = f"Connected ({self.port_var.get()})" if self.port_var else "Connected"
            status_color = ("gray35", "gray70")
        elif (connection.state == PAIRING):
            status_text = "Pairing..."
            status_color = ("gray50", "gray60")
        else:
            status_text = "Not Connected"
            status_color = ("gray50", "gray60")

        self.status_label.configure(text=status_text, text_color=status_color)
        ping_text = f"{connection.ms:4d} ms" if connection.ms is not None else "---- ms"
        self.ping.configure(text=ping_text, text_color=status_color)

    def build(self):
        self.panel.grid(row=0, column=0, sticky="nw", padx=0, pady=0)
        self.title.grid(row=0, column=0, pady=4)
        self.port_entry.grid(row=1, column=0, padx=6, pady=3, sticky="w")
        self.reconnect_button.grid(row=2, column=0, padx=6, pady=3, sticky="w")
        self.status_label.grid(row=3, column=0, padx=6, pady=(0, 3), sticky="w")
        self.ping.grid(row=4, column=0, padx=6, pady=(0, 3), sticky="w")

# =====================================================================
# TimeView:
class TimeView:
    def __init__(self, parent):
        self.panel = ctk.CTkFrame(parent, border_width=1)
        self.label_pgt = ctk.CTkLabel(self.panel, text="Time (program): ", font=("IBM Plex Mono", 12))
        self.label_srt = ctk.CTkLabel(self.panel, text="Time (Surtr): ", font=("IBM Plex Mono", 12))
    
    def convert_to_min_sec(self, seconds):
        if seconds is None:
            return "--:--"
        minutes = int(seconds) // 60
        secs = int(seconds) % 60
        return f"{minutes:02d}:{secs:02d}"
        
    def update(self, surtrTime: Time):
        self.label_pgt.configure(True, text=f"Time (program): " + self.convert_to_min_sec(surtrTime.guiSinceBoot))
        self.label_srt.configure(True, text=f"Time (Surtr): " + self.convert_to_min_sec(surtrTime.surtrSinceBoot))

    def build(self):
        self.panel.grid(row=4, column=0, padx=0, pady=(4, 0), sticky="nw")
        self.label_pgt.grid(row=0, column=0, padx=6, pady=(3, 1), sticky="w")
        self.label_srt.grid(row=1, column=0, padx=6, pady=(0, 3), sticky="w")
