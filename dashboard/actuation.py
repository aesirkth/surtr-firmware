
from constants import *

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
    def __init__(self, parent, func_ignition, func_switch, func_stepper):
        self.panel = ctk.CTkFrame(parent, border_width=1)
        self.switch = self.Switch(self.panel, func_switch)
        self.stepper = self.Stepper(self.panel, func_stepper)
        self.ignition = self.Ignition(self.panel, func_ignition)
    
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
                self.sw_state = ctk.BooleanVar(value=False)
                self.sw = ctk.CTkSwitch(
                    parent, 
                    variable=self.sw_state, 
                    command=lambda: func(self.id, self.sw_state.get()),
                    onvalue=True, 
                    offvalue=False, 
                    width=50, 
                    font=DEFAULT_FONT, 
                    corner_radius=0)

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