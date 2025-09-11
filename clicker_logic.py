import platform
import time
import threading
from pynput.mouse import Button as PynputButton

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

if not (IS_MAC and HAVE_QUARTZ):
    # fallback — обычный pynput
    from pynput.mouse import Controller as PynputController


def _current_cursor_pos():
    # возвращает (x, y)
    evt = CGEventCreate(None)
    loc = CGEventGetLocation(evt)
    return (loc.x, loc.y)


class _MacQuartzClicker:
    """Кликер через Quartz — минимальное вмешательство, нет лагов курсора."""
    def __init__(self):
        self.source = CGEventSourceCreate(kCGEventSourceStateCombinedSessionState)
        # критично: не глушим локальные события после синтетических
        CGEventSourceSetLocalEventsSuppressionInterval(self.source, 0.0)

    def _post_click(self, button: PynputButton):
        x, y = _current_cursor_pos()

        if button == PynputButton.left:
            b = kCGMouseButtonLeft
            down_t, up_t = kCGEventLeftMouseDown, kCGEventLeftMouseUp
        elif button == PynputButton.right:
            b = kCGMouseButtonRight
            down_t, up_t = kCGEventRightMouseDown, kCGEventRightMouseUp
        else:
            # middle (или любой «другой» в терминах CG)
            b = kCGMouseButtonCenter
            down_t, up_t = kCGEventOtherMouseDown, kCGEventOtherMouseUp

        ev_down = CGEventCreateMouseEvent(self.source, down_t, (x, y), b)
        CGEventPost(kCGHIDEventTap, ev_down)

        ev_up = CGEventCreateMouseEvent(self.source, up_t, (x, y), b)
        CGEventPost(kCGHIDEventTap, ev_up)

    def click(self, button: PynputButton):
        self._post_click(button)


class _PynputClicker:
    def __init__(self):
        self._mouse = PynputController()

    def click(self, button: PynputButton):
        self._mouse.click(button)


class ClickerSettings:
    def __init__(self, cps=18, button=PynputButton.left, mode="hold"):
        self.cps = max(1, min(200, cps))
        self.button = button
        self.mode = mode


class Clicker:
    def __init__(self, settings: ClickerSettings):
        self.settings = settings
        # backend выбирается один раз
        if IS_MAC and HAVE_QUARTZ:
            self._backend = _MacQuartzClicker()
        else:
            self._backend = _PynputClicker()

        self._running = threading.Event()
        self._lock = threading.Lock()
        self._active = False
        self._last_state = False
        self._input_check = lambda: False

    def set_input_checker(self, checker_fn):
        self._input_check = checker_fn

    def start(self):
        self._running.clear()
        threading.Thread(target=self._run_click_loop, daemon=True).start()
        threading.Thread(target=self._run_activation_loop, daemon=True).start()

    def stop(self):
        self._running.set()

    def _run_click_loop(self):
        # Небольшая защита от «дрёжи» на высоких CPS
        min_sleep = 1 / max(1, self.settings.cps)
        while not self._running.is_set():
            if self._active:
                try:
                    self._backend.click(self.settings.button)
                except Exception:
                    pass
                time.sleep(min_sleep)
            else:
                time.sleep(0.05)

    def _run_activation_loop(self):
        while not self._running.is_set():
            state = self._input_check()
            if self.settings.mode == "hold":
                with self._lock:
                    self._active = state
            elif state and not self._last_state:
                with self._lock:
                    self._active = not self._active
                time.sleep(0.2)
            self._last_state = state
            time.sleep(0.01)