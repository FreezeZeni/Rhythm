# ui.py
import threading
import flet as ft
from pynput.mouse import Button
from clicker_logic import ClickerSettings, Clicker
from key_selector import KeySelector


def build_ui(page: ft.Page):
    # Window and theme
    page.title = "Clickaizen AutoClicker"
    page.window.width = 840
    # Увеличили высоту, чтобы уместить два профиля вертикально
    page.window.height = 600
    page.window.center()
    page.padding = 8
    page.spacing = 6
    # Use hex colors for compatibility across Flet versions
    page.theme = ft.Theme(color_scheme_seed="#00BCD4")
    # Полностью убираем верхний баннер/заголовок
    page.appbar = None

    # Профили создаются ниже; глобальные настройки не нужны

    # Вспомогательная фабрика: один профиль кликера (для независимой работы)
    def make_profile(title: str, default_button_index: int = 0):
        settings = ClickerSettings()
        # Кнопка мыши по умолчанию
        settings.button = [Button.left, Button.middle, Button.right][default_button_index]
        clicker = Clicker(settings)

        # CPS
        cps_input = ft.TextField(label="CPS", value="18", width=100, dense=True)
        cps_slider = ft.Slider(min=1, max=200, value=18, divisions=199, label="{value}", expand=True)

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
        cps_slider.on_change = lambda e: (setattr(cps_input, "value", str(int(e.control.value))), update_cps())[1]

        # Кнопка мыши
        button_selector = ft.CupertinoSlidingSegmentedButton(
            selected_index=default_button_index,
            on_change=lambda e: setattr(settings, "button", [Button.left, Button.middle, Button.right][int(e.data)]),
            controls=[ft.Text("Left"), ft.Text("Middle"), ft.Text("Right")],
        )

        # Режим
        mode_selector = ft.CupertinoSlidingSegmentedButton(
            selected_index=0,
            on_change=lambda e: setattr(settings, "mode", ["hold", "toggle"][int(e.data)]),
            controls=[ft.Text("Hold"), ft.Text("Toggle")],
        )

        # Выбор клавиши активации
        select_btn = ft.OutlinedButton("Выбрать…")
        selected_label = ft.Text("—", italic=True, size=12)

        def select_key(e):
            select_btn.disabled = True
            select_btn.text = "Нажмите…"
            page.update()

            def worker():
                selector = KeySelector()
                key, key_type = selector.select()
                checker = selector.get_input_checker()

                def finalize():
                    clicker.set_input_checker(checker)
                    select_btn.text = "Изменить…"
                    select_btn.disabled = False
                    selected_label.value = str(key)
                    page.update()

                try:
                    page.invoke_later(finalize)
                except Exception:
                    finalize()

            threading.Thread(target=worker, daemon=True).start()

        select_btn.on_click = select_key

        # Старт/Стоп (крупная центральная кнопка под карточкой)
        running = {"value": False}

        def update_start_btn():
            if running["value"]:
                start_btn.text = "Стоп"
                start_btn.icon = "stop_circle"
                start_btn.style = ft.ButtonStyle(
                    bgcolor="#E53935",
                    color="#FFFFFF",
                    shape=ft.RoundedRectangleBorder(radius=12),
                    padding=ft.padding.symmetric(16, 18),
                )
            else:
                start_btn.text = "Старт"
                start_btn.icon = "play_arrow"
                start_btn.style = ft.ButtonStyle(
                    bgcolor="#43A047",
                    color="#FFFFFF",
                    shape=ft.RoundedRectangleBorder(radius=12),
                    padding=ft.padding.symmetric(16, 18),
                )

        def on_start_click(e):
            if not running["value"]:
                clicker.start()
                running["value"] = True
            else:
                clicker.stop()
                running["value"] = False
            update_start_btn()
            page.update()

        start_btn = ft.FilledButton(text="Старт", icon="play_arrow", on_click=on_start_click)
        update_start_btn()

        # Разметка карточки профиля
        title_row = ft.Row([
            ft.Text(title, weight=ft.FontWeight.BOLD),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        cps_row = ft.Row([cps_input, cps_slider], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER)
        selectors_row = ft.Row([
            ft.Column([ft.Text("Кнопка мыши", size=12), button_selector], spacing=4, tight=True),
            ft.Column([ft.Text("Режим", size=12), mode_selector], spacing=4, tight=True),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER)

        activation_row = ft.Row([
            select_btn,
            selected_label,
        ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER, wrap=True)

        content = ft.Column([
            title_row,
            cps_row,
            selectors_row,
            activation_row,
        ], spacing=6)
        # Убираем фон карточек: используем контейнер без фона и с меньшим padding
        card = ft.Container(content=content, padding=6)
        # Вернём разметку как «раньше»: большая кнопка по центру под карточкой
        return ft.Column([
            card,
            ft.Row([start_btn], alignment=ft.MainAxisAlignment.CENTER),
        ], spacing=6)

    # Два профиля: левый и правый кликеры
    profile_left = make_profile("Профиль 1 — Левая кнопка", default_button_index=0)
    profile_right = make_profile("Профиль 2 — Правая кнопка", default_button_index=2)

    # Располагаем профили вертикально один под другим
    page.add(profile_left, profile_right)
