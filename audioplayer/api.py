import requests

class AudioServer:

    def __init__(self, ip: str, port: int):
        self.ip = ip
        self.port = port

    def play(self, file: str, volume: float=1):
        try:
            response = requests.get(f'http://{self.ip}:{self.port}/api/play', params={'file': file, 'volume': volume})
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Error playing file '{file}'")

    def stop(self, file: str):
        try:
            response = requests.get(f'http://{self.ip}:{self.port}/api/stop', params={'file': file})
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Error stopping file '{file}'")

    def check_connection(self):
        try:
            response = requests.get(f'http://{self.ip}:{self.port}/api/ping')
            response.raise_for_status()
            return response.ok
        except requests.RequestException as e:
            print(f"Error checking connection")

if __name__ == '__main__':
    server = AudioServer('localhost', 5000)
    while True:
        eval(input(">>"))