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

def app(page: ft.Page):
    global cps, cps_text_bar, Cps_Slider, mouse_button, button, Select_Key
    page.title = "AutoClicker"
    page.window.width = 840
    page.window.height = 400
    page.window.center()
    
    def cps_update(e):
        global cps, cps_text_bar, Cps_Slider
        cps = cps_text_bar.value
        if cps_text_bar.value == '':
            Cps_Slider.value = 1
            Cps_Slider.update()
        else:
            cps_text_bar.value = int(cps_text_bar.value)
            if cps_text_bar.value > 200:
                Cps_Slider.value = 200
                Cps_Slider.update()
            else:
                Cps_Slider.value = int(cps_text_bar.value)
                Cps_Slider.update()

    cps_text_bar = ft.TextField(
        label="Click per second",
        value=18,
        on_change=lambda e: cps_update(e),
        width=120
    )
    
    cps = cps_text_bar.value
    
    def button_changing(e):
        global button
        if int(e.data) == 0:
            button = Button.left
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

    Activation_mode = ft.CupertinoSlidingSegmentedButton(
            selected_index=0,
            on_change=lambda e: print(f"selected_index: {e.data}"),
            padding=ft.padding.symmetric(0, 5),
            controls=[
                ft.Text("Hold"),
                ft.Text("Toggle")
            ]
        )
    
    def cps_text_bar_update(e):
        global cps
        setattr(cps_text_bar, "value", int(e.control.value)), cps_text_bar.update()
        cps = cps_text_bar.value
    
    Cps_Slider = ft.Slider(
        min=0,
        max=200,
        value=25,
        divisions=200,
        label="{value}",
        on_change=lambda e: cps_text_bar_update(e)
        )
        
    
    Activation_test = ft.Text(
        "Activation Key:", 
        theme_style=ft.TextThemeStyle.TITLE_MEDIUM
        )

    Select_Key = ft.OutlinedButton(
        "Select...", 
        on_click=lambda e: main(),
        data=0,
        )
    first_row = ft.Row([cps_text_bar, Clicks, Activation_mode, Activation_test, Select_Key])
    
    page.add(first_row, Cps_Slider)


def on_mouse_click_select(_, __, button, pressed):
    global selected_key, Select_Key, keyy
    keyy = 'is_mouse'
    if pressed:
        selected_key = button
        print(f"Вы выбрали кнопку мыши: {button}")
        Select_Key.text = selected_key
        Select_Key.update()
        stop_event.set()
        return False


def on_key_press_select(key):
    global selected_key, keyy
    keyy = 'is_keyboard'
    selected_key = key
    print(f"Вы выбрали клавишу: {key}")
    Select_Key.text = selected_key
    Select_Key.update()
    stop_event.set()
    return False
    # try:
        # selected_key = key
        # print(f"Вы выбрали клавишу: {key}")
        # stop_event.set()
        # return False
    # except Exception as e:
        # print(f"Ошибка при выборе клавиши: {e}")


def selecter_mouse():
    with mouse.Listener(on_click=on_mouse_click_select) as mouse_listener:
        while not stop_event.is_set():
            mouse_listener.join(0.1)

def selecter_keyboard():
    with keyboard.Listener(on_press=on_key_press_select) as keyboard_listener:
        while not stop_event.is_set():
            keyboard_listener.join(0.1)

def is_mouse_clicked():
    return ctypes.windll.user32.GetAsyncKeyState(mouse_key) != 0

def is_keyboard_clicked():
    return kb.is_pressed(selected_key)

def mouse_clicker():
    global cps, button
    while True:
        if is_mouse_clicked():
            interval = 1 / int(cps)
            start_time = time.perf_counter()
            while is_mouse_clicked():
                current_time = time.perf_counter()
                if current_time - start_time >= interval:
                    active_mouse.click(button)
                    start_time = current_time

def keyboard_clicker():
    global cps, button
    while True:
        if is_keyboard_clicked():
            interval = 1 / int(cps)
            start_time = time.perf_counter()
            while is_keyboard_clicked():
                current_time = time.perf_counter()
                if current_time - start_time >= interval:
                    active_mouse.click(button)
                    start_time = current_time

def main():
    global mouse_key, keyy, selected_key
    stop_event.clear()
    print("selecting")
    thread1 = threading.Thread(target=selecter_mouse)
    thread2 = threading.Thread(target=selecter_keyboard)
    thread1.start()
    thread2.start()
    thread1.join()
    thread2.join()
    
    if selected_key == None:
        time.sleep(0.4)
    elif keyy == 'is_mouse':
        print('is_mouse')
        if selected_key == Button.x2:
            mouse_key = 0x06
        elif selected_key == Button.x1:
            mouse_key = 0x05
        elif selected_key == Button.middle:
            mouse_key = 0x04
        elif selected_key == Button.left:
            mouse_key = 0x03
        elif selected_key == Button.right:
            mouse_key = 0x02
        mouse_clicker()
    elif keyy == 'is_keyboard':
        selected_key = str(selected_key).replace("'", "")
        print(selected_key)
        keyboard_clicker()

if __name__ == '__main__':
    ft.app(target=app)