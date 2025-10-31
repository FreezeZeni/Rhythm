# key_selector.py
import ctypes
import platform
import threading

from pynput import mouse, keyboard
from pynput.mouse import Button

IS_MAC = platform.system() == "Darwin"
IS_WINDOWS = platform.system() == "Windows"
HAVE_QUARTZ = False
if IS_MAC:
    try:
        from Quartz import (
            CGEventTapCreate,
            kCGSessionEventTap,               # <— используем session
            kCGHeadInsertEventTap,
            kCGEventTapOptionListenOnly,      # <— «слушаем», не вмешиваемся
            CGEventMaskBit,
            kCGEventLeftMouseDown,
            kCGEventLeftMouseUp,
            kCGEventRightMouseDown,
            kCGEventRightMouseUp,
            kCGEventOtherMouseDown,
            kCGEventOtherMouseUp,
            kCGEventTapDisabledByTimeout,
            CGEventGetIntegerValueField,
            kCGMouseEventButtonNumber,
            CGEventTapEnable,
        )
        from CoreFoundation import (
            CFMachPortCreateRunLoopSource,
            CFRunLoopAddSource,
            CFRunLoopGetCurrent,
            CFRunLoopRun,
            CFRunLoopStop,
            kCFRunLoopCommonModes,
        )
        HAVE_QUARTZ = True
    except Exception:
        HAVE_QUARTZ = False


def _mouse_label_from_number(n: int) -> str:
    if n == 0:
        return "Mouse Left"
    if n == 1:
        return "Mouse Right"
    if n == 2:
        return "Mouse Middle"
    if n == 3:
        return "Mouse X1"
    if n == 4:
        return "Mouse X2"
    return f"Mouse X{n}"


class _MouseLabel:
    def __init__(self, number: int):
        self.number = number
        self.label = _mouse_label_from_number(number)

    def __str__(self):
        return self.label


class _MacMouseTap:
    def __init__(self, on_event):
        if not (IS_MAC and HAVE_QUARTZ):
            raise RuntimeError("Mac mouse tap is only available on macOS with Quartz.")
        self.on_event = on_event
        self._thread = None
        self._loop = None
        self._tap = None

    def _run(self):
        mask = (
            CGEventMaskBit(kCGEventLeftMouseDown)
            | CGEventMaskBit(kCGEventLeftMouseUp)
            | CGEventMaskBit(kCGEventRightMouseDown)
            | CGEventMaskBit(kCGEventRightMouseUp)
            | CGEventMaskBit(kCGEventOtherMouseDown)
            | CGEventMaskBit(kCGEventOtherMouseUp)
        )

        def _callback(_proxy, typ, event, _refcon):
            if typ == kCGEventTapDisabledByTimeout:
                CGEventTapEnable(self._tap, True)
                return event

            if typ in (kCGEventLeftMouseDown, kCGEventLeftMouseUp):
                btn = 0
                pressed = typ == kCGEventLeftMouseDown
            elif typ in (kCGEventRightMouseDown, kCGEventRightMouseUp):
                btn = 1
                pressed = typ == kCGEventRightMouseDown
            elif typ in (kCGEventOtherMouseDown, kCGEventOtherMouseUp):
                btn = int(CGEventGetIntegerValueField(event, kCGMouseEventButtonNumber))
                pressed = typ == kCGEventOtherMouseDown
            else:
                return event

            try:
                self.on_event(btn, pressed)
            except Exception:
                pass
            return event

        self._tap = CGEventTapCreate(
            kCGSessionEventTap,             # раньше было kCGHIDEventTap
            kCGHeadInsertEventTap,
            kCGEventTapOptionListenOnly,    # раньше было kCGEventTapOptionDefault
            mask,
            _callback,
            None,
        )
        if not self._tap:
            return

        src = CFMachPortCreateRunLoopSource(None, self._tap, 0)
        self._loop = CFRunLoopGetCurrent()
        CFRunLoopAddSource(self._loop, src, kCFRunLoopCommonModes)
        CGEventTapEnable(self._tap, True)
        CFRunLoopRun()

    def start(self):
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        if self._loop is not None:
            CFRunLoopStop(self._loop)
        if self._thread is not None:
            self._thread.join(timeout=0.5)


class KeySelector:
    def __init__(self):
        self.selected_key = None
        self.key_type = None
        self._stop_event = threading.Event()
        self._monitor = None

    def select(self, on_update_ui=None):
        self.selected_key = None
        self._stop_event.clear()

        key_listener = keyboard.Listener(on_press=self._on_key_press)
        key_listener.start()

        if IS_MAC and HAVE_QUARTZ:
            def _on_mouse(btn_num: int, pressed: bool):
                if pressed and not self._stop_event.is_set():
                    self.key_type = "mouse"
                    self.selected_key = _MouseLabel(btn_num)
                    self._stop_event.set()
            mac_tap = _MacMouseTap(_on_mouse)
            mac_tap.start()
        else:
            mouse_listener = mouse.Listener(on_click=self._on_mouse_click)
            mouse_listener.start()

        self._stop_event.wait()

        key_listener.stop()
        if IS_MAC and HAVE_QUARTZ:
            mac_tap.stop()
        else:
            mouse_listener.stop()

        return self.selected_key, self.key_type

    def _on_mouse_click(self, x, y, btn, pressed):
        if pressed and not self._stop_event.is_set():
            self.key_type = "mouse"
            self.selected_key = btn
            self._stop_event.set()

    def _on_key_press(self, key):
        if not self._stop_event.is_set():
            self.key_type = "keyboard"
            self.selected_key = str(key).replace("'", "").replace("Key.", "")
            self._stop_event.set()

    def get_input_checker(self):
        if self.key_type == "mouse":
            if IS_WINDOWS and isinstance(self.selected_key, Button):
                button_to_vk = {
                    Button.left: 0x01,
                    Button.right: 0x02,
                    Button.middle: 0x04,
                    Button.x1: 0x05,
                    Button.x2: 0x06,
                }
                vk_code = button_to_vk.get(self.selected_key)
                if vk_code is not None:
                    user32 = ctypes.windll.user32
                    user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
                    user32.GetAsyncKeyState.restype = ctypes.c_short

                    def checker():
                        return bool(user32.GetAsyncKeyState(vk_code) & 0x8000)

                    checker.is_mouse = True
                    return checker

            if IS_MAC and HAVE_QUARTZ and isinstance(self.selected_key, _MouseLabel):
                target_num = self.selected_key.number
                state = {"down": False}

                def _on_mouse(btn_num: int, pressed: bool):
                    if btn_num == target_num:
                        state["down"] = pressed

                self._monitor = _MacMouseTap(_on_mouse)
                self._monitor.start()
                return lambda: state["down"]

            if isinstance(self.selected_key, Button):
                target = self.selected_key
                state = {"down": False}

                def on_click(x, y, btn, pressed):
                    if btn == target:
                        state["down"] = pressed

                self._monitor = mouse.Listener(on_click=on_click)
                self._monitor.start()
                fn = lambda: state["down"]
                fn.is_mouse = True
                return fn

            return lambda: False

        if self.key_type == "keyboard":
            target_name = self.selected_key
            key_obj = getattr(keyboard.Key, target_name, None)
            if key_obj is None:
                key_obj = keyboard.KeyCode.from_char(target_name)

            state = {"down": False}

            def on_press(k):
                if k == key_obj:
                    state["down"] = True

            def on_release(k):
                if k == key_obj:
                    state["down"] = False

            self._monitor = keyboard.Listener(on_press=on_press, on_release=on_release)
            self._monitor.start()
            fn = lambda: state["down"]
            fn.is_mouse = False       # <— ДОБАВЛЕНО
            return fn

        return lambda: False
