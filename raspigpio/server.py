import logging
import RPi.GPIO as GPIO
import time
import threading
from flask import Flask, request

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

class GPIOPinServer:
    def __init__(self, app: Flask, pin: int, id: str):
        self.app = app
        self.id = id
        self.pin = pin
        self.gpio_pin = GPIOPin(pin)
        self._setup_routes()

    def _setup_routes(self):

        self.app.route(f'/api/gpio/{self.id}/ping', methods=['GET'], endpoint=f'ping_gpio_{self.id}')(
            lambda: ("", 200)
        )

        self.app.route(f'/api/gpio/{self.id}/on', methods=['GET'], endpoint=f'turn_on_gpio_{self.id}')(
            lambda: self._handle_turn_on()
        )

        self.app.route(f'/api/gpio/{self.id}/off', methods=['GET'], endpoint=f'turn_off_gpio_{self.id}')(
            lambda: self._handle_turn_off()
        )

    def _handle_turn_on(self):
        duration = request.args.get('duration', None)
        if duration is not None:
            self.gpio_pin.turn_on_for(int(duration))
        else:
            self.gpio_pin.turn_on()
        return "", 200

    def _handle_turn_off(self):
        self.gpio_pin.turn_off()
        return "", 200


        
if __name__ == "__main__":
    app = Flask(__name__)
    server = GPIOPinServer(app, 2, "test")
    server2 = GPIOPinServer(app, 3, "test2")
    app.run(debug=True, host='0.0.0.0', port=5001)