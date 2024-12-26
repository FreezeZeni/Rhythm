import ctypes

def is_mouse_clicked(button="left"):
    # Словарь кнопок мыши и их виртуальных кодов
    mouse_buttons = {
        "left": 0x01,    # Левая кнопка мыши
        "right": 0x02,   # Правая кнопка мыши
        "middle": 0x04,  # Средняя кнопка мыши (колесико)
        "x1": 0x05,      # Боковая кнопка мыши 1 (назад)
        "x2": 0x06       # Боковая кнопка мыши 2 (вперед)
    }
    # Проверяем, есть ли заданная кнопка в словаре
    if button not in mouse_buttons:
        raise ValueError("Некорректная кнопка! Используйте: 'left', 'right', 'middle', 'x1', 'x2'")
    
    # Проверяем состояние кнопки мыши
    return ctypes.windll.user32.GetAsyncKeyState(mouse_buttons[button]) != 0

while True:
    if is_mouse_clicked("left"):
        print("Левая кнопка мыши нажата!")
    elif is_mouse_clicked("right"):
        print("Правая кнопка мыши нажата!")
    elif is_mouse_clicked("middle"):
        print("Средняя кнопка мыши нажата!")
    elif is_mouse_clicked("x1"):
        print("Боковая кнопка мыши 1 нажата!")
    elif is_mouse_clicked("x2"):
        print("Боковая кнопка мыши 2 нажата!")
    else:
        print("Кнопки мыши не нажаты.")
