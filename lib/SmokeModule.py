import logging
import RPi.GPIO as GPIO
import time
import threading

logging.basicConfig(level=logging.INFO)

class SmokeModule:
    def __init__(self, pin):
        GPIO.setmode(GPIO.BCM)
        self.terminate = False
        self.pin = pin
        GPIO.setup(self.pin, GPIO.OUT)
        self.turn_off()
        logging.debug(f"initialised smoke module on pin {self.pin}")

    def turn_on(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.output(self.pin, True)
        logging.debug(f"turned on smoke module on pin {self.pin}")

    def turn_on_for(self, duration):
        self.terminate = True
        time.sleep(0.02)
        self.terminate = False
        thread = threading.Thread(target=self._turn_on_for_thread, args=(duration,))
        thread.start()

    def _turn_on_for_thread(self, duration):
        logging.debug(f"started new tread for pin {self.pin} that will stay on for {duration} seconds")
        self.turn_on()
        start_time = time.time()
        while time.time() - start_time < duration:
            if self.terminate == True:
                logging.debug(f"stopping the thread for {self.pin} prematurely after {time.time() - start_time} seconds because a second thread was started")
                break
            time.sleep(0.01)
        self.turn_off()

    def turn_off(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.output(self.pin, False)
        logging.debug(f"turned off smoke module on pin {self.pin}")

    def cleanup(self):
        GPIO.cleanup()
        logging.debug(f"cleaned up GPIOs")
