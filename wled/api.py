import logging
import requests

class Wled:
    def __init__(self, ip):
        self.ip = ip
        self.base_url = f'http://{self.ip}/win'

    def check_connection(self):
        try:
            res = requests.get(f'http://{self.ip}:80')
            return res.ok
        except Exception as e:
            logging.error(f"Connection error: {e}")

    def on(self):
        url = f'{self.base_url}&T=1'
        try:
            res = requests.get(url)
            if not res.ok:
                logging.error(f"Error turning on")
        except Exception as e:
            logging.error(f"Connection error: {e}")

    def off(self):
        url = f'{self.base_url}&T=0' 
        print(url)
        try:
            res = requests.get(url)
            if not res.ok:
                logging.error(f"Error turning off")
        except Exception as e:
            logging.error(f"Connection error: {e}")
        
    def brightness(self, brightness: int):

        if brightness not in range(0, 255):
            logging.error(f"Invalid brightness value: {brightness}")
        
        url = f'{self.base_url}&A={brightness}'
        try:
            res = requests.get(url)
            if not res.ok:
                logging.error(f"Error setting brightness")
        except Exception as e:
            logging.error(f"Connection error: {e}")

    def preset(self, preset: int):
        url = f'{self.base_url}&PL={preset}'
        try:
            res = requests.get(url)
            if not res.ok:
                logging.error(f"Error setting preset")
        except Exception as e:
            logging.error(f"Connection error: {e}")

    def color(self, color: tuple):
        url = f'{self.base_url}&R={color[0]}&G={color[1]}&B={color[2]}'
        try:
            res = requests.get(url)
            if not res.ok:
                logging.error(f"Error setting color")
        except Exception as e:
            logging.error(f"Connection error: {e}")

class WledGroup:
    def __init__(self, wleds: list[Wled]):
        self.wleds = wleds

    def check_connection(self):
        results = []
        for w in self.wleds:
            results.append(w.check_connection())
        return results

    def on(self):
        for w in self.wleds:
            w.on()

    def off(self):
        for w in self.wleds:
            w.off()

    def brightness(self, brightness: int):
        for w in self.wleds:
            w.brightness(brightness)

    def preset(self, preset: int):
        for w in self.wleds:
            w.preset(preset)

    def color(self, color: tuple):
        for w in self.wleds:
            w.color(color)

if __name__ == "__main__":
    w = Wled("<ip>")
    w.on()