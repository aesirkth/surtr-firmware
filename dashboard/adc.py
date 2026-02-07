
from constants import *

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

        self.channel: list[ADC.Channel] = []
        for i in range(0, NUM_CHANNELS_PER_ADC):
            ch = ADC.Channel(self.panel, f"CH {i+1}", "-")
            self.channel.append(ch)

    def update_channels(self, adc_values):
        for i in range(0, NUM_CHANNELS_PER_ADC):
            self.channel[i].update_val(adc_values[i])

    def update_range_label(self, label):
        self.PT_range_label.configure(True, text=label)
		
    # =====================================================================
    class Channel:
    
        def __init__(self, parent, label, value):
            self.label = ctk.CTkLabel(parent, text=label, font=DEFAULT_FONT)
            self.value = ctk.CTkLabel(parent, text=value, font=DEFAULT_FONT)

        def update_val(self, val):
            self.value.configure(True, text=f"{val:8.3f}")
        
        def update_label(self, label):
            self.label.configure(True, text=label)
    