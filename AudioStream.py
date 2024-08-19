import socket
import threading
import pyaudio
import pickle
import struct
import atexit
import time

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
                                      frames_per_buffer=self.chunk,
                                      output_device_index=self.outputDevice)
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

    def add(self, id, server, chunk=1024, format=pyaudio.paInt16, channels=1, rate=44100):
        if id is None:
            raise ValueError("ID cannot be None")
        elif self.id_exists(id):
            raise ValueError("ID already in use")
        else:
            self.streamClients[id] = StreamClient(id, server, chunk, format, channels, rate)
        
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

    def __init__(self, id, port, chunk=1024, format=pyaudio.paInt16, channels=1, rate=44100):
        self.id = id
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
            print(f"Stream with id {self.id} already exists")
        try:
            self.stopThreadFlag.clear()
            self.serverThread = threading.Thread(target=self.audio_stream, args=())
            self.serverThread.start()
        except:
            print ("Error: unable to create thread")     

    def stop(self):
        if not self.stopThreadFlag.is_set():
            self.stopThreadFlag.set()
            self.serverThread.join()
            print(f"Server with id {self.id} stopped")
        else:
            print(f"Server with id {self.id} already stopped")
    
    def on_exit(self):
        if self.serverThread and self.serverThread.is_alive():
            self.stop()

class StreamServerHandler:

    def __init__(self):
        self.servers = {}

    def add(self, id, port, chunk=1024, format=pyaudio.paInt16, channels=1, rate=44100):
        if id is None:
            raise ValueError("ID cannot be None")
        elif self.id_exists(id):
            raise ValueError("ID already in use")
        else:
            self.servers[id] = StreamServer(id, port, chunk, format, channels, rate)

    def start(self, id):
        if self.id_exists(id):
            self.servers[id].start()
        else:
            raise ValueError("ID not found")
        
    def stop(self, id):
        if self.id_exists(id):
            self.servers[id].stop()
        else:
            raise ValueError("ID not found")
        
    def delete(self, id):
        if self.id_exists(id):
            del self.servers[id]
        else:
            raise ValueError("ID not found")
        
    def id_exists(self, id):
        return id in self.servers
       
if __name__ == '__main__':
    audioStreamServerHandler = StreamServerHandler()
    audioStreamServerHandler.add(id=1, port=7000)
    audioStreamServerHandler.start(1)

    # audioStreamHandler = StreamClientHandler()
    # audioStreamHandler.add(id=1, server=('192.168.1.117', 7000))
    # audioStreamHandler.start(1)