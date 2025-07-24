from pynput.mouse import Controller, Button
import time
import threading

class ClickerSettings:
    def __init__(self, cps=18, button=Button.left, mode="hold"):
        self.cps = max(1, min(200, cps))
        self.button = button
        self.mode = mode

class Clicker:
    def __init__(self, settings: ClickerSettings):
        self.settings = settings
        self.mouse = Controller()
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
        while not self._running.is_set():
            if self._active:
                self.mouse.click(self.settings.button)
                time.sleep(1 / self.settings.cps)
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
