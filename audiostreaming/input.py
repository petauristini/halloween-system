import tkinter as tk
import tkinter.ttk as ttk
from PIL import Image, ImageTk
import pyaudio
import os
import sys
import socket
import threading
import pyaudio
import pickle
import struct
import atexit
import time
import requests
from audiostreaming.utils import get_local_ip, get_input_devices

DEFAULT_IP = "127.0.0.1"
DEFAULT_PORT = 5000

module_dir = os.path.dirname(__file__)
assets_dir = os.path.join(module_dir, 'assets')

class StreamingInput:

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

    def _audio_stream(self):
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
            self.serverThread = threading.Thread(target=self._audio_stream, args=())
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

class StreamingInputHandler:
    def __init__(self, mainServer, output_update_callback: callable = None, input_update_callback: callable = None):
        self.inputs = []
        self.outputs = []
        self.servers = {}
        self.output_update_callback = output_update_callback
        self.input_update_callback = input_update_callback

        self.mainServer = mainServer
        self.mainServerConnected = False
        self.lastRegistration = 0
        self.registrationInterval = 3
        self.registrationThreadStopFlag = threading.Event()
        self.registrationThread = threading.Thread(target=self.register_inputs, daemon=True)
        self.registrationThread.start()
        self.pyaudio = pyaudio.PyAudio()
        self._update_inputs()
        self._update_outputs()
        

    def _update_outputs(self):
        try:
            response = requests.get(f'http://{self.mainServer[0]}:{self.mainServer[1]}/api/streamingcontrol/info/outputs')
            if not response.ok:
                print(f"Error while updating outputs: {response.text}")
                new_outputs = []
                return
            new_outputs = response.json()
        except:
            print("Error while updating outputs")
            new_outputs = []
        if new_outputs != self.outputs:
            self.outputs = new_outputs
            if self.output_update_callback:
                self.output_update_callback()
                print("callback initiated")

    def _update_inputs(self):
        new_inputs = []
        for i in range(self.pyaudio.get_device_count()):
            device_info = self.pyaudio.get_device_info_by_index(i)     
            if device_info['maxInputChannels'] > 0:
                new_inputs.append((i, device_info['name']))
        if new_inputs != self.inputs:
            self.inputs = new_inputs
            if self.input_update_callback:
                self.input_update_callback()
        

    def add(self, inputId, inputName, port=0, chunk=1024, format=pyaudio.paInt16, channels=1, rate=44100):
        if inputId is None:
            raise ValueError("inputId cannot be None")
        elif self.input_in_use(inputId):
            raise ValueError("input already in use")
        else:
            self.servers[inputId] = StreamingInput(inputId, inputName, port, chunk, format, channels, rate)

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
                self._update_outputs()
                serversCopy = self.servers.copy()
                serverList = [{'inputId': server.inputId, 'inputName': server.inputName, 'port': server.port, 'ip': server.ip} for server in serversCopy.values()]

                url = f'http://{self.mainServer[0]}:{self.mainServer[1]}/api/streamingcontrol/input'
                try:
                    response = requests.post(url, json=serverList, timeout=2)  # Added timeout
                    if response.status_code == 200:
                        self.mainServerConnected = True
                    else:
                        self.mainServerConnected = False
                except requests.RequestException as e:
                    print(f"Request Exception with main server")
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
        self.pyaudio.terminate()
        print("Registration thread terminated")

class InputDeviceApp:
    def __init__(self, root):
        self.root = root
        self.root.withdraw()

        self.audioStreamingInputHandler = StreamingInputHandler((DEFAULT_IP, DEFAULT_PORT), self.refresh_display)

        self.root.title("Audio Streaming Input")

        self.current_inputs = {}

        # Set dark mode colors
        self.bg_color = "#2E2E2E"
        self.fg_color = "#FFFFFF"
        self.button_active_bg = "#3A3A3A"
        self.button_inactive_bg = "#4CAF50"
        self.button_inactive_fg = "#FFFFFF"
        self.button_active_fg = "#FFFFFF"
        self.button_hover_bg = "#757575"  # Gray shade for hover
        self.button_hover_fg = "#FFFFFF"  # White text for hover

        self.root.configure(bg=self.bg_color)

        # Create the top frame for server input
        self.top_frame = tk.Frame(self.root, bg=self.bg_color)
        self.top_frame.pack(pady=10, padx=10, fill=tk.X)

        # Label above the IP and Port entries, will show the connection status too
        self.server_config_label = tk.Label(self.top_frame, text="Main Server (Connecting...)", font=("Arial", 12, "bold"), fg=self.fg_color, bg=self.bg_color)
        self.server_config_label.pack(side=tk.TOP, pady=(0, 5))

        # Label for IP address input
        self.ip_label = tk.Label(self.top_frame, text="IP:", fg=self.fg_color, bg=self.bg_color)
        self.ip_label.pack(side=tk.LEFT, padx=(0, 5))

        # Entry for IP address with default value
        self.ip_entry = tk.Entry(self.top_frame, bg=self.button_active_bg, fg=self.fg_color, width=15, insertbackground=self.fg_color)
        self.ip_entry.insert(0, DEFAULT_IP)
        self.ip_entry.pack(side=tk.LEFT, padx=(0, 10))

        # Label for port input
        self.port_label = tk.Label(self.top_frame, text="Port:", fg=self.fg_color, bg=self.bg_color)
        self.port_label.pack(side=tk.LEFT, padx=(0, 5))

        # Entry for port with default value
        self.port_entry = tk.Entry(self.top_frame, bg=self.button_active_bg, fg=self.fg_color, width=6, insertbackground=self.fg_color)
        self.port_entry.insert(0, DEFAULT_PORT)
        self.port_entry.pack(side=tk.LEFT, padx=(0, 10))

        # Update button
        self.update_button = tk.Button(self.top_frame, text="Update", command=self.update_server_config, bg=self.button_inactive_bg,
                                       fg=self.button_inactive_fg, activebackground=self.button_hover_bg, activeforeground=self.button_hover_fg, relief="flat")
        self.update_button.pack(side=tk.LEFT)

        # Separation line with increased height
        self.separator = tk.Frame(self.root, height=6, bd=1, relief=tk.SUNKEN, bg="#757575")  # Increased height
        self.separator.pack(fill=tk.X, padx=10, pady=10)

        # Load images for mute and unmute
        self.mute_image = ImageTk.PhotoImage(Image.open(os.path.join(assets_dir, 'muted.png')).resize((40, 40)))
        self.unmute_image = ImageTk.PhotoImage(Image.open(os.path.join(assets_dir, 'unmuted.png')).resize((40, 40)))

        # Frame to display the list of devices
        self.device_list_frame = tk.Frame(root, bg=self.bg_color)
        self.device_list_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        # Display all input devices
        self.display_devices()

        # Adjust the window size to fit the content
        self.adjust_window_size()

        # Update connection status periodically
        self.update_connection_status()

        # Set the on_closing method to handle the window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.root.deiconify()
        print("GUI is ready...")
    
    def _handle_device_activation(self, device_name, device_index, is_activated):
        if is_activated:
            self.audioStreamingInputHandler.add(inputId=device_index, inputName=device_name)
            self.audioStreamingInputHandler.start(inputId=device_index)
        else:
            self.audioStreamingInputHandler.delete(inputId=device_index)

    def _handle_device_mute(self, device_name, device_index, is_muted):
        if is_muted:    
            self.audioStreamingInputHandler.stop(inputId=device_index)
        else:
            self.audioStreamingInputHandler.start(inputId=device_index)

    def update_server_config(self):
        ip = self.ip_entry.get()
        port = self.port_entry.get()
        # Here you can add your logic to update the server IP and port in the self.audioStreamingInputHandler
        print(f"Server IP: {ip}, Port: {port}")
        # Example: Update the server handler with the new IP and port
        self.audioStreamingInputHandler.update_main_server((ip, int(port)))

    def update_connection_status(self):
        if self.audioStreamingInputHandler.mainServerConnected:
            self.server_config_label.config(text="Main Server (Connected)", fg="#4CAF50")
        else:
            self.server_config_label.config(text="Main Server (Disconnected)", fg="#F44336")
        # Call this method again after 1 second to keep the status updated
        self.root.after(1000, self.update_connection_status)

    def refresh_display(self):
        print("Refreshing display...")
        # Clear the current device list frame
        for widget in self.device_list_frame.winfo_children():
            widget.destroy()

        # Display updated devices
        self.display_devices()

    def add_device(self, device):
        device_entry_frame = tk.Frame(self.device_list_frame, bd=2, relief=tk.RAISED, width=400, bg=self.bg_color)
        device_entry_frame.pack(fill=tk.X, pady=5, padx=5)
        device_entry_frame.pack_propagate(False)

        # Use grid layout for internal widgets
        device_entry_frame.grid_rowconfigure(0, weight=0)  # Dropdown row
        device_entry_frame.grid_rowconfigure(1, weight=0)  # Buttons row
        device_entry_frame.grid_columnconfigure(0, weight=1)  # Expand the column for the dropdown

        # Label to display the device name
        device_label = tk.Label(device_entry_frame, text=device[1], font=("Arial", 12), wraplength=260, anchor="w", justify="left", fg=self.fg_color, bg=self.bg_color)
        device_label.grid(row=0, column=0, padx=10, pady=5, sticky="ew")

        # Create a frame to hold the dropdown and buttons
        control_frame = tk.Frame(device_entry_frame, bg=self.bg_color)
        control_frame.grid(row=0, column=1, columnspan=2, padx=10, pady=5, sticky="ew")
        control_frame.grid_rowconfigure(0, weight=0)  # Dropdown row
        control_frame.grid_rowconfigure(1, weight=0)  # Buttons row 
        control_frame.grid_columnconfigure(0, weight=1)  # Dropdown expands

        # Check if outputs is empty
        if not self.audioStreamingInputHandler.outputs:
            # Create a label to indicate no outputs available
            no_outputs_label = tk.Label(control_frame, text="No outputs available", font=("Arial", 12), fg="red", bg=self.bg_color)
            no_outputs_label.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        else:
            # Create a list of channels for the dropdown
            self.selected_channel = tk.StringVar(value=self.audioStreamingInputHandler.outputs[0])  # Default value

            # Create the dropdown menu
            dropdown_menu = tk.OptionMenu(control_frame, self.selected_channel, *self.audioStreamingInputHandler.outputs)
            dropdown_menu.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
            
            dropdown_menu.config(bg=self.bg_color, fg=self.fg_color, activebackground=self.button_active_bg, activeforeground=self.button_active_fg, relief="flat")

            menu = dropdown_menu.nametowidget(dropdown_menu.menuname)
            menu.config(bg=self.bg_color, fg=self.fg_color, activebackground=self.button_active_bg, activeforeground=self.button_active_fg)

            # Adjust dropdown width to fit content, using a placeholder
            dropdown_menu.update_idletasks()
            dropdown_width = dropdown_menu.winfo_reqwidth()
            control_frame.config(width=dropdown_width + 20)  # Add some padding to the width

        # Create a frame to hold the activation and mute buttons
        buttons_frame = tk.Frame(control_frame, bg=self.bg_color)
        buttons_frame.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        buttons_frame.grid_columnconfigure(0, weight=1)  # Expand the column for activation button
        buttons_frame.grid_columnconfigure(1, weight=0)  # Fixed size for mute button

        # Activation button
        activation_var = tk.BooleanVar(value=False)  # False = Deactivated, True = Activated
        activation_button = tk.Button(buttons_frame, text="Activate", command=lambda d=device[1], i=device[0], v=activation_var: self.toggle_activation(d, i, v),
                                    bg=self.button_inactive_bg, fg=self.button_inactive_fg, relief="flat", width=10, height=1,
                                    activebackground=self.button_hover_bg, activeforeground=self.button_hover_fg,
                                    highlightthickness=0, bd=0, cursor="hand2")
        activation_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        # Mute/unmute button
        mute_var = tk.BooleanVar(value=False)  # False = Unmuted by default
        mute_button = tk.Button(buttons_frame, image=self.unmute_image, command=lambda v=mute_var, d=device[1], i=device[0]: self.toggle_mute(v, d, i),
                                bg=self.bg_color, borderwidth=0, highlightthickness=0, activebackground=self.bg_color, activeforeground=self.fg_color, relief="flat", cursor="hand2")
        mute_button.grid(row=0, column=1, padx=5, pady=5)

        # Store references to buttons and vars in the frame
        device_entry_frame.activation_button = activation_button
        device_entry_frame.activation_var = activation_var
        device_entry_frame.mute_button = mute_button
        device_entry_frame.mute_var = mute_var
        device_entry_frame.dropdown_menu = dropdown_menu if not not self.audioStreamingInputHandler.outputs else None  # Store dropdown reference

        # Disable mute button by default (as the device is deactivated initially)
        mute_button.config(state=tk.DISABLED)

        self.current_inputs[device[0]] = device_entry_frame
        
    def remove_device(self, device_id):
        if device_id in self.current_inputs:
            device_frame = self.current_inputs.pop(device_id)
            device_frame.destroy()

    def display_devices(self):  
        # Clear the existing devices display
        for widget in self.device_list_frame.winfo_children():  
            widget.destroy()

        for device in self.audioStreamingInputHandler.inputs:
            self.add_device(device)



    def toggle_activation(self, device, device_index, activation_var):
        # Only proceed if outputs are available
        if not self.audioStreamingInputHandler.outputs:
            print("Cannot activate input, no outputs available")
            return

        # Toggle the activation state
        is_activated = not activation_var.get()
        activation_var.set(is_activated)
        activation_button_text = "Deactivate" if is_activated else "Activate"
        activation_button_bg = "#f44336" if is_activated else self.button_inactive_bg

        # Update the button text and background color
        activation_button = self.get_activation_button(device)
        activation_button.config(text=activation_button_text, bg=activation_button_bg)

        # Handle the mute button based on the activation state
        mute_button = self.get_mute_button(device)
        if mute_button:
            if is_activated:
                mute_button.config(state=tk.NORMAL)
                mute_button.config(image=self.unmute_image if not self.get_mute_var(device).get() else self.mute_image)
                # Disable the dropdown if the device is activated
                self.set_dropdown_state(device, state=tk.DISABLED)
            else:
                mute_button.config(state=tk.DISABLED)
                self.get_mute_var(device).set(False)  # Ensure the device is unmuted
                mute_button.config(image=self.unmute_image)
                # Enable the dropdown if the device is deactivated
                self.set_dropdown_state(device, state=tk.NORMAL)

        # Call the function to handle activation
        self._handle_device_activation(device, device_index, is_activated)


    def toggle_mute(self, mute_var, device, device_index):
        # Toggle the mute state
        is_muted = not mute_var.get()
        mute_var.set(is_muted)

        # Find the mute button for the given device
        mute_button = self.find_mute_button(device)
        if mute_button:
            mute_button.config(image=self.mute_image if is_muted else self.unmute_image)

        # Call the function to handle mute
        self._handle_device_mute(device, device_index, is_muted)

    def set_dropdown_state(self, device, state):
        # Find the dropdown menu for the given device and set its state
        for widget in self.device_list_frame.winfo_children():
            if isinstance(widget, tk.Frame):
                if widget.winfo_children():
                    if widget.winfo_children()[0].cget("text") == device:
                        dropdown_menu = widget.dropdown_menu
                        dropdown_menu.config(state=state)
                        return

    def get_mute_var(self, device):
        # Find the mute variable for the given device
        for widget in self.device_list_frame.winfo_children():
            if isinstance(widget, tk.Frame):
                if widget.winfo_children():
                    if widget.winfo_children()[0].cget("text") == device:
                        return widget.mute_var
        return None

    def get_mute_button(self, device):
        # Find the mute button for the given device
        for widget in self.device_list_frame.winfo_children():
            if isinstance(widget, tk.Frame):
                if widget.winfo_children():
                    if widget.winfo_children()[0].cget("text") == device:
                        return widget.mute_button
        return None

    def find_mute_button(self, device):
        # Find the mute button for the given device
        for widget in self.device_list_frame.winfo_children():
            if isinstance(widget, tk.Frame):
                if widget.winfo_children():
                    if widget.winfo_children()[0].cget("text") == device:
                        return widget.mute_button
        return None

    def get_activation_button(self, device):
        # Find the activation button for the given device
        for widget in self.device_list_frame.winfo_children():
            if isinstance(widget, tk.Frame):
                if widget.winfo_children():
                    if widget.winfo_children()[0].cget("text") == device:
                        return widget.activation_button
        return None

    def adjust_window_size(self):
        # Update the window size to fit all content
        self.root.update_idletasks()    
        width = self.device_list_frame.winfo_reqwidth() + 20  # Small padding to ensure it fits well
        height = self.device_list_frame.winfo_reqheight() + 20  # Small padding to ensure it fits well

        # Set the window size
        self.root.geometry(f"{width}x{height}")

        # Disable resizing
        self.root.resizable(False, False)

    def on_closing(self):
        """Handles the GUI-specific cleanup when the window is closed."""
        print("GUI is closing...")
        
        # Terminate the StreamingInputHandler to stop any active threads
        self.audioStreamingInputHandler.terminate()
        
        self.root.destroy()  # Close the Tkinter window
        sys.exit(0)  # Exit the script completely


if __name__ == "__main__":
    root = tk.Tk()

    app = InputDeviceApp(root)

    root.mainloop()
