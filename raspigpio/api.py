import requests
import logging

logging.basicConfig(level=logging.INFO)


class GPIOPin:
    def __init__(self, ip: str, port: int, pin: int):
        self.server = (ip, port)
        self.pin = pin

    def check_connection(self):
        url = f"http://{self.server[0]}:{self.server[1]}/api/raspigpio/ping"
        try:
            res = requests.get(url)
            if not res.ok:
                logging.error(f"Error pinging pin {self.pin}")
        except Exception as e:
            logging.error(f"Connection error: {e}")

    def turn_on(self):
        url = f"http://{self.server[0]}:{self.server[1]}/api/raspigpio/on/?pin={self.pin}"
        try:
            res = requests.get(url)
            if not res.ok:
                logging.error(f"Error turning on pin {self.pin}")
        except Exception as e:
            logging.error(f"Connection error: {e}")

    def turn_off(self):
        url = f"http://{self.server[0]}:{self.server[1]}/api/raspigpio/off?pin={self.pin}"
        try:
            res = requests.get(url)
            if not res.ok:
                logging.error(f"Error turning off pin {self.pin}")
        except Exception as e:
            logging.error(f"Connection error: {e}")

    def turn_on_for(self, duration: int):
        url = f"http://{self.server[0]}:{self.server[1]}/api/raspigpio/on?pin={self.pin}&duration={duration}"
        try:
            res = requests.get(url)
            if not res.ok:
                logging.error(f"Error turning on pin {self.pin}")
        except Exception as e:
            logging.error(f"Connection error: {e}")

class GPIOGroup:
    def __init__(self, pins: list):
        self.pins = pins

    def check_connection(self):
        result = []
        for pin in self.pins:
            result.append(pin.check_connection())
        return result
    
    def turn_on(self):
        for pin in self.pins:
            pin.turn_on()

    def turn_on_for(self, duration: int):
        for pin in self.pins:
            pin.turn_on_for(duration)

    def turn_off(self):
        for pin in self.pins:
            pin.turn_off()
    
