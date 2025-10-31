# clicker_logic.py
import platform
import time
import threading
from pynput.mouse import Button as PynputButton

IS_WINDOWS = platform.system() == "Windows"
IS_MAC = platform.system() == "Darwin"
HAVE_QUARTZ = False

if IS_MAC:
    try:
        import Quartz
        from Quartz import (
            CGEventCreate,
            CGEventGetLocation,
            CGEventCreateMouseEvent,
            CGEventPost,
            CGEventSourceCreate,
            CGEventSourceSetLocalEventsSuppressionInterval,
            kCGHIDEventTap,
            kCGEventSourceStateCombinedSessionState,
            kCGMouseButtonLeft,
            kCGMouseButtonRight,
            kCGMouseButtonCenter,
            kCGEventLeftMouseDown,
            kCGEventLeftMouseUp,
            kCGEventRightMouseDown,
            kCGEventRightMouseUp,
            kCGEventOtherMouseDown,
            kCGEventOtherMouseUp,
        )
        HAVE_QUARTZ = True
    except Exception:
        HAVE_QUARTZ = False

if not (IS_MAC and HAVE_QUARTZ) and not IS_WINDOWS:
    # fallback — обычный pynput на Linux и пр.
    from pynput.mouse import Controller as PynputController


# -------------------- WINDOWS backend via SendInput --------------------
if IS_WINDOWS:
    import ctypes
    from ctypes import wintypes

    if hasattr(wintypes, "ULONG_PTR"):
        ULONG_PTR = wintypes.ULONG_PTR
    else:
        # Fallback if ctypes.wintypes does not expose ULONG_PTR.
        ULONG_PTR = ctypes.c_ulonglong if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_ulong

    # Константы SendInput
    INPUT_MOUSE = 0
    MOUSEEVENTF_LEFTDOWN   = 0x0002
    MOUSEEVENTF_LEFTUP     = 0x0004
    MOUSEEVENTF_RIGHTDOWN  = 0x0008
    MOUSEEVENTF_RIGHTUP    = 0x0010
    MOUSEEVENTF_MIDDLEDOWN = 0x0020
    MOUSEEVENTF_MIDDLEUP   = 0x0040

    class MOUSEINPUT(ctypes.Structure):
        _fields_ = [
            ("dx", wintypes.LONG),
            ("dy", wintypes.LONG),
            ("mouseData", wintypes.DWORD),
            ("dwFlags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ULONG_PTR),
        ]

    class _I(ctypes.Union):
        _fields_ = [("mi", MOUSEINPUT)]

    class INPUT(ctypes.Structure):
        _anonymous_ = ("i",)
        _fields_ = [("type", wintypes.DWORD), ("i", _I)]

    _SendInput = ctypes.windll.user32.SendInput

    _EXTRA_MARK = 0xC1A0C1A0  # пометка наших синтетических событий

    def _send_mouse(flags: int):
        inp = INPUT()
        inp.type = INPUT_MOUSE
        # dx,dy=0 => клик строго в текущей позиции, без перемещения курсора
        inp.mi = MOUSEINPUT(0, 0, 0, flags, 0, _EXTRA_MARK)
        _SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))


class _MacQuartzClicker:
    """Кликер через Quartz — минимальное вмешательство, нет лагов курсора."""
    def __init__(self):
        self.source = CGEventSourceCreate(kCGEventSourceStateCombinedSessionState)
        CGEventSourceSetLocalEventsSuppressionInterval(self.source, 0.0)

    def _post_click(self, button: PynputButton):
        x, y = CGEventGetLocation(CGEventCreate(None))
        if button == PynputButton.left:
            b = kCGMouseButtonLeft;  down_t, up_t = kCGEventLeftMouseDown,  kCGEventLeftMouseUp
        elif button == PynputButton.right:
            b = kCGMouseButtonRight; down_t, up_t = kCGEventRightMouseDown, kCGEventRightMouseUp
        else:
            b = kCGMouseButtonCenter; down_t, up_t = kCGEventOtherMouseDown, kCGEventOtherMouseUp
        CGEventPost(kCGHIDEventTap, CGEventCreateMouseEvent(self.source, down_t, (x, y), b))
        CGEventPost(kCGHIDEventTap, CGEventCreateMouseEvent(self.source, up_t,   (x, y), b))

    def click(self, button: PynputButton):
        self._post_click(button)


class _PynputClicker:
    def __init__(self):
        self._mouse = PynputController()

    def click(self, button: PynputButton):
        self._mouse.click(button)


class _WinClicker:
    """SendInput-кликер без перемещения и дрожи указателя."""
    def click(self, button: PynputButton):
        if button == PynputButton.left:
            _send_mouse(MOUSEEVENTF_LEFTDOWN);  _send_mouse(MOUSEEVENTF_LEFTUP)
        elif button == PynputButton.right:
            _send_mouse(MOUSEEVENTF_RIGHTDOWN); _send_mouse(MOUSEEVENTF_RIGHTUP)
        else:
            _send_mouse(MOUSEEVENTF_MIDDLEDOWN); _send_mouse(MOUSEEVENTF_MIDDLEUP)


class ClickerSettings:
    def __init__(self, cps=18, button=PynputButton.left, mode="hold"):
        self.cps = max(1, min(200, cps))
        self.button = button
        self.mode = mode


class Clicker:
    def __init__(self, settings: ClickerSettings):
        self.settings = settings
        # backend
        if IS_MAC and HAVE_QUARTZ:
            self._backend = _MacQuartzClicker()
        elif IS_WINDOWS:
            self._backend = _WinClicker()
        else:
            self._backend = _PynputClicker()

        self._running = threading.Event()
        self._lock = threading.Lock()
        self._active = False
        self._last_state = False
        self._input_check = lambda: False

        # подавляем самовозбуждение, когда горячая — мышь
        self._input_is_mouse = False
        self._suppress_until = 0.0   # time.monotonic()

    def set_input_checker(self, checker_fn):
        self._input_check = checker_fn
        # KeySelector будет помечать checker_fn атрибутами
        self._input_is_mouse = bool(getattr(checker_fn, "is_mouse", False))

    def start(self):
        self._running.clear()
        threading.Thread(target=self._run_click_loop, daemon=True).start()
        threading.Thread(target=self._run_activation_loop, daemon=True).start()

    def stop(self):
        self._running.set()

    def _run_click_loop(self):
        min_sleep = 1 / max(1, self.settings.cps)
        while not self._running.is_set():
            if self._active:
                try:
                    # короткое окно, в которое детектор не считает "нажатие"
                    self._suppress_until = time.monotonic() + 0.03
                    self._backend.click(self.settings.button)
                except Exception:
                    pass
                time.sleep(min_sleep)
            else:
                time.sleep(0.05)

    def _run_activation_loop(self):
        while not self._running.is_set():
            state = self._input_check()
            # Если горячая — мышь, игнорируем "нажатие" внутри окна подавления
            if self._input_is_mouse and time.monotonic() < self._suppress_until:
                state = False

            if self.settings.mode == "hold":
                with self._lock:
                    self._active = state
            elif state and not self._last_state:
                with self._lock:
                    self._active = not self._active
                time.sleep(0.2)  # антидребезг
            self._last_state = state
            time.sleep(0.01)
