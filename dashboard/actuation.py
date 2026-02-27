
from constants import *
import re

# =========================================================================	
# ACTUATION
# {
#	    Switch:
#			button[8]
#		Stepper:
#			motor[3]
#		Ignition
#	}
# }
# =========================================================================	
# func_ignition() and func_stepper() not used right now.
class Actuation:
    def __init__(self, parent, func_ignition, func_switch, func_stepper, func_can):
        self.panel = ctk.CTkFrame(parent, border_width=1)
        self.switch = self.Switch(self.panel, func_switch)
        self.stepper = self.Stepper(self.panel, func_stepper)
        self.ignition = self.Ignition(self.panel, func_ignition)
        self.can = self.Can(self.panel, func_can)
    
    # =====================================================================
    class Switch:
        def __init__(self, parent, func):
            self.panel = ctk.CTkFrame(parent)
            self.title = ctk.CTkLabel(self.panel, text="Switches", font=DEFAULT_FONT_BOLD)
            self.button: list[Actuation.Switch.Button] = []
            for i in range(0, NUM_SWITCHES):
                bt = Actuation.Switch.Button(self.panel, i+1, f"SW {i+1}", func)
                self.button.append(bt)	

        # Function pointer for "switch_command()" is passed here.
        # It is then called as a lambda in order to supply arguments.
        # The tkinter switch works by calling "command" each time "variable" changes.
        # And the "variable" is set by the gui button to "onvalue" or "offvalue"
        class Button:
            def __init__(self, parent, id, label, func):
                self.id = id
                self.label 	= ctk.CTkLabel(parent, text=label, font=DEFAULT_FONT)
                self.disabled = False
                self.current_state = False
                self.on = ctk.CTkButton(
                    parent,
                    text="On",
                    command=lambda: func(self.id, True),
                    width=50,
                    font=DEFAULT_FONT,
                    corner_radius=0
                )
                self.off = ctk.CTkButton(
                    parent,
                    text="Off",
                    command=lambda: func(self.id, False),
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
    class Stepper:
        def __init__(self, parent, func):
            self.panel = ctk.CTkFrame(parent)
            self.title = ctk.CTkLabel(self.panel, text="Steppers", font=DEFAULT_FONT_BOLD)
            self.motor: list[Actuation.Stepper.Motor] = []
            for i in range(0,NUM_STEPPERS):
                bt = Actuation.Stepper.Motor(self.panel, f"STEP {i+1}", func)
                self.motor.append(bt)	
        
        class Motor:
            def __init__(self, parent, label, func):
                self.label 	= ctk.CTkLabel(parent, text=label, font=DEFAULT_FONT)
                self.entry  = ctk.CTkEntry(parent, width=60, font=DEFAULT_FONT)
                self.button = ctk.CTkButton(parent, text="Send", command=func, width=60, font=DEFAULT_FONT, corner_radius=0)
                self.disabled = False

            def update_label(self, label):
                self.label.configure(True, text=label)

            def set_disabled(self, disabled):
                self.disabled = disabled
                text_color = ("gray60", "gray45") if disabled else ("gray10", "gray90")
                entry_state = "disabled" if disabled else "normal"
                button_state = "disabled" if disabled else "normal"
                self.label.configure(text_color=text_color)
                self.entry.configure(state=entry_state)
                self.button.configure(state=button_state)

    # =====================================================================
    class Ignition:
            def __init__(self, parent, func):
                self.panel = ctk.CTkFrame(parent)
                self.title = ctk.CTkLabel(self.panel, text="Ignition", font=DEFAULT_FONT_BOLD)		
                self.button = ctk.CTkButton(
                    self.panel, 
                    text="Ignite", 
                    command=func, 
                    width=150, 
                    font=DEFAULT_FONT, 
                    corner_radius=0)
                self.disabled = False

            def update_label(self, label):
                self.button.configure(text=label)

            def set_disabled(self, disabled):
                self.disabled = disabled
                state = "disabled" if disabled else "normal"
                self.button.configure(state=state)

    # =====================================================================
    class Can:
            def __init__(self, parent, func_send):
                self.panel = ctk.CTkFrame(parent)
                self.title = ctk.CTkLabel(self.panel, text="CAN", font=DEFAULT_FONT_BOLD)
                can_id_vcmd = (self.panel.register(self._validate_can_id), "%P")
                msg_vcmd = (self.panel.register(self._validate_can_message), "%P")
                self.can_id_entry = ctk.CTkEntry(
                    self.panel,
                    width=100,
                    font=DEFAULT_FONT,
                    corner_radius=0,
                    placeholder_text="ID hex",
                    validate="key",
                    validatecommand=can_id_vcmd,
                )
                self.message_entry = ctk.CTkEntry(
                    self.panel,
                    width=230,
                    font=DEFAULT_FONT,
                    corner_radius=0,
                    placeholder_text="len(2B)+payload hex",
                    validate="key",
                    validatecommand=msg_vcmd,
                )
                self.send_button = ctk.CTkButton(
                    self.panel,
                    text="Send",
                    command=lambda: func_send(self.can_id_entry.get(), self.message_entry.get()),
                    width=70,
                    font=DEFAULT_FONT,
                    corner_radius=0
                )

            def _validate_can_id(self, proposed: str):
                if proposed == "":
                    return True
                return re.fullmatch(r"(0[xX])?[0-9a-fA-F]*", proposed) is not None

            def _validate_can_message(self, proposed: str):
                if proposed == "":
                    return True
                if re.fullmatch(r"[0-9a-fA-FxX,\s]*", proposed) is None:
                    return False

                has_separators = ("," in proposed) or (" " in proposed)
                if not has_separators:
                    return re.fullmatch(r"(0[xX])?[0-9a-fA-F]*", proposed) is not None

                tokens = [tok for tok in re.split(r"[\s,]+", proposed.strip()) if tok]
                for tok in tokens:
                    if re.fullmatch(r"(0[xX])?[0-9a-fA-F]{0,2}", tok) is None:
                        return False
                return True