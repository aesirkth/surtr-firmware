from constants import *

# ==========================================================================
# CONFIG MANAGER 
# ==========================================================================
class Config:

    # __init__():
    #   IMPORT CONFIG button is gives the config_import() function along with 
    #   the config_apply_labels() function passed down from Dashboard.
    def __init__(self, parent, func_apply_labels, initial_config_path):
        self.panel = ctk.CTkFrame(parent, fg_color="transparent")
        self.path_var = ctk.StringVar(value=initial_config_path)
        self.path_entry = ctk.CTkEntry(self.panel, textvariable=self.path_var, state="readonly", width=400, font=DEFAULT_FONT)
        self.import_button = ctk.CTkButton(
            self.panel, 
            text="Import Config", 
            command=lambda: self.config_import(func_apply_labels), 
            font=DEFAULT_FONT, 
            corner_radius=0)
        self.filepath = initial_config_path
        self.config   = config_loadfile(self.filepath)

    # config_import():
    #   opens up box to pick config file.
    #   should file not be valid then keep old.
    #   func_apply_labels() --> Dashboard.config_apply_labels()
    def config_import(self, func_apply_labels):
        filepath_import = filedialog.askopenfilename(
            title="Select Config File",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialdir=os.path.dirname(self.filepath)
        )

        if filepath_import == "":
            print("filepath_import is empty string.")
            return
        
        config_import = config_loadfile(filepath_import)
        if config_import == None:
            return

        self.config = config_import
        self.filepath = filepath_import
        self.path_var = ctk.StringVar(value=self.filepath)
        self.path_entry.configure(True, textvariable=self.path_var)
        func_apply_labels()

    def get_adc_channel_scale(self, adc_id, ch_id):
        return self.config[f"ADC{adc_id}"][f"channel{ch_id}"]["scale"]
    
    def get_adc_channel_label(self, adc_id, ch_id):
        return self.config[f"ADC{adc_id}"][f"channel{ch_id}"]["label"]

    def get_adc_channel_disabled(self, adc_id, ch_id):
        channel_cfg = self.config[f"ADC{adc_id}"][f"channel{ch_id}"]
        return channel_cfg.get("disabled", False)

    def get_switch_label(self, switch_id):
        return self._get_switch_cfg(switch_id).get("label", f"SW {switch_id}")

    def get_switch_on_label(self, switch_id):
        return self._get_switch_cfg(switch_id).get("on_label", "On")

    def get_switch_off_label(self, switch_id):
        return self._get_switch_cfg(switch_id).get("off_label", "Off")

    def get_switch_disabled(self, switch_id):
        return self._get_switch_cfg(switch_id).get("disabled", False)

    def get_stepper_label(self, stepper_id):
        return self._get_stepper_cfg(stepper_id).get("label", f"STEP {stepper_id}")

    def get_stepper_disabled(self, stepper_id):
        return self._get_stepper_cfg(stepper_id).get("disabled", False)

    def _get_switch_cfg(self, switch_id):
        switches = self.config.get("SWITCHES", {})
        return switches.get(f"switch{switch_id}", {})

    def _get_stepper_cfg(self, stepper_id):
        steppers = self.config.get("STEPPERS", {})
        return steppers.get(f"stepper{stepper_id}", {})


# config_loadfile():
#	Tries to retrieve json config object from file.
def config_loadfile(filepath):
    try:
        return json.load(open(filepath, 'r'))
    except:
        print("Failed to open config file.")
        return None
