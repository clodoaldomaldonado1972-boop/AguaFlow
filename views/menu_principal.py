import flet as ft


def montar_menu(page: ft.Page, *args, **kwargs):
    # Cores fixas para evitar erros de importação
    return ft.View(
        route="/menu",
        controls=[
            ft.AppBar(title=ft.Text("AguaFlow - Menu"), bgcolor="#1A1C1E"),
            ft.Column([
                ft.Container(height=50),
                ft.Icon("water_drop", size=80, color="blue"),
                ft.ElevatedButton(
                    "GERAR QR CODES", on_click=lambda _: page.go("/qrcodes"), width=300),
                ft.ElevatedButton(
                    "SAIR", on_click=lambda _: page.go("/login"), width=300),
            ], horizontal_alignment="center")
        ],
        bgcolor="#121417"
    )

    return ft.View(
        route="/menu",
        controls=[
            ft.Container(
                content=coluna,
                alignment=ft.Alignment(0, 0),  # Coordenada universal de centro
                expand=True
            )
        ],
        bgcolor="#121417"
    )
