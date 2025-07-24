from pynput import mouse, keyboard
from pynput.mouse import Button
import ctypes
import threading
import keyboard as kb


class KeySelector:
    def __init__(self):
        self.selected_key = None
        self.key_type = None
        self._stop_event = threading.Event()

    def select(self, on_update_ui=None):
        self.selected_key = None
        self._stop_event.clear()
        mouse_listener = mouse.Listener(on_click=self._on_mouse_click)
        key_listener = keyboard.Listener(on_press=self._on_key_press)

        mouse_listener.start()
        key_listener.start()

        while not self._stop_event.is_set():
            pass

        mouse_listener.stop()
        key_listener.stop()
        return self.selected_key, self.key_type

    def _on_mouse_click(self, _, __, btn, pressed):
        if pressed:
            self.key_type = "mouse"
            self.selected_key = btn
            self._stop_event.set()

    def _on_key_press(self, key):
        self.key_type = "keyboard"
        self.selected_key = str(key).replace("'", "").replace("Key.", "")
        self._stop_event.set()

    def get_input_checker(self):
        if self.key_type == "mouse":
            key_map = {
                Button.left: 0x01,
                Button.right: 0x02,
                Button.middle: 0x04,
                Button.x1: 0x05,
                Button.x2: 0x06,
            }
            code = key_map.get(self.selected_key)
            return lambda: ctypes.windll.user32.GetAsyncKeyState(code) & 0x8000 != 0
        elif self.key_type == "keyboard":
            return lambda: kb.is_pressed(self.selected_key)
        return lambda: False
