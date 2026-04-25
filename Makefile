
all:
	west build -b launchpad_controller ./application/launchpad_controller -p always 

flash:
	west build -b launchpad_controller ./application/launchpad_controller -p always -t flash

