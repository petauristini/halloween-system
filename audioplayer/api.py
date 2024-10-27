import requests
import logging

logging.basicConfig(level=logging.INFO)

class AudioServer:

    def __init__(self, ip: str, port: int):
        self.ip = ip
        self.port = port

    def play(self, file: str, volume: float=1, loops=0):
        try:
            res = requests.get(f'http://{self.ip}:{self.port}/api/audioplayer/play', params={'file': file, 'volume': volume, 'loops': loops})
            if not res.ok:
                logging.error(f"Error playing file '{file}'")
        except Exception as e:
            logging.error(f"Connection error: {e}")

    def stop(self, file: str):
        try:
            res = requests.get(f'http://{self.ip}:{self.port}/api/audioplayer/stop', params={'file': file})
            if not res.ok:
                logging.error(f"Error stopping file '{file}'")
        except Exception as e:
            logging.error(f"Connection error: {e}")

    def check_connection(self):
        try:
            res = requests.get(f'http://{self.ip}:{self.port}/api/audioplayer/ping')
            return res.ok
        except Exception as e:
            logging.error(f"Connection error: {e}")

    def update(self):
        try:
            res = requests.get(f'http://{self.ip}:{self.port}/api/audioplayer/update')
            if not res.ok:
                logging.error(f"Error updating files")
        except Exception as e:
            logging.error(f"Connection error: {e}")

class AudioServerGroup:

    def __init__(self, servers: list[AudioServer]):
        self.servers = servers

    def play(self, file: str, volume: float=1, loops=0):
        for server in self.servers:
            server.play(file, volume)


    def stop(self, file: str):
        for server in self.servers:
            server.stop(file)

    def check_connection(self):
        results = []
        for server in self.servers:
            results.append(server.check_connection())
        return results

    def update(self):
        for server in self.servers:
            server.update()


if __name__ == '__main__':
    server = AudioServer('localhost', 5000)
    while True:
        eval(input(">>"))