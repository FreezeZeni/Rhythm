from pynput import mouse

selected_button = None

def on_click_select(_, __, button, pressed):
    """Выбор кнопки мыши."""
    global selected_button
    if pressed:
        selected_button = button
        print(f"Вы выбрали кнопку: {button}")
        return False

def on_click_action(_, __, button, pressed):
    if pressed and button == selected_button:
        print(f"Выбранная кнопка '{selected_button}' была нажата!")

print("Нажмите кнопку мыши (MButton, XButton1, XButton2), чтобы выбрать её...")
with mouse.Listener(on_click=on_click_select) as listener:
    listener.join()

print(f"Слушаем нажатия кнопки '{selected_button}'. Нажмите CTRL+C для завершения.")
with mouse.Listener(on_click=on_click_action) as listener:
    listener.join()
