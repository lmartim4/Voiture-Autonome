from control import activate_reverse, deactivate_reverse

class KeyboardController:
    def __init__(self, console, interface):
        self.console = console
        self.interface = interface
        self.listener = keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release
        )
    
    def start(self):
        self.listener.start()

    def on_press(self, key):
        global running
        
        try:
            if key.char == 'w':
                self.forward()
            elif key.char == 's':
                self.backward()
            elif key.char == 'a':
                self.left()
            elif key.char == 'd':
                self.right()

        except AttributeError:
            if key == keyboard.Key.enter and not running:
                running = True
                self.console.info("Running...")
                self.console.info("Press CTRL+C to stop the code")

    def on_release(self, key):
        try:
            if key.char in ['a', 'd']:
                # Return steering to neutral
                self.interface["steer"].set_duty_cycle((DC_STEER_MAX + DC_STEER_MIN)/2)
        except AttributeError:
            pass
        
        try:
            if key.char == 's':
                deactivate_reverse(self.interface["speed"])
        except AttributeError:
            pass
        
        try:
            if key.char == 'w':
                self.interface["speed"].set_duty_cycle(7.5)
        except AttributeError:
            pass

        if key == keyboard.Key.esc:
            return False

    def forward(self):
        self.console.info("Going forward!")
        self.interface["speed"].set_duty_cycle(DC_SPEED_MAX)
    
    def backward(self):
        activate_reverse(self.interface["speed"])	
        
    def left(self):
        self.console.info("Turning left!")
        self.interface["steer"].set_duty_cycle(DC_STEER_MIN)

    def right(self):
        self.console.info("Turning right!")
        self.interface["steer"].set_duty_cycle(DC_STEER_MAX)