import logging
import RPi.GPIO as GPIO
import time
import threading

logging.basicConfig(level=logging.INFO)


class SmokeModule:
    def __init__(self, pin):
        """Initialize a Smoke Module on a specified pin"""
        GPIO.setmode(GPIO.BCM)
        self.stop_event = threading.Event()
        self.pin = pin
        GPIO.setup(self.pin, GPIO.OUT)
        self.turn_off()
        logging.debug(f"initialised smoke module on pin {self.pin}")

    def turn_on(self):
        """Turn on the smoke module until disabled"""
        self.stop_thread()
        GPIO.setmode(GPIO.BCM)
        GPIO.output(self.pin, True)
        logging.debug(f"turned on smoke module on pin {self.pin}")

    def turn_on_for(self, duration):
        """Turn on the smoke module for a specified number of seconds"""
        self.stop_thread()
        thread = threading.Thread(target=self._turn_on_for_thread, args=(duration,))
        thread.start()

    def _turn_on_for_thread(self, duration):
        logging.debug(f"started new thread for pin {self.pin} that will stay on for {duration} seconds")
        self.turn_on()
        start_time = time.time()
        while time.time() - start_time < duration:
            if self.stop_event.is_set():
                logging.debug(f"stopping the thread for {self.pin} prematurely after {time.time() - start_time} seconds because a second thread was started")
                break
            time.sleep(0.001)

        self.turn_off()

    def turn_off(self):
        """Turn off the module until enabled"""
        self.stop_thread()
        GPIO.setmode(GPIO.BCM)
        GPIO.output(self.pin, False)
        logging.debug(f"turned off smoke module on pin {self.pin}")
    
    def stop_thread(self):
        """Stop thread by starting event"""
        self.stop_event.set()
        time.sleep(0.002)
        self.stop_event.clear()

    def cleanup(self):
        """Clean up GPIO pins used"""
        GPIO.cleanup()
        logging.debug(f"cleaned up GPIOs")