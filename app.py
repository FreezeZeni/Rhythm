# type: ignore
from pynput.mouse import Controller, Button
active_mouse = Controller()
import flet as ft
import time
import ctypes

from pynput import mouse, keyboard
from pynput.mouse import Listener
import threading
import time
import keyboard as kb

selected_key = None
keyy = None
stop_event = threading.Event()
mouse_key = None
button = Button.left
cps = 18
toggle_active = False
toggle_lock = threading.Lock()
clicker_stop_event = threading.Event()

def app(page: ft.Page):
    global cps, cps_text_bar, Cps_Slider, mouse_button, button, Select_Key
    page.title = "AutoClicker"
    page.window.width = 840
    page.window.height = 400
    page.window.center()
    
    def cps_update(e):
        global cps, cps_text_bar, Cps_Slider
        try:
            if cps_text_bar.value == '':
                cps = 1
                Cps_Slider.value = 1
            else:
                cps_value = int(cps_text_bar.value)
                cps = min(200, max(1, cps_value))
                Cps_Slider.value = cps
                cps_text_bar.value = cps
            Cps_Slider.update()
            cps_text_bar.update()
        except ValueError:
            cps = 1
            cps_text_bar.value = "1"
            Cps_Slider.value = 1
            Cps_Slider.update()
            cps_text_bar.update()

    cps_text_bar = ft.TextField(
        label="Click per second",
        value="18",
        on_change=lambda e: cps_update(e),
        width=120
    )
    
    cps = int(cps_text_bar.value)
    
    def button_changing(e):
        global button
        if int(e.data) == 0:
            button = Button.left
        elif int(e.data) == 1:
            button = Button.middle
        elif int(e.data) == 2:
            button = Button.right
            
    Clicks = ft.CupertinoSlidingSegmentedButton(
            selected_index=0,
            on_change=lambda e: button_changing(e),
            padding=ft.padding.symmetric(0, 10),
            controls=[
                ft.Text("Left"),
                ft.Text("Middle"),
                ft.Text("Right")
            ],
        )

    global activation_mode
    activation_mode = "hold"
    
    def activation_mode_change(e):
        global activation_mode, toggle_active
        if int(e.data) == 0:
            activation_mode = "hold"
            with toggle_lock:
                toggle_active = False
        else:
            activation_mode = "toggle"

    Activation_mode = ft.CupertinoSlidingSegmentedButton(
            selected_index=0,
            on_change=lambda e: activation_mode_change(e),
            padding=ft.padding.symmetric(0, 5),
            controls=[
                ft.Text("Hold"),
                ft.Text("Toggle")
            ]
        )
    
    def cps_slider_update(e):
        global cps
        cps = int(e.control.value)
        cps_text_bar.value = str(cps)
        cps_text_bar.update()
    
    Cps_Slider = ft.Slider(
        min=1,
        max=200,
        value=18,
        divisions=199,
        label="{value}",
        on_change=cps_slider_update
        )
    
    Activation_test = ft.Text(
        "Activation Key:", 
        theme_style=ft.TextThemeStyle.TITLE_MEDIUM
        )

    Select_Key = ft.OutlinedButton(
        "Select...",
        on_click=lambda e: select_key_thread(),
        data=0,
        )
    
    first_row = ft.Row([cps_text_bar, Clicks, Activation_mode, Activation_test, Select_Key])
    
    page.add(first_row, Cps_Slider)


def on_mouse_click_select(_, __, button, pressed):
    global selected_key, Select_Key, keyy
    keyy = 'is_mouse'
    if pressed:
        selected_key = button
        print(f"Selected mouse button: {button}")
        Select_Key.text = str(button).replace("Button.", "")
        Select_Key.update()
        stop_event.set()
        return False


def on_key_press_select(key):
    global selected_key, keyy
    keyy = 'is_keyboard'
    selected_key = key
    print(f"Selected key: {key}")
    selected_key = str(selected_key).replace("'", "")
    selected_key = str(selected_key).replace("Key.", "")
    Select_Key.text = selected_key
    Select_Key.update()
    stop_event.set()
    return False


def selecter():
    with mouse.Listener(on_click=on_mouse_click_select) as mouse_listener, \
         keyboard.Listener(on_press=on_key_press_select) as keyboard_listener:

        while not stop_event.is_set():
            mouse_listener.join(0.1)
            keyboard_listener.join(0.1)


def is_mouse_clicked():
    return ctypes.windll.user32.GetAsyncKeyState(mouse_key) & 0x8000 != 0


def is_keyboard_clicked():
    global selected_key
    if selected_key is None:
        return False
    try:
        return kb.is_pressed(selected_key)
    except TypeError:
        print(f"Error with key: {selected_key}")
        return False


def auto_click_worker():
    global cps, button, clicker_stop_event
    while not clicker_stop_event.is_set():
        if toggle_active:
            interval = 1.0 / int(cps)
            active_mouse.click(button)
            time.sleep(interval)
        else:
            time.sleep(0.05)


def mouse_clicker():
    global cps, button, activation_mode, toggle_active, clicker_stop_event
    
    while not clicker_stop_event.is_set():
        current_state = is_mouse_clicked()
        
        if activation_mode == "hold":
            with toggle_lock:
                toggle_active = current_state
        else:
            if current_state and not last_state:
                with toggle_lock:
                    toggle_active = not toggle_active
                    print(f"Toggle mode: {'ON' if toggle_active else 'OFF'}")

                time.sleep(0.2)
                
        last_state = current_state
        time.sleep(0.01)


def keyboard_clicker():
    global cps, button, activation_mode, toggle_active, clicker_stop_event

    last_state = False
    
    while not clicker_stop_event.is_set():
        current_state = is_keyboard_clicked()
        
        if activation_mode == "hold":
            with toggle_lock:
                toggle_active = current_state
        else:
            if current_state and not last_state:
                with toggle_lock:
                    toggle_active = not toggle_active
                    print(f"Toggle mode: {'ON' if toggle_active else 'OFF'}")

                time.sleep(0.2)
                
        last_state = current_state
        time.sleep(0.01)


def select_key_thread():
    threading.Thread(target=main, daemon=True).start()


def main():
    global mouse_key, keyy, selected_key, toggle_active, clicker_stop_event

    Select_Key.text = "..."
    Select_Key.update()
    clicker_stop_event.set()
    time.sleep(0.2)
    clicker_stop_event = threading.Event()

    with toggle_lock:
        toggle_active = False
    
    stop_event.clear()
    selected_key = None
    print("selecting key or button...")
    thread1 = threading.Thread(target=selecter)
    thread1.start()
    thread1.join()
    
    if selected_key is None:
        print("No key selected")
        return
    
    clicker_thread = threading.Thread(target=auto_click_worker, daemon=True)
    clicker_thread.start()

    if keyy == 'is_mouse':
        print('Mouse button selected')
        if selected_key == Button.x2:
            mouse_key = 0x06
        elif selected_key == Button.x1:
            mouse_key = 0x05
        elif selected_key == Button.middle:
            mouse_key = 0x04
        elif selected_key == Button.left:
            mouse_key = 0x01
        elif selected_key == Button.right:
            mouse_key = 0x02

        mouse_thread = threading.Thread(target=mouse_clicker, daemon=True)
        mouse_thread.start()
        
    elif keyy == 'is_keyboard':
        selected_key = str(selected_key).replace("'", "")
        selected_key = str(selected_key).replace("Key.", "")
        print(f"Keyboard key selected: {selected_key}")

        keyboard_thread = threading.Thread(target=keyboard_clicker, daemon=True)
        keyboard_thread.start()

if __name__ == '__main__':
    ft.app(target=app)