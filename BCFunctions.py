import ctypes
import numpy as np
import wmi
import json
from PIL import Image
from pystray import Icon, MenuItem as item, Menu

def save_settings(bsObj, csObj):
    settings = {
        "brightness": bsObj.get(),
        "color_temperature": csObj.get()
    }
    with open('settings.json', 'w') as f:
        json.dump(settings,f)

def load_settings():
    try:
        with open('settings.json','r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {'brightness': 25, 'color_temp': 3500}

def on_closing(bsObj, csObj, tkObj):
    save_settings(bsObj, csObj)
    tkObj.quit()

def quit_action(icon, tkObj):
    icon.stop()
    tkObj.quit()

def get_current_brightness():
    c = wmi.WMI(namespace='wmi')
    brightness = c.WmiMonitorBrightness()[0]
    return brightness.currentBrightness


def update_HDC(gamma):
    hdc = ctypes.windll.user32.GetDC(0)
    result = ctypes.windll.gdi32.SetDeviceGammaRamp(hdc, ctypes.byref(gamma))
    ctypes.windll.user32.ReleaseDC(0, hdc)


def update_color_temperature(kelvin):
    temp = int(kelvin) / 100.0
    if temp <= 66:
        red = 255
        green = temp
        green = 99.4708025861 * np.log(green) - 161.1195681661
        blue = 0 if temp <= 19 else (138.5177312231 * np.log(temp - 10) - 305.0447927307)
    else:
        red = 329.698727446 * ((temp - 60) ** -0.1332047592)
        green = 288.1221695283 * ((temp - 60) ** -0.0755148492)
        blue = 255

    red = np.clip(red, 0, 255)
    green = np.clip(green, 0, 255)
    blue = np.clip(blue, 0, 255)

    gamma_ramp = (ctypes.c_ushort * 256)()
    gamma_ramp_g = (ctypes.c_ushort * 256)()
    gamma_ramp_b = (ctypes.c_ushort * 256)()

    for i in range(256):
        gamma_ramp[i] = int(i * red / 255) << 8
        gamma_ramp_g[i] = int(i * green / 255) << 8
        gamma_ramp_b[i] = int(i * blue / 255) << 8

    full_gamma_ramp = (ctypes.c_ushort * 768)()
    for i in range(256):
        full_gamma_ramp[i] = gamma_ramp[i]
        full_gamma_ramp[i + 256] = gamma_ramp_g[i]
        full_gamma_ramp[i + 512] = gamma_ramp_b[i]
    update_HDC(full_gamma_ramp)


def update_brightness(brightness_value):
    c = wmi.WMI(namespace='wmi')
    methods = c.WmiMonitorBrightnessMethods()[0]
    methods.WmiSetBrightness(brightness_value, 0)


def run_tray():
    icon_image = Image.open("IcoImage.ico")
    menu = Menu(item('Quit', quit_action))
    tray_icon = Icon("GammaApp", icon_image, menu=menu)
    tray_icon.run()



def get_current_color_temperature(bsObj, csObj):
    gamma_ramp_r = (ctypes.c_ushort * 256)()
    gamma_ramp_g = (ctypes.c_ushort * 256)()
    gamma_ramp_b = (ctypes.c_ushort * 256)()
    full_gamma_ramp = (ctypes.c_ushort * 768)()
    red,green,blue,temp = 0,0,0,0
    red = np.clip(red, 0, 255)
    green = np.clip(green, 0, 255)
    blue = np.clip(blue, 0, 255)

    hdc = ctypes.windll.user32.GetDC(0)
    result = ctypes.windll.gdi32.GetDeviceGammaRamp(hdc, ctypes.byref(full_gamma_ramp))
    ctypes.windll.user32.ReleaseDC(0, hdc)
    
    if result:
        for i in range(256):
            gamma_ramp_r[i] = full_gamma_ramp[i]
            gamma_ramp_g[i] = full_gamma_ramp[i + 256]
            gamma_ramp_b[i] = full_gamma_ramp[i + 512]
        
        # Calculate color temperature from the gamma ramps (this is a simplified approach)
        red = gamma_ramp_r[255] >> 8
        green = gamma_ramp_g[255] >> 8
        blue = gamma_ramp_b[255] >> 8
        
        if red==255 & green==255 & blue == 255:
            settings = load_settings()
            bsObj.set(settings["brightness"])
            try:
                color_temperature = settings['color_temperature']
            except (FileNotFoundError, KeyError):
                 color_temperature  = 3500
            csObj.set(color_temperature)
        elif red == 255:
            temp = 0.05 + np.exp((green + 161.1195681661) / 99.4708025861)
        elif blue == 255:
            temp = 60-0.5 + (red/329.698727446)** (1/-0.1332047592)
        

        return temp*100.0
    else:
        print("Failed to get gamma ramp")
        return None
