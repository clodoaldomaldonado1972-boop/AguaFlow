import flet as ft


def main(page: ft.Page):
    page.add(ft.Text("O Flet está funcionando!", size=30))
    page.add(ft.ElevatedButton("Clique aqui"))


ft.app(target=main)
