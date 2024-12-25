from pynput import keyboard

selected_key = None

def on_custom_key():
    print(f"Выбранная клавиша '{selected_key}' была нажата!")

def on_press_select(key):
    global selected_key
    try:
        selected_key = key
        print(f"Вы выбрали клавишу: {key}")
        return False
    except Exception as e:
        print(f"Ошибка при выборе клавиши: {e}")


def on_press(key):
    global selected_key
    try:
        if key == selected_key:
            on_custom_key()
    except Exception as e:
        print(f"Ошибка при обработке нажатия: {e}")

print("Нажмите любую клавишу, которую хотите выбрать для выполнения действия...")
with keyboard.Listener(on_press=on_press_select) as listener:
    listener.join()

print(f"Слушаем нажатия клавиши '{selected_key}'. Нажмите ESC для выхода.")
with keyboard.Listener(on_press=on_press) as listener:
    listener.join()
