from typing import Any
from parser import SurtrParser
import sys
import os
from widgets import TextLastValue, TimeLastValue
from config_manager import ConfigManager
import tkinter as tk
import customtkinter as ctk
from tkinter import filedialog
import traceback

# Voltage and current ranges. OBS: Voltages currently not tested.
V_START = 0.9
V_END = 4.5
C_START = 4
C_END = 20

# Helper function to get display data
def get_display_data(parser, id_str, conversion=lambda x: x, unconnected_value="-"):
    """Wrapper that can handle an unconnected parser."""
    if parser.connected:
        try:
            return conversion(parser.data[id_str][1][-1])
        except Exception:
            pass
    return unconnected_value


# Helper function to build channel label
def _build_channel_label(channel_num, label_text):
    """Build label string: 'N. label: ' if label exists, 'N: ' if empty."""
    if label_text:
        return f"{channel_num}. {label_text}: "
    return f"{channel_num}: "


# Helper function to build context label texts
def _context_label_texts(adc_config):
    """Compute context label strings for both ADCs with newlines padded to match height."""
    context_text_0 = adc_config["ADC0"].get("context_label", "")
    context_text_1 = adc_config["ADC1"].get("context_label", "")

    newlines_0 = context_text_0.count("\n")
    newlines_1 = context_text_1.count("\n")
    if newlines_0 < newlines_1:
        context_text_0 += "\n" * (newlines_1 - newlines_0)
    elif newlines_1 < newlines_0:
        context_text_1 += "\n" * (newlines_0 - newlines_1)
        
    return context_text_0, context_text_1

# Main dashboard window
class SurtrDashboard(ctk.CTk):
    """Main dashboard window. All UI state and dependencies are held here."""

    def __init__(self, parser, initial_config_path=None):
        super().__init__()
        self.parser = parser

        # Font
        self._font_path = os.path.join(os.path.dirname(__file__), "resources", "IBMPlexMono-Regular.ttf")
        ctk.FontManager.load_font(self._font_path)
        self._font_name = "IBM Plex Mono"
        self._default_font = (self._font_name, 15)

        # Appearance
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        # Config manager
        if initial_config_path is None:
            initial_config_path = os.path.join(os.path.dirname(__file__), "adc_config.json")
        self.config_manager = ConfigManager(initial_config_path)

        # ADC widgets
        self.adc_widgets = []
        self.context_label_widgets = []

        # Window
        self.title("Surtr Dashboard")
        self.minsize(900, 600)
        self._build_ui()


    # Refresh ADC labels
    def refresh_adc_labels(self, adc_config=None):
        """Update all ADC widget labels and context labels from the given config."""

        if adc_config is None:
            adc_config = self.config_manager.get_config()

        # For each ADC widget, update the label text
        for label_widget, value_widget, adc_name, channel_num in self.adc_widgets:
            channel_key = f"channel{channel_num}"
            label_text = adc_config[adc_name][channel_key]["label"]
            label_widget.configure(text=_build_channel_label(channel_num, label_text))

        # Update context labels
        context_text_0, context_text_1 = _context_label_texts(adc_config)
        for context_label_widget, adc_name in self.context_label_widgets:
            if adc_name == "ADC0":
                context_label_widget.configure(text=context_text_0)
            elif adc_name == "ADC1":
                context_label_widget.configure(text=context_text_1)
            else:
                raise ValueError(f"Invalid ADC name: {adc_name}")

    # Import config
    def _import_config(self):
        """Open file dialog to select and load a new config file."""
        current_path = self.config_manager.get_path()
        file_path = filedialog.askopenfilename(
            title="Select ADC Config File",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialdir=(
                os.path.dirname(current_path)
                if os.path.exists(current_path)
                else os.path.dirname(__file__)
            ),
        )
        if file_path:
            self.config_manager.load_from_path(file_path)
            self._config_path_var.set(self.config_manager.get_path())
            self.refresh_adc_labels(self.config_manager.get_config())

    # Create ADC widget
    def _create_adc_widget(
        self, panel, channel_num, adc_name, value_id, adc_config=None, *, scale_type
    ):
        """Create label and value widgets for an ADC channel and store them for later updates.
        scale_type: 'v' for voltage scaling (V_START..V_END), 'c' for current scaling (C_START..C_END).
        """
        if scale_type not in ("v", "c"):
            raise ValueError(f"scale_type must be 'v' or 'c', got {scale_type!r}")
        if adc_config is None:
            adc_config = self.config_manager.get_config()
        channel_key = f"channel{channel_num}" # Get the channel key, which is the channel number
        label_text = adc_config[adc_name][channel_key]["label"]

        if scale_type == "v":
            conversion = lambda x, adc=adc_name, ch=channel_key: self.config_manager.get_config()[
                adc
            ][ch]["scale"] * (x - V_START) / (V_END - V_START)
        elif scale_type == "c":
            conversion = lambda x, adc=adc_name, ch=channel_key: self.config_manager.get_config()[
                adc
            ][ch]["scale"] * (x - C_START) / (C_END - C_START)
        else:
            raise ValueError(f"scale_type must be 'v' or 'c', got {scale_type!r}")

        label_widget = ctk.CTkLabel(
            panel,
            text=_build_channel_label(channel_num, label_text),
            font=self._default_font,
        )
        value_widget = TextLastValue(
            panel,
            "",
            lambda pid=value_id, conv=conversion: get_display_data(
                self.parser, pid, conv
            ),
            font=self._default_font,
        )
        self.adc_widgets.append((label_widget, value_widget, adc_name, channel_num))
        return label_widget, value_widget

    def _execute_parser_command(self, action):
        """Run a parser command and update status label."""
        if not self.parser.connected:
            self._status_label.configure(text="not connected")
            return
        try:
            action()
        except Exception as e:
            traceback.print_exc()
            print(e)
            self._status_label.configure(text="error")
        else:
            self._status_label.configure(text="ok")

    def _send_switch_command(self, switch_id, state):
        self._execute_parser_command(lambda: self.parser.toggle_switch(switch_id, state))

    def _send_ignition_command(self):
        self._execute_parser_command(lambda: self.parser.ignite(0))

    def _send_step_command(self, stepper_id, entry_widget):
        delta = entry_widget.get()
        self._execute_parser_command(lambda: self.parser.motor_step(stepper_id, int(delta)))

    def _build_ui(self):
        # Config panel at top
        config_panel = ctk.CTkFrame(self, fg_color="transparent")
        self._config_path_var = tk.StringVar(value=self.config_manager.get_path())
        config_path_entry = ctk.CTkEntry(
            config_panel,
            textvariable=self._config_path_var,
            state="readonly",
            width=400,
            font=self._default_font,
        )
        config_path_entry.grid(row=0, column=1, padx=4, pady=4, sticky="ew")
        config_panel.grid_columnconfigure(1, weight=1)
        ctk.CTkButton(
            config_panel,
            text="Import Config",
            command=self._import_config,
            font=self._default_font,
            corner_radius=0,
        ).grid(row=0, column=0, padx=4, pady=4)
        config_panel.grid(row=0, column=0, columnspan=2, sticky="ew", padx=8, pady=4)
        adc_config = self.config_manager.get_config()

        self._status_label = ctk.CTkLabel(self, text="", font=self._default_font)
        self._status_label.grid(row=1, column=1, padx=4, sticky="ew")

        # ADC panels
        adc0_panel = ctk.CTkFrame(self, border_width=1)
        adc1_panel = ctk.CTkFrame(self, border_width=1)
        send_panel = ctk.CTkFrame(self, border_width=1)
        ctk.CTkLabel(
            adc0_panel, text="ADC0 readings", font=(self._font_name, 14, "bold")
        ).grid(row=0, column=0, columnspan=4, padx=16, pady=8)
        ctk.CTkLabel(
            adc1_panel, text="ADC1 readings", font=(self._font_name, 14, "bold")
        ).grid(row=0, column=0, columnspan=4, padx=16, pady=8)

        # ADC0 channels
        self._create_adc_widget(adc0_panel, 1, "ADC0", "value10", adc_config, scale_type="c")
        self._create_adc_widget(adc0_panel, 2, "ADC0", "value20", adc_config, scale_type="c")
        self._create_adc_widget(adc0_panel, 3, "ADC0", "value30", adc_config, scale_type="c")
        self._create_adc_widget(adc0_panel, 4, "ADC0", "value40", adc_config, scale_type="c")
        self._create_adc_widget(adc0_panel, 5, "ADC0", "value50", adc_config, scale_type="c")
        self._create_adc_widget(adc0_panel, 6, "ADC0", "value60", adc_config, scale_type="c")
        self._create_adc_widget(adc0_panel, 7, "ADC0", "value70", adc_config, scale_type="c")
        self._create_adc_widget(adc0_panel, 8, "ADC0", "value90", adc_config, scale_type="c")
        self._create_adc_widget(adc0_panel, 9, "ADC0", "value80", adc_config, scale_type="c")
        self._create_adc_widget(adc0_panel, 10, "ADC0", "value100", adc_config, scale_type="c")
        self._create_adc_widget(adc0_panel, 11, "ADC0", "value110", adc_config, scale_type="c")

        # ADC1 channels
        self._create_adc_widget(adc1_panel, 1, "ADC1", "value11", adc_config, scale_type="c")
        self._create_adc_widget(adc1_panel, 2, "ADC1", "value21", adc_config, scale_type="c")
        self._create_adc_widget(adc1_panel, 3, "ADC1", "value31", adc_config, scale_type="c")
        self._create_adc_widget(adc1_panel, 4, "ADC1", "value41", adc_config, scale_type="c")
        self._create_adc_widget(adc1_panel, 5, "ADC1", "value51", adc_config, scale_type="c")
        self._create_adc_widget(adc1_panel, 6, "ADC1", "value61", adc_config, scale_type="c")
        self._create_adc_widget(adc1_panel, 7, "ADC1", "value71", adc_config, scale_type="c")
        self._create_adc_widget(adc1_panel, 8, "ADC1", "value91", adc_config, scale_type="c")
        self._create_adc_widget(adc1_panel, 9, "ADC1", "value81", adc_config, scale_type="c")
        self._create_adc_widget(adc1_panel, 10, "ADC1", "value101", adc_config, scale_type="c")
        self._create_adc_widget(adc1_panel, 11, "ADC1", "value111", adc_config, scale_type="c")

        # Context labels
        context_text_0, context_text_1 = _context_label_texts(adc_config)
        context_label0 = ctk.CTkLabel(
            adc0_panel, text=context_text_0, font=self._default_font, justify="center"
        )
        context_label0.grid(row=7, column=0, columnspan=4, padx=16, pady=8)
        self.context_label_widgets.append((context_label0, "ADC0"))
        context_label1 = ctk.CTkLabel(
            adc1_panel, text=context_text_1, font=self._default_font, justify="center"
        )
        context_label1.grid(row=7, column=0, columnspan=4, padx=16, pady=8)
        self.context_label_widgets.append((context_label1, "ADC1"))

        # Grid layout for ADC0
        for i, (label_w, value_w, _, _) in enumerate[Any](self.adc_widgets[:11]):
            row = (i // 2) + 1
            col_left = (i % 2) * 2
            label_w.grid(row=row, column=col_left, padx=4, pady=4, sticky="w")
            value_w.grid(row=row, column=col_left + 1, padx=4, pady=4, sticky="w")
        # ADC1
        for i, (label_w, value_w, _, _) in enumerate[Any](self.adc_widgets[11:22]):
            row = (i // 2) + 1
            col_left = (i % 2) * 2
            label_w.grid(row=row, column=col_left, padx=4, pady=4, sticky="w")
            value_w.grid(row=row, column=col_left + 1, padx=4, pady=4, sticky="w")

        # Grid column configuration
        adc0_panel.grid_columnconfigure(1, minsize=120)
        adc0_panel.grid_columnconfigure(3, minsize=120)
        adc1_panel.grid_columnconfigure(1, minsize=120)
        adc1_panel.grid_columnconfigure(3, minsize=120)

        # Send panel: switches, steppers, ignition
        send_panel.grid_columnconfigure(0, weight=0)
        send_panel.grid_columnconfigure(1, weight=0)
        send_panel.grid_columnconfigure(2, weight=1)

        # Switch frame
        switch_frame = ctk.CTkFrame(send_panel)
        ctk.CTkLabel(
            switch_frame, text="Switches", font=(self._font_name, 14, "bold")
        ).grid(row=0, column=0, columnspan=6, pady=4)
        num_switches = 8
        switches_per_column = 4
        for switch_id in range(1, num_switches + 1):
            row = (switch_id - 1) % switches_per_column + 1
            col = (switch_id - 1) // switches_per_column
            ctk.CTkLabel(
                switch_frame, text=f"SW {switch_id}", font=self._default_font
            ).grid(row=row, column=col * 3 + 0, padx=4, pady=2, sticky="w")
            ctk.CTkButton(
                switch_frame,
                text="On",
                command=lambda i=switch_id: self._send_switch_command(i, True),
                width=50,
                font=self._default_font,
                corner_radius=0,
            ).grid(row=row, column=col * 3 + 1, padx=4, pady=2, sticky="ew")
            ctk.CTkButton(
                switch_frame,
                text="Off",
                command=lambda i=switch_id: self._send_switch_command(i, False),
                width=50,
                font=self._default_font,
                corner_radius=0,
            ).grid(row=row, column=col * 3 + 2, padx=4, pady=2, sticky="ew")
        switch_frame.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)

        # Stepper frame
        step_frame = ctk.CTkFrame(send_panel)
        ctk.CTkLabel(
            step_frame, text="Steppers", font=(self._font_name, 14, "bold")
        ).grid(row=0, column=0, columnspan=3, pady=4)
        stepper_entries = []
        for step_id in range(1, 4):
            row = step_id
            ctk.CTkLabel(
                step_frame, text=f"Stepper {step_id}", font=self._default_font
            ).grid(row=row, column=0, padx=4, pady=3, sticky="w")
            entry = ctk.CTkEntry(step_frame, width=60, font=self._default_font)
            entry.grid(row=row, column=1, padx=4, pady=3, sticky="ew")
            stepper_entries.append(entry)
            ctk.CTkButton(
                step_frame,
                text="Send",
                command=lambda i=step_id, e=entry: self._send_step_command(i, e),
                width=60,
                font=self._default_font,
                corner_radius=0,
            ).grid(row=row, column=2, padx=4, pady=3, sticky="ew")
        step_frame.grid(row=0, column=1, sticky="nsew", padx=12, pady=12)

        # Ignition frame
        ignition_frame = ctk.CTkFrame(send_panel)
        ctk.CTkLabel(
            ignition_frame, text="Ignition", font=(self._font_name, 14, "bold")
        ).pack(pady=4)
        ctk.CTkButton(
            ignition_frame,
            text="Ignite",
            command=self._send_ignition_command,
            width=150,
            font=self._default_font,
            corner_radius=0,
            state="disabled",
        ).pack(fill="x", padx=24, pady=6)
        ignition_frame.grid(row=0, column=2, sticky="nsew", padx=12, pady=12)

        # Grid column configuration
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Time
        time_label = TimeLastValue(
            self,
            "time: ",
            lambda: get_display_data(
                self.parser, "us_since_boot", lambda x: x / 1e6
            ),
            font=self._default_font,
        )
        time_label.grid(row=1, column=0)

        # Panels
        adc0_panel.grid(row=2, column=0, padx=(24, 12), pady=8, sticky="n")
        adc1_panel.grid(row=2, column=1, padx=(12, 24), pady=8, sticky="n")
        send_panel.grid(row=3, column=0, columnspan=2, pady=16, padx=24)


def main():
    com_port = sys.argv[1] if len(sys.argv) > 1 else None
    parser = SurtrParser(com_port)
    initial_config_path = os.path.join(os.path.dirname(__file__), "adc_config.json")
    app = SurtrDashboard(parser=parser, initial_config_path=initial_config_path)
    app.mainloop()


if __name__ == "__main__":
    main()
