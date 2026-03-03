import flet as ft


def main(page: ft.Page):
    page.add(ft.Text("Se você está lendo isso, o Flet está funcionando!"))


ft.app(target=main)
