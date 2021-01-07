try: 
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
except:
    pass
from time import sleep
from typing import Callable

from utils import current_millis, increase_test_millis_by, print_debug

class BikeSensor():
    def __init__(self, idle_time: int, pin: int, debug_sensor: bool = False) -> None:
        try: 
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        except:
            pass

        self.debug_sensor = debug_sensor
        self.pin = pin
        self.idle_time = idle_time
        self.previous_handled_time = None
        self.paused = False
        self.recording = False
        self.is_idle = False
        self.on_revolution: Callable[[float],None] = None
        self.on_idle: Callable[[bool],None] = None
        self.on_first_rev: Callable[[],None] = None
        self.initialise()

    def initialise(self):
        self.current_state = -1
        self.off_time = -1

    def pause(self):
        self.paused = True
        self.initialise()
    
    def resume(self):
        self.initialise()
        self.paused = False

    def _handle_new_state(self, new_state):
        if self.paused:
            return
        
        handled_state = True

        increase_test_millis_by(750)

        if new_state != self.current_state and new_state == 1:
            if self.off_time == -1:
                if self.is_idle:
                    self.on_idle(False)
                    self.is_idle = False
                elif self.on_first_rev:
                    self.on_first_rev(-1)
                self.off_time = current_millis()
            else:
                time_in_seconds = (current_millis() - self.off_time) / 1000
                if self.on_revolution:
                    self.on_revolution(time_in_seconds)
                self.off_time = current_millis()
            sleep(0.2)
        else:
            handled_state = False
            sleep(0.1)
        self.current_state = new_state

        return handled_state

    def start(self):
        if self.recording:
            return
        print_debug("Start recording bike sensor")

        self.recording = True

        if not self.debug_sensor:
            if not self.previous_handled_time:
                self.previous_handled_time = current_millis()
                
            while self.recording:
                if not self._handle_new_state(GPIO.input(self.pin)):
                    if current_millis() - self.previous_handled_time > self.idle_time:
                        if self.on_idle and not self.is_idle:
                            print_debug('idle')
                            self.is_idle = True
                            self.initialise()
                            self.on_idle(True)
                else:
                    self.previous_handled_time = current_millis()
        else:
            i = 0
            while self.recording:
                if self.is_idle:
                    self.is_idle = False
                    self.on_idle(False)
                if i % 2 != 0 and i != 0:
                    self._handle_new_state(1)
                else:
                    self._handle_new_state(0)
                i += 1
                sleep(0.5)
        print_debug("End recording bike sensor")
        
    def stop(self):
        self.recording = False

if __name__ == '__main__':
    sensor = BikeSensor()
    sensor.on_revolution = print
    sensor.start()
