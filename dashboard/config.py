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
            title="Select ADC Config File",
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
		

# config_loadfile():
#	Tries to retrieve json config object from file.
def config_loadfile(filepath):
    try:
        return json.load(open(filepath, 'r'))
    except:
        print("Failed to open config file.")
        return None
