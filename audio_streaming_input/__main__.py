import tkinter as tk
import tkinter.ttk as ttk
from PIL import Image, ImageTk
import pyaudio
import os
import sys
from lib import AudioStream

module_dir = os.path.dirname(__file__)
assets_dir = os.path.join(module_dir, 'assets')

# Initialize the StreamServerHandler instance
audioStreamServerHandler = AudioStream.StreamServerHandler(('127.0.0.1', 5000))

def get_input_devices():
    p = pyaudio.PyAudio()
    devices = []
    for i in range(p.get_device_count()):
        device_info = p.get_device_info_by_index(i)
        if device_info['maxInputChannels'] > 0:
            devices.append(device_info['name'])
    p.terminate()
    return devices

def handle_device_activation(device_name, device_index, is_activated):
    if is_activated:
        audioStreamServerHandler.add(inputId=device_index, inputName=device_name)
        audioStreamServerHandler.start(inputId=device_index)
    else:
        audioStreamServerHandler.delete(inputId=device_index)

def handle_device_mute(device_name, device_index, is_muted):
    if is_muted:
        audioStreamServerHandler.stop(inputId=device_index)
    else:
        audioStreamServerHandler.start(inputId=device_index)

class InputDeviceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio Streaming Input")

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
        self.ip_entry.insert(0, "192.168.1.50")  # Default IP address
        self.ip_entry.pack(side=tk.LEFT, padx=(0, 10))

        # Label for port input
        self.port_label = tk.Label(self.top_frame, text="Port:", fg=self.fg_color, bg=self.bg_color)
        self.port_label.pack(side=tk.LEFT, padx=(0, 5))

        # Entry for port with default value
        self.port_entry = tk.Entry(self.top_frame, bg=self.button_active_bg, fg=self.fg_color, width=6, insertbackground=self.fg_color)
        self.port_entry.insert(0, "8080")  # Default Port
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

    def update_server_config(self):
        ip = self.ip_entry.get()
        port = self.port_entry.get()
        # Here you can add your logic to update the server IP and port in the audioStreamServerHandler
        print(f"Server IP: {ip}, Port: {port}")
        # Example: Update the server handler with the new IP and port
        audioStreamServerHandler.update_main_server((ip, int(port)))

    def update_connection_status(self):
        if audioStreamServerHandler.mainServerConnected:
            self.server_config_label.config(text="Main Server (Connected)", fg="#4CAF50")
        else:
            self.server_config_label.config(text="Main Server (Disconnected)", fg="#F44336")
        # Call this method again after 1 second to keep the status updated
        self.root.after(1000, self.update_connection_status)

    def display_devices(self):
        # Get the list of input devices
        self.input_devices = get_input_devices()

        for index, device in enumerate(self.input_devices):
            # Create a frame for each device entry with a fixed width
            device_entry_frame = tk.Frame(self.device_list_frame, bd=2, relief=tk.RAISED, width=400, bg=self.bg_color)
            device_entry_frame.pack(fill=tk.X, pady=5, padx=5)
            device_entry_frame.pack_propagate(False)

            # Use grid layout for internal widgets
            device_entry_frame.grid_rowconfigure(0, weight=0)  # Dropdown row
            device_entry_frame.grid_rowconfigure(1, weight=0)  # Buttons row
            device_entry_frame.grid_columnconfigure(0, weight=1)  # Expand the column for the dropdown

            # Label to display the device name
            device_label = tk.Label(device_entry_frame, text=device, font=("Arial", 12), wraplength=260, anchor="w", justify="left", fg=self.fg_color, bg=self.bg_color)
            device_label.grid(row=0, column=0, padx=10, pady=5, sticky="ew")

            # Create a frame to hold the dropdown and buttons
            control_frame = tk.Frame(device_entry_frame, bg=self.bg_color)
            control_frame.grid(row=0, column=1, columnspan=2, padx=10, pady=5, sticky="ew")
            control_frame.grid_rowconfigure(0, weight=0)  # Dropdown row
            control_frame.grid_rowconfigure(1, weight=0)  # Buttons row 
            control_frame.grid_columnconfigure(0, weight=1)  # Dropdown expands

            # Create a list of channels for the dropdown
            channels = audioStreamServerHandler.channels
            self.selected_channel = tk.StringVar(value=channels[0])  # Default value

            # Create the dropdown menu
            dropdown_menu = tk.OptionMenu(control_frame, self.selected_channel, *channels)
            # Let the dropdown fit its content
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
            activation_button = tk.Button(buttons_frame, text="Activate", command=lambda d=device, i=index, v=activation_var: self.toggle_activation(d, i, v),
                                        bg=self.button_inactive_bg, fg=self.button_inactive_fg, relief="flat", width=10, height=1,
                                        activebackground=self.button_hover_bg, activeforeground=self.button_hover_fg,
                                        highlightthickness=0, bd=0, cursor="hand2")
            activation_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

            # Mute/unmute button
            mute_var = tk.BooleanVar(value=False)  # False = Unmuted by default
            mute_button = tk.Button(buttons_frame, image=self.unmute_image, command=lambda v=mute_var, d=device, i=index: self.toggle_mute(v, d, i),
                                    bg=self.bg_color, borderwidth=0, highlightthickness=0, activebackground=self.bg_color, activeforeground=self.fg_color, relief="flat", cursor="hand2")
            mute_button.grid(row=0, column=1, padx=5, pady=5)

            # Store references to buttons and vars in the frame
            device_entry_frame.activation_button = activation_button
            device_entry_frame.activation_var = activation_var
            device_entry_frame.mute_button = mute_button
            device_entry_frame.mute_var = mute_var
            device_entry_frame.dropdown_menu = dropdown_menu  # Store dropdown reference

            # Disable mute button by default (as the device is deactivated initially)
            mute_button.config(state=tk.DISABLED)

    def toggle_activation(self, device, device_index, activation_var):
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
        handle_device_activation(device, device_index, is_activated)

    def toggle_mute(self, mute_var, device, device_index):
        # Toggle the mute state
        is_muted = not mute_var.get()
        mute_var.set(is_muted)

        # Find the mute button for the given device
        mute_button = self.find_mute_button(device)
        if mute_button:
            mute_button.config(image=self.mute_image if is_muted else self.unmute_image)

        # Call the function to handle mute
        handle_device_mute(device, device_index, is_muted)

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
        
        # Terminate the StreamServerHandler to stop any active threads
        audioStreamServerHandler.terminate()
        
        self.root.destroy()  # Close the Tkinter window
        sys.exit(0)  # Exit the script completely


# Create the main window
root = tk.Tk()
root.withdraw()

# Instantiate the app
app = InputDeviceApp(root)
print("GUI is ready...")

root.deiconify()

# Run the application
root.mainloop()
