import RPi.GPIO as GPIO
import time
import threading

class SmokeModule:
    def __init__(self, pin):
        GPIO.setmode(GPIO.BCM)
        self.terminate = False
        self.pin = pin
        GPIO.setup(self.pin, GPIO.OUT)
        self.turn_off()

    def turn_on(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.output(self.pin, True)
        print(f"GPIO pin {self.pin} is ON")

    def turn_on_for(self, duration):
        self.terminate = True
        time.sleep(0.02)
        self.terminate = False
        thread = threading.Thread(target=self._turn_on_for_thread, args=(duration,))
        thread.start()

    def _turn_on_for_thread(self, duration):
        self.turn_on()
        print(f"GPIO pin {self.pin} will stay ON for {duration} seconds")
        start_time = time.time()
        while time.time() - start_time < duration:
            if self.terminate == True:
                print(f"Stopping the thread prematurely after {time.time() - start_time} seconds.")
                break
            time.sleep(0.01)  # Sleep a bit to avoid busy-waiting

        self.turn_off()

    def turn_off(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.output(self.pin, False)
        print(f"GPIO pin {self.pin} is OFF")

    def cleanup(self):
        GPIO.cleanup()
        print("GPIO cleanup done.")

"""# Example usage:
if __name__ == "__main__":
    # Create a SmokeModule object controlling GPIO pin 17
    smoke_module = SmokeModule(17)
    smoke_module2 = SmokeModule(27)
    
    smoke_module.turn_on()
    smoke_module2.turn_on()

    time.sleep(3)

    smoke_module.turn_off()
    smoke_module2.turn_off()

    time.sleep(2)
    
    smoke_module.turn_on_for(5)
    time.sleep(4)
    smoke_module.turn_on_for(5)"""