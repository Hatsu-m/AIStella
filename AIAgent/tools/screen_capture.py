import os
import time
from mss import mss
from PIL import Image

def get_screenshot():
    with mss() as sct:
        monitor = sct.monitors[0]
        screenshot = sct.grab(monitor)
    img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
    screenshots_dir = os.path.join(os.getcwd(), "screenshots")
    os.makedirs(screenshots_dir, exist_ok=True)
    timestamp = int(time.time() * 1000)
    file_path = os.path.join(screenshots_dir, f"screenshot_{timestamp}.png")
    img.save(file_path)
    return img, file_path
