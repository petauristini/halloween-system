import logging
import RPi.GPIO as GPIO
import time
import threading
from flask import Flask
import requests

logging.basicConfig(level=logging.INFO)

class GPIOPin:
    def __init__(self, pin):
        """Initialize a specified pin"""
        self.pin = pin
        self.stop_event = threading.Event()
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.OUT)
        self.turn_off()
        logging.debug(f"Initialised pin {self.pin}")

    def turn_on(self):
        """Turn on the pin until disabled"""
        self.stop_thread()
        GPIO.setmode(GPIO.BCM)
        GPIO.output(self.pin, True)
        logging.debug(f"Turned on pin {self.pin}")

    def turn_on_for(self, duration):
        """Turn on the pin for a specified number of seconds"""
        self.stop_thread()
        thread = threading.Thread(target=self._turn_on_for_thread, args=(duration,))
        thread.start()

    def _turn_on_for_thread(self, duration):
        logging.debug(f"Started new thread for pin {self.pin} that will stay on for {duration} seconds")
        self.turn_on()
        start_time = time.time()
        while time.time() - start_time < duration:
            if self.stop_event.is_set():
                logging.debug(f"Stopping the thread for {self.pin} prematurely after {time.time() - start_time} seconds because a second thread was started")
                break
            time.sleep(0.001)

        self.turn_off()

    def turn_off(self):
        """Turn off the pin until enabled"""
        self.stop_thread()
        GPIO.setmode(GPIO.BCM)
        GPIO.output(self.pin, False)
        logging.debug(f"Turned off pin {self.pin}")
    
    def stop_thread(self):
        """Stop thread by starting event"""
        self.stop_event.set()
        time.sleep(0.002)
        self.stop_event.clear()

    def cleanup(self):
        """Clean up GPIO pins used"""
        GPIO.cleanup()
        logging.debug(f"Cleaned up GPIOs")

class GPIOHandler:
    def __init__(self):
        self.outputs = {}

    def get_outputs(self):
        return self.outputs
    
    def _pin_exists(self, pin: int):
        return pin in self.outputs
    
    def add(self, pin: int):
        if self._pin_exists(pin):
            logging.warning(f"Pin {pin} is already exists")
            return
        self.outputs[pin] = GPIOPin(pin)
        logging.info(f"Pin {pin} created")

    def turn_on(self, pin: int):
        if not self._pin_exists(pin):
            logging.error(f"Pin '{pin}' not found")
        self.outputs[pin].turn_on()

    def turn_on_for(self, pin: str, duration: int):
        if not self._pin_exists(pin):
            logging.error(f"Pin '{pin}' not found")
        self.outputs[pin].turn_on_for(duration)

class GPIOHandlerServer:
    def __init__(self, app: Flask):
        self.app = app
        self.gpio_handler = GPIOHandler()
        self._setup_routes()

    def _setup_routes(self):

        @self.app.route('/api/raspigpio/ping', methods=['GET'])
        def ping_gpio_handler():
            return "", 200

        @self.app.route('/api/raspigpio/on', methods=['GET'])
        def turn_on_pin():
            pin = requests.args.get('pin')
            duration = requests.args.get('duration', None)
            if duration is not None:
                self.gpio_handler.turn_on_for(pin, duration)
            else:
                self.gpio_handler.turn_on(pin)
            return "", 200

        @self.app.route('/api/raspigpio/off', methods=['GET'])
        def turn_off_pin():
            pin = requests.args.get('pin')
            self.gpio_handler.turn_off(id)
            return "", 200
        
if __name__ == "__main__":
    app = Flask(__name__)
    server = GPIOHandlerServer(app, 17)