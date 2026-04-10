import flet as ft


def montar_menu(page: ft.Page):
    # Versão ultra-segura para teste após limpeza
    return ft.View(
        route="/menu",
        controls=[
            ft.AppBar(title=ft.Text("AguaFlow - Menu"), bgcolor="blue"),
            ft.Column(
                controls=[
                    ft.Container(height=20),
                    ft.Text("MENU PRINCIPAL", size=30, weight="bold"),
                    ft.ElevatedButton(
                        "GERAR QR CODES", on_click=lambda _: page.go("/qrcodes"), width=250),
                    ft.ElevatedButton(
                        "REALIZAR MEDIÇÃO", on_click=lambda _: page.go("/medicao"), width=250),
                    ft.TextButton(
                        "Sair", on_click=lambda _: page.go("/login")),
                ],
                horizontal_alignment="center",
            )
        ],
        vertical_alignment="center",
        horizontal_alignment="center",
    )
