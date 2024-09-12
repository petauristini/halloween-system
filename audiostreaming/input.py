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
CONECTION_STATUS_UPDATE_INTERVAL = 1000
INPUT_DEVICE_WIDGET_WIDTH = 250
INPUT_DEVICE_WIDGET_HEIGHT = 100

module_dir = os.path.dirname(__file__)
assets_dir = os.path.join(module_dir, 'assets')

class StreamingInput:

    def __init__(self, inputId, inputName, outputs=[], port=0, chunk=1024, format=pyaudio.paInt16, channels=1, rate=44100):
        self.inputId = inputId
        self.inputName = inputName
        self.outputs = outputs
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
        self._start()

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

    def _start(self):
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

    def start(self, inputId, inputName, outputs=[],port=0, chunk=1024, format=pyaudio.paInt16, channels=1, rate=44100):
        if inputId is None:
            raise ValueError("inputId cannot be None")
        elif self.input_in_use(inputId):
            raise ValueError("input already in use")
        else:
            self.servers[inputId] = StreamingInput(inputId, inputName, outputs, port, chunk, format, channels, rate)
        
    def stop(self, inputId):
        if self.input_in_use(inputId):
            self.servers[inputId].stop()
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
                serverList = [{'ip': server.ip, 'port': server.port, 'outputs': server.outputs} for server in serversCopy.values()]

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
        servers = self.servers.copy()
        for i in servers:
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

        self.audioStreamingInputHandler = StreamingInputHandler((DEFAULT_IP, DEFAULT_PORT))

        # Initialize device output vars
        self.device_output_vars = {}
        self.device_selected_outputs = {}
        self.devices = []

        self.root.title("Audio Streaming Input")

        self.root.resizable(False, False)

        # Set dark mode colors
        self.bg_color = "#2E2E2E"
        self.fg_color = "#FFFFFF"
        self.button_active_bg = "#3A3A3A"
        self.button_inactive_bg = "#4CAF50"
        self.button_inactive_fg = "#FFFFFF"
        self.button_active_fg = "#FFFFFF"
        self.button_hover_bg = "#757575"  # Gray shade for hover
        self.button_hover_fg = "#FFFFFF"  # White text for hover
        self.connected_color = "#4CAF50"  # Green for connected
        self.disconnected_color = "#F44336"  # Red for disconnected

        self.root.configure(bg=self.bg_color)

        # Load images for buttons
        self.refresh_image = ImageTk.PhotoImage(Image.open(os.path.join(assets_dir, 'refresh.png')).resize((30, 30)))
        self.update_image = ImageTk.PhotoImage(Image.open(os.path.join(assets_dir, 'update.png')).resize((30, 30)))  # Load Update button image
        self.select_output_image = ImageTk.PhotoImage(Image.open(os.path.join(assets_dir, 'speaker.png')).resize((30, 30)))
        self.checked_image = ImageTk.PhotoImage(Image.open(os.path.join(assets_dir, 'checked.png')).resize((20, 20)))
        self.unchecked_image = ImageTk.PhotoImage(Image.open(os.path.join(assets_dir, 'unchecked.png')).resize((20, 20)))
        self.activate_image = ImageTk.PhotoImage(Image.open(os.path.join(assets_dir, 'activate.png')).resize((30, 30)))
        self.deactivate_image = ImageTk.PhotoImage(Image.open(os.path.join(assets_dir, 'deactivate.png')).resize((30, 30)))
        self.ok_image = ImageTk.PhotoImage(Image.open(os.path.join(assets_dir, 'ok.png')).resize((30, 30)))
        self.icon_image = ImageTk.PhotoImage(Image.open(os.path.join(assets_dir, 'icon.png')).resize((30, 30)))

        self.root.iconphoto(False, self.icon_image)

        # Frame for input devices
        self.input_device_frame = tk.Frame(root, bg=self.bg_color)
        self.input_device_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True, side=tk.TOP)

        # Create the top frame with a fixed height and pack it at the bottom
        self.top_bar = tk.Frame(self.root, bg=self.bg_color, height=100)  # Set a fixed height for top_bar
        self.top_bar.pack(pady=10, padx=10, fill=tk.X, side=tk.BOTTOM)  # Fill horizontally and align at the bottom

        # Use grid layout for precise control inside the top_bar
        self.top_bar.grid_rowconfigure(0, weight=1)
        self.top_bar.grid_columnconfigure(0, weight=1)  # For Refresh Devices button
        self.top_bar.grid_columnconfigure(1, weight=1)  # For IP, Port entries and Update button

        # Refresh Devices button (left aligned) with image
        self.refresh_input_devices_button = tk.Button(self.top_bar, image=self.refresh_image, command=self.refresh_input_devices,
                                        bg=self.bg_color, relief="flat", borderwidth=0, highlightthickness=0)
        self.refresh_input_devices_button.grid(row=0, column=0, sticky="w", padx=5, pady=5)

        # Control Server Configuration
        self.control_server_configuration = tk.Frame(self.top_bar, bg=self.bg_color)
        self.control_server_configuration.grid(row=0, column=1, sticky="e")

        self.ip_entry = tk.Entry(self.control_server_configuration, bg=self.button_active_bg, fg=self.fg_color, width=15, insertbackground=self.fg_color)
        self.ip_entry.insert(0, DEFAULT_IP)
        self.ip_entry.pack(side=tk.LEFT, padx=(0, 5))

        self.port_entry = tk.Entry(self.control_server_configuration, bg=self.button_active_bg, fg=self.fg_color, width=6, insertbackground=self.fg_color)
        self.port_entry.insert(0, DEFAULT_PORT)
        self.port_entry.pack(side=tk.LEFT, padx=(0, 10))  # Increased padding to the right of the Port Entry

        self.update_server_configuration_button = tk.Button(self.control_server_configuration, image=self.update_image, command=self.update_server_config,
                                        bg=self.bg_color, relief="flat", borderwidth=0, highlightthickness=0)
        self.update_server_configuration_button.pack(side=tk.LEFT)

        # Separation line above the top bar
        self.separator = tk.Frame(self.root, height=6, bd=1, relief=tk.SUNKEN, bg="#757575")  # Increased height
        self.separator.pack(fill=tk.X, side=tk.BOTTOM)

        # Display all input devices
        self.refresh_input_devices()

        # Update connection status periodically
        self.update_connection_status()

        # Set the on_closing method to handle the window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.root.deiconify()

        print("GUI is ready...")

    def update_input_devices(self):
        self.devices = get_input_devices()
    
    def _handle_device_activation(self, device_name, device_index, is_activated):
        if is_activated:
            outputs = self.device_selected_outputs[device_name] if device_name in self.device_selected_outputs else []
            self.audioStreamingInputHandler.start(inputId=device_index, inputName=device_name, outputs=outputs)
        else:
            self.audioStreamingInputHandler.stop(inputId=device_index)

    def update_server_config(self):
        ip = self.ip_entry.get()
        port = self.port_entry.get()

        self.audioStreamingInputHandler.update_main_server((ip, int(port)))
        print(f"Control Server Updated: IP: {ip}, Port: {port}")

    def update_connection_status(self):
        try:
            if self.audioStreamingInputHandler.mainServerConnected:
                self.ip_entry.config(bg=self.connected_color)
                self.port_entry.config(bg=self.connected_color)
            else:
                self.ip_entry.config(bg=self.disconnected_color)
                self.port_entry.config(bg=self.disconnected_color)
        except Exception as e:
            print(f"Error updating connection status: {e}")
            self.ip_entry.config(bg=self.disconnected_color)
            self.port_entry.config(bg=self.disconnected_color)
        self.root.after(CONECTION_STATUS_UPDATE_INTERVAL, self.update_connection_status)

    def refresh_input_devices(self):
        self.update_input_devices()
        self.arrange_input_devices_widgets()


    def arrange_input_devices_widgets(self):
        # Clear the existing devices display
        for widget in self.input_device_frame.winfo_children():
            widget.destroy()

        # Define the number of columns in the grid
        num_columns = 3  # Adjust this number based on your layout preferences

        print("Devices:", self.devices)

        if not self.devices:
            print("No devices found.")
            return

        # Store buttons in a dictionary
        self.device_buttons = {}

        # Loop through devices and create frames for each
        for index, device in enumerate(self.devices):
            # Create a frame for each device entry with a fixed size and white border
            input_device = tk.Frame(self.input_device_frame, bd=2, relief=tk.RAISED, bg=self.bg_color, 
                                    width=INPUT_DEVICE_WIDGET_WIDTH, height=INPUT_DEVICE_WIDGET_HEIGHT, 
                                    highlightbackground="white", highlightcolor="white", highlightthickness=2)
            input_device.grid(row=index // num_columns, column=index % num_columns, pady=5, padx=5)
            input_device.grid_propagate(False)  # Prevent resizing inside the grid

            # Frame to hold the device name and buttons
            content_frame = tk.Frame(input_device, bg=self.bg_color, width=INPUT_DEVICE_WIDGET_WIDTH, height=INPUT_DEVICE_WIDGET_HEIGHT)
            content_frame.pack_propagate(False)  # Prevent resizing inside the pack
            content_frame.pack(fill=tk.BOTH, expand=True)

            # Label to display the device name (limited width with ellipsis)
            max_device_name_length = 20  # Adjust this number as needed
            truncated_device_name = device if len(device) <= max_device_name_length else device[:max_device_name_length - 3] + '...'

            device_label = tk.Label(content_frame, text=truncated_device_name, font=("Arial", 12), anchor="w", justify="left", fg=self.fg_color, bg=self.bg_color)
            device_label.pack(side=tk.TOP, padx=5, pady=5)

            # Frame to hold the buttons
            buttons_frame = tk.Frame(content_frame, bg=self.bg_color)
            buttons_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)  # Fill horizontally and align at the bottom

            # Activation button (left-aligned)
            activation_var = tk.BooleanVar(value=False)
            activation_button = tk.Button(buttons_frame, image=self.activate_image, command=lambda d=device, i=index, v=activation_var: self.toggle_activation(d, i, v),
                                        bg=self.bg_color, relief="flat", borderwidth=0, highlightthickness=0,
                                        activebackground=self.button_hover_bg, activeforeground=self.button_hover_fg,
                                        cursor="hand2")
            activation_button.pack(side=tk.LEFT, padx=5, pady=5)

            # Button to open the output selection window (right-aligned)
            output_button = tk.Button(buttons_frame, image=self.select_output_image, command=lambda d=device: self.open_output_selection(d),
                                    bg=self.bg_color, relief="flat", borderwidth=0, highlightthickness=0)
            output_button.pack(side=tk.RIGHT, padx=5, pady=5)  # Changed to RIGHT to align it to the right side

            # Store references to buttons and vars in the frame
            self.device_buttons[device] = {
                'activation_button': activation_button,
                'activation_var': activation_var,
                'output_button': output_button
            }

        # Disable grid row/column resizing completely
        for col in range(num_columns):
            self.input_device_frame.grid_columnconfigure(col, weight=0)  # Prevent resizing of columns
        for row in range((len(self.devices) + num_columns - 1) // num_columns):
            self.input_device_frame.grid_rowconfigure(row, weight=0)  # Prevent resizing of rows

    def open_output_selection(self, device):
        # Create a new Toplevel window
        output_window = tk.Toplevel(self.root)
        output_window.configure(bg="#ffffff")

        # Remove the title bar and standard window controls
        output_window.overrideredirect(True)

        # Set the Toplevel window to be transient for the main window
        output_window.transient(self.root)
        output_window.grab_set()  # Make the Toplevel window modal, blocking input to other windows

        # Load your images (checked and unchecked)
        self.checked_image = ImageTk.PhotoImage(Image.open(os.path.join(assets_dir, 'checked.png')).resize((20, 20)))
        self.unchecked_image = ImageTk.PhotoImage(Image.open(os.path.join(assets_dir, 'unchecked.png')).resize((20, 20)))

        # Initialize the dictionary to store the output variables and buttons for this device
        self.device_output_vars = {}

        # Get previously selected outputs for the device
        previously_selected_outputs = self.device_selected_outputs.get(device, [])

        # Create a frame to hold the checkboxes and labels
        content_frame = tk.Frame(output_window, bg=self.bg_color)
        content_frame.pack(padx=2, pady=2, fill=tk.BOTH, expand=True)

        for row, output in enumerate(self.audioStreamingInputHandler.outputs):
            # Set the initial value of the BooleanVar based on previous selection
            var = tk.BooleanVar(value=output in previously_selected_outputs)
            
            # Create a frame for each row
            row_frame = tk.Frame(content_frame, bg=self.bg_color)
            row_frame.grid(row=row, column=0, sticky="ew", padx=10, pady=5)
            
            # Checkbox button
            checkbox_button = tk.Button(row_frame, image=self.unchecked_image, command=lambda o=output, v=var: self.toggle_output_image(o, v),
                                        bg=self.bg_color, relief="flat", borderwidth=0, highlightthickness=0, cursor="hand2")
            checkbox_button.grid(row=0, column=0, sticky="w")
            
            # Label for the output name
            output_label = tk.Label(row_frame, text=output, fg=self.fg_color, bg=self.bg_color)
            output_label.grid(row=0, column=1, padx=10, pady=5, sticky="w")

            # Store the variable and checkbox button associated with each output for this device
            self.device_output_vars[output] = (var, checkbox_button)

            # Set the checkbox image based on the initial value of var
            checkbox_button.config(image=self.checked_image if var.get() else self.unchecked_image)

        # Add an OK button to confirm selection
        ok_button = tk.Button(content_frame, image=self.ok_image, command=lambda: self.save_output_selection(output_window, device),
                            bg=self.bg_color, relief="flat", borderwidth=0, highlightthickness=0)
        ok_button.grid(row=len(self.audioStreamingInputHandler.outputs), column=0, pady=10, padx=10)

        # Force the window to update and get accurate dimensions
        output_window.update_idletasks()

        # Calculate the size and position of the window
        window_width = output_window.winfo_width()
        window_height = output_window.winfo_height()

        # Get the main window's position and size
        main_window_x = self.root.winfo_rootx()
        main_window_y = self.root.winfo_rooty()
        main_window_width = self.root.winfo_width()
        main_window_height = self.root.winfo_height()

        # Calculate position to center the window relative to the main window
        x = main_window_x + (main_window_width - window_width) // 2
        y = main_window_y + (main_window_height - window_height) // 2

        # Set the window geometry
        output_window.geometry(f"{window_width}x{window_height}+{x}+{y}")

        # Ensure the window is correctly positioned
        output_window.update()


    def toggle_output_image(self, output, var):
        # Toggle the selection state
        is_selected = not var.get()
        var.set(is_selected)

        # Get the button associated with the output
        checkbox_button = self.device_output_vars[output][1]

        # Change the image based on the new state
        checkbox_button.config(image=self.checked_image if is_selected else self.unchecked_image)


    def get_selected_outputs_for_device(self, device):
        # Retrieve selected outputs for the given device
        return [output for output, (var, _) in self.device_output_vars.items() if var.get()]

    def save_output_selection(self, output_window, device):
        # Save the selected outputs for this device
        selected_outputs = self.get_selected_outputs_for_device(device)
        print(f"Selected outputs for {device}: {selected_outputs}")

        # Update the dictionary with the selected outputs
        self.device_selected_outputs[device] = selected_outputs

        # Close the output selection window
        output_window.destroy()



    def toggle_activation(self, device, device_index, activation_var):
        if not self.audioStreamingInputHandler.outputs:
            print("Cannot activate input, no outputs available")
            return

        is_activated = not activation_var.get()
        activation_var.set(is_activated)

        activation_button = self.get_activation_button(device)
        if activation_button:
            activation_button.config(image=self.deactivate_image if is_activated else self.activate_image)
        else:
            print(f"Activation button not found for device: {device}")

        # Handle the activation logic
        selected_outputs = self.get_selected_outputs_for_device(device)
        self._handle_device_activation(device, device_index, is_activated)

    def get_activation_button(self, device):
        return self.device_buttons.get(device, {}).get('activation_button')

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
