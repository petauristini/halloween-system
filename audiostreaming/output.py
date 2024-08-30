import socket
import threading
import pyaudio
import pickle
import struct
import atexit
from flask import Flask, request, jsonify
import re

class StreamingOutput:
    def __init__(self, server: tuple, outputDevice=0, chunk=1024, format=pyaudio.paInt16, channels=1, rate=44100):
        self.server = server
        self.outputDevice = outputDevice
        self.chunk = chunk
        self.format = format
        self.channels = channels
        self.rate = rate
        self.stopThreadFlag = threading.Event()
        self.clientThread = None

        self.stopThreadFlag.clear()
        self.clientThread = threading.Thread(target=self._audio_stream, args=())
        self.clientThread.start()
        
        atexit.register(self.stop)

    def _audio_stream(self):
        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(format=self.format,
                                      channels=self.channels,           
                                      rate=self.rate,
                                      output=True,
                                      frames_per_buffer=self.chunk)
        self.clientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socketAddress = self.server
        print('Connecting to server at', self.socketAddress)
        self.clientSocket.sendto(b"Client connected", self.socketAddress)

        data = b""
        payload_size = struct.calcsize("Q")

        while not self.stopThreadFlag.is_set():

            self.clientSocket.sendto(b"Client connected", self.socketAddress) # Possible optimization

            try:
                while len(data) < payload_size:
                    packet, _ = self.clientSocket.recvfrom(4 * 1024)
                    if not packet: break
                    data += packet

                packed_msg_size = data[:payload_size]
                data = data[payload_size:]
                msg_size = struct.unpack("Q", packed_msg_size)[0]

                while len(data) < msg_size:
                    packet, _ = self.clientSocket.recvfrom(4 * 1024)
                    if not packet: break
                    data += packet

                frame_data = data[:msg_size]    
                data = data[msg_size:]
                frame = pickle.loads(frame_data)
                self.stream.write(frame)

            except Exception as e:
                print(f"Error: {e}")
                break

    def stop(self):
            self.stopThreadFlag.set()
            self.clientThread.join()
            self.clientSocket.close()
            self.stream.stop_stream()
            self.stream.close()
            self.audio.terminate()

class StreamingOutputHandler:
    def __init__(self):
        self.streams = {}

    def start(self, server, outputDevice=0, chunk=1024, format=pyaudio.paInt16, channels=1, rate=44100):
        if not self._stream_exists(server):
            self.streams[server] = StreamingOutput(server, outputDevice, chunk, format, channels, rate)
        else:
            print(f"Stream with server {server} already running")   

    def stop(self, server):
        if self._stream_exists(server):
            self.streams[server].stop()
            del self.streams[server]
        else:
            print(f"Stream with server {server} not running")

    def delete(self, server):
        if self._stream_exists(server):
            self.streams[server].stop()
            del self.streams[server]
        else:
            print(f"Stream with server {server} not running")

    def id_exists(self, id):
        return id in self.streams

    def get_all(self):
        return self.streams
    def _stream_exists(self, server):
        return server in self.streams

class AudioStreamingOutputServer:
    def __init__(self, app: Flask):
        self.app = app
        self.stream_client_handler = StreamingOutputHandler()
        self._setup_routes()

    def _validate_ip(self, ip: str):
        pattern = re.compile(r'^(\d{1,3}\.){3}\d{1,3}$')
    
        if not pattern.match(ip):
            return False
        
        octets = ip.split('.')
        
        for octet in octets:
            if not 0 <= int(octet) <= 255:
                return False
        
        return True
    
    def _validate_port(self, port: int):
        return 0 <= port <= 65535  
      
    def _setup_routes(self):
        
        @self.app.route('/api/streamingoutput/ping', methods=['GET'])
        def ping():
            return "", 200
        
        @self.app.route('/api/streamingoutput/start', methods=['GET'])
        def start():
            ip = request.args.get('ip')
            port = request.args.get('port')
            
            print (ip, port)
            if not ip or not port:
                return jsonify(error="Missing IP or port"), 400
            
            if not ( self._validate_ip(ip) and self._validate_port(int(port)) ):
                return jsonify(error="Invalid IP or port"), 400

            server = (ip, int(port))

            self.stream_client_handler.start(server)

            return "", 200
        
        @self.app.route('/api/streamingoutput/stop', methods=['GET'])
        def stop():
            ip = request.args.get('ip')
            port = request.args.get('port')

            if not ( self._validate_ip(ip) and self._validate_port(int(port)) ):
                return jsonify(error="Invalid IP or port"), 400

            server = (ip, int(port))

            self.stream_client_handler.stop(server)

            return "", 200

if __name__ == '__main__':
    app = Flask(__name__)
    server = AudioStreamingOutputServer(app)
    app.run(debug=True)
