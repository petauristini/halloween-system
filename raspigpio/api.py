import requests
import logging

logging.basicConfig(level=logging.INFO)


class GPIOPin:
    def __init__(self, ip: str, port: int, id: int):
        self.ip = ip
        self.port = port
        self.id = id
        self.base_url = f"http://{self.ip}:{self.port}/api/gpio/{self.id}"

    def check_connection(self):
        try:
            res = requests.get(f"{self.base_url}/ping")
            if not res.ok:
                logging.error(f"Error pinging pin {self.id}")
        except Exception as e:
            logging.error(f"Connection error: {e}")

    def turn_on(self, duration: int = None):
        try:
            res = requests.get(f"{self.base_url}/on")
            if not res.ok:
                logging.error(f"Error turning on pin {self.id}")
        except Exception as e:
            logging.error(f"Connection error: {e}")

    def turn_on_for(self, duration: int):
        try:
            res = requests.get(f"{self.base_url}/on?duration={duration}")
            if not res.ok:
                logging.error(f"Error turning on pin {self.id}")
        except Exception as e:
            logging.error(f"Connection error: {e}")

    def turn_off(self):
        try:
            res = requests.get(f"{self.base_url}/off")
            if not res.ok:
                logging.error(f"Error turning off pin {self.id}")
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
    
