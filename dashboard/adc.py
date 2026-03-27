
from constants import *
from graph import plot_single_graph_live

# ===============================================================
# ADC CHANNELS
# Each ADC holds 12 channels.
# ===============================================================
class ADC:
    def __init__(self, parent, id, title, label):
        self.id = id
        self.panel = ctk.CTkFrame(parent, border_width=1)
        self.title = ctk.CTkLabel(self.panel, text=title, font=DEFAULT_FONT_BOLD)
        self.label = ctk.CTkLabel(self.panel, text=label, font=DEFAULT_FONT)
        self.PT_range_label = ctk.CTkLabel(self.panel, text="range_text_0", font=DEFAULT_FONT, justify="center")
        self.datafile = None
        self.configfile = None

        self.channel: list[ADC.Channel] = []
        for i in range(0, NUM_CHANNELS_PER_ADC):
            ch = ADC.Channel(self.panel, f"CH {i+1}", "-", lambda n=i: plot_single_graph_live(self.id, n, self.datafile, self.configfile))
            self.channel.append(ch)

    def update_channels(self, adc_values):
        for i in range(0, NUM_CHANNELS_PER_ADC):
            self.channel[i].update_val(adc_values[i])

    def update_range_label(self, label):
        self.PT_range_label.configure(True, text=label)
		
    # =====================================================================
    class Channel:
    
        def __init__(self, parent, label, value, func):
            self.label = ctk.CTkLabel(parent, text=label, font=DEFAULT_FONT)
            self.value = ctk.CTkLabel(parent, text=value, font=DEFAULT_FONT)
            self.button = ctk.CTkButton(parent, 
                                        text="G", 
                                        command=lambda: func(), 
                                        width=25, 
                                        font=DEFAULT_FONT, 
                                        corner_radius=0)
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
    