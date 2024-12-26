import win32con
import win32api
import time
from pynput.mouse import Controller, Button, Listener
from pynput import mouse, keyboard

mouse = Controller()

cps = int(input())
interval = 1 / cps

def is_caps_lock_on():
    return win32api.GetKeyState(win32con.VK_CAPITAL) & 0x0001 != 0



while True:
    if is_caps_lock_on():
        start_time = time.perf_counter()
        while is_caps_lock_on():
            current_time = time.perf_counter()
            if current_time - start_time >= interval:
                mouse.click(Button.left)
                start_time = current_time
    else:
        time.sleep(0.3)
