import flet as ft
from ui import build_ui

def app(page: ft.Page):
    build_ui(page)

if __name__ == '__main__':
    ft.app(target=app)
