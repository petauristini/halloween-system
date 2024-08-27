import socket
import threading
import pyaudio
import pickle
import struct
import atexit
import time
import requests

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Connect to an external address; it won't actually send data
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
    except Exception:
        local_ip = "127.0.0.1"  # Fallback to localhost
    finally:
        s.close()
    return local_ip

class StreamClient:
    def __init__(self, id, server: tuple, outputDevice=0, chunk=1024, format=pyaudio.paInt16, channels=1, rate=44100):
        self.id = id
        self.server = server
        self.outputDevice = outputDevice
        self.chunk = chunk
        self.format = format
        self.channels = channels
        self.rate = rate
        self.stopThreadFlag = threading.Event()
        self.clientThread = None
        atexit.register(self.on_exit)

    def audio_stream(self):
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

        # Clean up
        self.clientSocket.close()
        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()
        print('Closed Succesfully   ')
    def start(self):

        if self.clientThread and self.clientThread.is_alive():
            return
        
        try:
            self.stopThreadFlag.clear()
            self.clientThread = threading.Thread(target=self.audio_stream, args=())
            self.clientThread.start()
        except:
            print ("Error: unable to start thread")

        

    def stop(self):
        if not self.stopThreadFlag.is_set():
            self.stopThreadFlag.set()
            self.clientThread.join()
            return "Terminated Succesfully", 200
        else:
            return "Already Terminated", 200
    
    def on_exit(self):
        if self.clientThread and self.clientThread.is_alive():
            self.stop()

class StreamClientHandler:
    def __init__(self):
        self.streamClients = {}

    def add(self, id, server, outputDevice=0, chunk=1024, format=pyaudio.paInt16, channels=1, rate=44100):
        if id is None:
            raise ValueError("ID cannot be None")
        elif self.id_exists(id):
            raise ValueError("ID already in use")
        else:
            self.streamClients[id] = StreamClient(id, server, outputDevice, chunk, format, channels, rate)
        
    def start(self, id):
        if self.id_exists(id):
            self.streamClients[id].start()
        else:
            raise ValueError("ID not found")
        
    def stop(self, id):
        if self.id_exists(id):
            self.streamClients[id].stop()
        else:
            raise ValueError("ID not found")
        
    def delete(self, id):
        if self.id_exists(id):
            del self.streamClients[id]
        else:
            raise ValueError("ID not found")
        
    def id_exists(self, id):
        return id in self.streamClients

class StreamServer:

    def __init__(self, inputId, inputName, port=0, chunk=1024, format=pyaudio.paInt16, channels=1, rate=44100):
        self.inputId = inputId
        self.inputName = inputName
        self.ip = get_local_ip()
        self.port = port
        self.chunk = chunk
        self.format = format
        self.channels = channels
        self.rate = rate
        self.stopThreadFlag = threading.Event()
        self.serverThread = None
        self.clients = set()
        atexit.register(self.on_exit)

    def audio_stream(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_socket.bind((self.ip, self.port))
        self.port = server_socket.getsockname()[1]
        server_socket.setblocking(False)

        audio = pyaudio.PyAudio()
        print('Server listening at', (self.ip, self.port))
        stream = audio.open(format=self.format,
                            channels=self.channels,
                            rate=self.rate,
                            input=True,
                            frames_per_buffer=self.chunk)
        
        client_addr = None

        while not self.stopThreadFlag.is_set():

            #Check For New Clients and update existing ones
            try:
                data, client_addr = server_socket.recvfrom(1024)

                existing_client = next((item for item in self.clients if item[0] == client_addr), None)
                current_time = time.time()
                client = (client_addr, current_time)

                if existing_client:
                    self.clients.remove(existing_client)
                else:
                    print(f'Client {client} connected') 

                self.clients.add(client)
                    
            except BlockingIOError:
                pass
            
            #Remove Timed Out Clients
            timedOutClients = {i for i in self.clients if time.time() - i[1] > 3}
            for client in timedOutClients:
                self.clients.remove(client)
                print(f'Client {client} disconnected')

            data = stream.read(self.chunk)

            a = pickle.dumps(data)
            message = struct.pack("Q", len(a)) + a
            for i in self.clients:  
                server_socket.sendto(message, i[0])

    def start(self):
        if self.serverThread and self.serverThread.is_alive():
            print(f"Stream with inputId {self.inputId} already exists")
        try:
            self.stopThreadFlag.clear()
            self.serverThread = threading.Thread(target=self.audio_stream, args=())
            self.serverThread.start()
            print(f"Server {self.inputId} : {self.inputName} started")
        except:
            print ("Error: unable to create thread")     

    def stop(self):
        if not self.stopThreadFlag.is_set():
            self.stopThreadFlag.set()
            self.serverThread.join()
            print(f"Server {self.inputId} : {self.inputName} stopped")
        else:
            print(f"Server {self.inputId} : {self.inputName} already stopped")
    
    def on_exit(self):
        if self.serverThread and self.serverThread.is_alive():
            self.stop()

class StreamServerHandler:
    def __init__(self, mainServer):
        self.mainServer = mainServer
        self.mainServerConnected = False
        self.channels = ["channel1", "channel2", "channel3", "channel4"]
        self.servers = {}

        self.lastRegistration = 0
        self.registrationInterval = 3
        self.registrationThreadStopFlag = threading.Event()
        self.registrationThread = threading.Thread(target=self.register_inputs, daemon=True)
        self.registrationThread.start()

    def add(self, inputId, inputName, port=0, chunk=1024, format=pyaudio.paInt16, channels=1, rate=44100):
        if inputId is None:
            raise ValueError("inputId cannot be None")
        elif self.input_in_use(inputId):
            raise ValueError("input already in use")
        else:
            self.servers[inputId] = StreamServer(inputId, inputName, port, chunk, format, channels, rate)

    def start(self, inputId):
        if self.input_in_use(inputId):
            self.servers[inputId].start()
        else:
            raise ValueError("inputId not found")
        
    def stop(self, inputId):
        if self.input_in_use(inputId):
            self.servers[inputId].stop()
        else:
            raise ValueError("inputId not found")
        
    def delete(self, inputId):
        self.stop(inputId)
        if self.input_in_use(inputId):
            del self.servers[inputId]
        else:
            raise ValueError("inputId not found")
        
    def get_port(self, inputId):
        if self.input_in_use(inputId):
            return self.servers[inputId].port
        else:
            raise ValueError("inputId not found")
        
    def input_in_use(self, inputId):
        return inputId in self.servers
    
    def register_inputs(self):
        while not self.registrationThreadStopFlag.is_set():
            current_time = time.time()
            if current_time - self.lastRegistration > self.registrationInterval:
                serversCopy = self.servers.copy()
                serverList = [{'inputId': server.inputId, 'inputName': server.inputName, 'port': server.port, 'ip': server.ip} for server in serversCopy.values()]

                url = f'http://{self.mainServer[0]}:{self.mainServer[1]}/register/input'
                try:
                    response = requests.post(url, json=serverList, timeout=2)  # Added timeout
                    if response.status_code == 200:
                        self.mainServerConnected = True
                    else:
                        self.mainServerConnected = False
                except requests.RequestException as e:
                    print(f"Request error: {e}")
                    self.mainServerConnected = False
                except Exception as e:
                    print(f"Unexpected error: {e}")
                    self.mainServerConnected = False

                self.lastRegistration = current_time

    def update_main_server(self, mainServer):
        self.mainServer = mainServer
        print(f"Main server updated to {self.mainServer}")

    def terminate(self):
        for i in self.servers:
            self.stop(i)
        if not self.registrationThreadStopFlag.is_set():
            self.registrationThreadStopFlag.set()
            self.registrationThread.join(timeout=5)  # Added timeout
            if self.registrationThread.is_alive():
                print("Thread did not terminate in time, forcefully terminating.")
                # You might need additional measures here if the thread is still running
        print("Registration thread terminated")
       
if __name__ == '__main__':
    audioStreamServerHandler = StreamServerHandler({'ip': '127.0.0.1', 'port': 5000})
    audioStreamServerHandler.add(inputId=1, inputName='input1', port=7000)
    audioStreamServerHandler.start(1)

    # audioStreamHandler = StreamClientHandler()
    # audioStreamHandler.add(id=1, server=('192.168.1.117', 7000))
    # audioStreamHandler.start(1)   