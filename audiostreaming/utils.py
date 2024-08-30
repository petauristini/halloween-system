import socket
import pyaudio

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

def get_input_devices():
    p = pyaudio.PyAudio()
    devices = []
    for i in range(p.get_device_count()):
        device_info = p.get_device_info_by_index(i)     
        if device_info['maxInputChannels'] > 0:
            devices.append(device_info['name'])
    p.terminate()
    return devices