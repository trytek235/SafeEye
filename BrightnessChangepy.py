import threading
import screen_brightness_control as sbc
import tkinter as tk
import ctypes
import numpy as np
import wmi
import json
from PIL import Image, ImageTk
from pystray import Icon, MenuItem as item, Menu
from BCFunctions import update_brightness, update_color_temperature, get_current_brightness, get_current_color_temperature, run_tray, on_closing

root = tk.Tk()

icon = ImageTk.PhotoImage(Image.open("IcoImage.ico"))
root.tk.call('wm', 'iconphoto', root._w, icon)
root.title("Brightness and Colour Control")

label = tk.Label(root, text='GammaApp')
label.pack()


brightness_scale = tk.Scale(root, from_=0, to_=100, orient='horizontal', label='Brightness', command=update_brightness)
brightness_value = get_current_brightness()
brightness_scale.set(brightness_value)
brightness_scale.pack()

color_scale = tk.Scale(root, from_=1000, to=10000, orient='horizontal', label='Color Temperature', command=update_color_temperature, tickinterval=4000, resolution=50)

# Set the color temperature scale's starting value
current_rgb = get_current_color_temperature(brightness_scale, color_scale)
if current_rgb:
    # You can process the RGB values to estimate color temperature
    # Assuming color_scale is used to set the color temperature
    color_scale.set(current_rgb)

color_scale.pack()

# Start tray icon in a separate thread
threading.Thread(target=run_tray, daemon=True).start()

root.protocol("WM_DELETE_WINDOW", on_closing(brightness_scale, color_scale, root))
root.mainloop()
