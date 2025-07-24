import flet as ft
from clicker_logic import ClickerSettings, Clicker
from key_selector import KeySelector

def build_ui(page: ft.Page):
    page.title = "AutoClicker"
    page.window.width = 840
    page.window.height = 400
    page.window.center()

    settings = ClickerSettings()
    clicker = Clicker(settings)

    cps_input = ft.TextField(label="CPS", value="18", width=120)
    cps_slider = ft.Slider(min=1, max=200, value=18, divisions=199, label="{value}")

    def update_cps(e=None):
        try:
            val = int(cps_input.value)
        except ValueError:
            val = 1
        val = max(1, min(200, val))
        cps_input.value = str(val)
        cps_slider.value = val
        settings.cps = val
        page.update()

    cps_input.on_change = update_cps
    cps_slider.on_change = lambda e: (setattr(cps_input, 'value', str(int(e.control.value))), update_cps())[1]

    button_selector = ft.CupertinoSlidingSegmentedButton(
        selected_index=0,
        on_change=lambda e: setattr(settings, "button", [settings.button.left, settings.button.middle, settings.button.right][int(e.data)]),
        controls=[ft.Text("Left"), ft.Text("Middle"), ft.Text("Right")]
    )

    mode_selector = ft.CupertinoSlidingSegmentedButton(
        selected_index=0,
        on_change=lambda e: setattr(settings, "mode", ["hold", "toggle"][int(e.data)]),
        controls=[ft.Text("Hold"), ft.Text("Toggle")]
    )

    select_btn = ft.OutlinedButton("Select...", data=0)

    def select_key(e):
        select_btn.text = "Waiting..."
        page.update()
        selector = KeySelector()
        key, key_type = selector.select()
        clicker.set_input_checker(selector.get_input_checker())
        select_btn.text = str(key)
        page.update()
        clicker.start()

    select_btn.on_click = select_key

    row = ft.Row([cps_input, button_selector, mode_selector, ft.Text("Activation Key:"), select_btn])
    page.add(row, cps_slider)
