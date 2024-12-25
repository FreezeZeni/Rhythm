# type: ignore
from pynput.mouse import Controller, Button 
mouse = Controller()
import win32api
import win32con
import flet as ft
import time

# cps = int(input())
# interval = 1 / cps

def is_caps_lock_on():
    return win32api.GetKeyState(win32con.VK_CAPITAL) & 0x0001 != 0

# def autoclicker():
    # while True:
        # if is_caps_lock_on():
            # start_time = time.perf_counter()
            # while is_caps_lock_on():
                # current_time = time.perf_counter()
                # if current_time - start_time >= interval:
                    # mouse.click(Button.left)
                    # start_time = current_time
        # else:
            # time.sleep(0.3)


def app(page: ft.Page):
    page.title = "AutoClicker"
    page.window.width = 840
    page.window.height = 400
    page.window.center()

    cps_text_bar = ft.TextField(
        label="Click per second",
        value=18,
        width=120
    )
    
    Clicks = ft.CupertinoSlidingSegmentedButton(
            selected_index=0,
            on_change=lambda e: print(f"selected_index: {e.data}"),
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
    
    Cps_Slider = ft.Slider(
        min=0,
        max=200,
        value=18,
        divisions=200,
        label="{value}",
        on_change=lambda e: (setattr(cps_text_bar, "value", int(e.control.value)), cps_text_bar.update())
        )
    
    Activation_test = ft.Text("Activation Key:", theme_style=ft.TextThemeStyle.TITLE_MEDIUM)

    Select_Key = ft.OutlinedButton("Select...", on_click=lambda e: print('hi'), data=0)
    
    first_row = ft.Row([cps_text_bar, Clicks, Activation_mode, Activation_test, Select_Key])
    
    page.add(first_row, Cps_Slider)

if __name__ == '__main__':
    ft.app(target=app)