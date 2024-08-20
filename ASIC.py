import tkinter as tk
from PIL import Image, ImageTk
import pyaudio
import AudioStream

# Initialize the StreamServerHandler instance
audioStreamServerHandler = AudioStream.StreamServerHandler()

# Function to get available input devices using PyAudio
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
    action = "Muted" if is_muted else "Unmuted"

class InputDeviceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio Stream Input Client - ASIC")

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

        # Load images for mute and unmute
        self.mute_image = ImageTk.PhotoImage(Image.open("muted.png").resize((40, 40)))
        self.unmute_image = ImageTk.PhotoImage(Image.open("unmuted.png").resize((40, 40)))

        # Frame to display the list of devices
        self.device_list_frame = tk.Frame(root, bg=self.bg_color)
        self.device_list_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        # Display all input devices
        self.display_devices()

        # Adjust the window size to fit the content
        self.adjust_window_size()

    def display_devices(self):
        # Get the list of input devices
        self.input_devices = get_input_devices()

        for index, device in enumerate(self.input_devices):
            # Create a frame for each device entry with a fixed width
            device_entry_frame = tk.Frame(self.device_list_frame, bd=2, relief=tk.RAISED, width=400, bg=self.bg_color)
            device_entry_frame.pack(fill=tk.X, pady=5, padx=5)
            device_entry_frame.pack_propagate(False)

            # Use grid layout for internal widgets
            device_entry_frame.grid_rowconfigure(0, weight=1)
            device_entry_frame.grid_columnconfigure(0, weight=1)  # Device label expands to fill remaining space
            device_entry_frame.grid_columnconfigure(1, weight=0)  # Fixed size for activation button
            device_entry_frame.grid_columnconfigure(2, weight=0)  # Fixed size for mute button

            # Label to display the device name
            device_label = tk.Label(device_entry_frame, text=device, font=("Arial", 12), wraplength=260, anchor="w", justify="left", fg=self.fg_color, bg=self.bg_color)
            device_label.grid(row=0, column=0, padx=10, pady=5, sticky="ew")

            # Activation button
            activation_var = tk.BooleanVar(value=False)  # False = Deactivated, True = Activated
            activation_button = tk.Button(device_entry_frame, text="Activate", command=lambda d=device, i=index, v=activation_var: self.toggle_activation(d, i, v),
                                        bg=self.button_inactive_bg, fg=self.button_inactive_fg, relief="flat", width=10, height=1,
                                        activebackground=self.button_hover_bg, activeforeground=self.button_hover_fg,
                                        highlightthickness=0, bd=0, cursor="hand2")
            activation_button.grid(row=0, column=1, padx=10, pady=5)

            # Mute/unmute button
            mute_var = tk.BooleanVar(value=False)  # False = Unmuted by default
            mute_button = tk.Button(device_entry_frame, image=self.unmute_image, command=lambda v=mute_var, d=device, i=index: self.toggle_mute(v, d, i),
                                    bg=self.bg_color, borderwidth=0, highlightthickness=0, activebackground=self.bg_color, activeforeground=self.fg_color, relief="flat", cursor="hand2")
            mute_button.grid(row=0, column=2, padx=10, pady=5)

            # Store references to buttons and vars in the frame
            device_entry_frame.activation_button = activation_button
            device_entry_frame.activation_var = activation_var
            device_entry_frame.mute_button = mute_button
            device_entry_frame.mute_var = mute_var

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
            else:
                mute_button.config(state=tk.DISABLED)
                self.get_mute_var(device).set(False)  # Ensure the device is unmuted
                mute_button.config(image=self.unmute_image)

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

# Create the main window
root = tk.Tk()

# Instantiate the app
app = InputDeviceApp(root)

# Run the application
root.mainloop()
