import win32con
import win32api
import time
import ctypes
from pynput.mouse import Controller, Button

mouse = Controller()

cps = 23.7  # Clicks per second
interval = 1 / cps

def is_caps_lock_on():
    return win32api.GetKeyState(win32con.VK_CAPITAL) & 0x0001 != 0

def get_high_precision_timer():
    """Get a high-precision counter value from Windows performance counter"""
    counter = ctypes.c_longlong()
    freq = ctypes.c_longlong()
    ctypes.windll.kernel32.QueryPerformanceCounter(ctypes.byref(counter))
    ctypes.windll.kernel32.QueryPerformanceFrequency(ctypes.byref(freq))
    return counter.value / freq.value

def busy_wait_until(target_time):
    """Busy-wait until the specified time with maximum precision"""
    while get_high_precision_timer() < target_time:
        pass

while True:
    if is_caps_lock_on():
        # Set precise base time
        base_time = get_high_precision_timer()
        click_count = 0
        
        while is_caps_lock_on():
            # Calculate exact time for the next click
            target_time = base_time + (click_count + 1) * interval
            
            # Wait precisely until the next click time
            busy_wait_until(target_time)
            
            # Execute click exactly on time
            mouse.click(Button.left)
            click_count += 1
    else:
        time.sleep(0.01)