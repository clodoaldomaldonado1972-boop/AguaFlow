import flet as ft
import views.styles as st

def montar_tela_configs(page: ft.Page):
    return ft.View(
        route="/configuracoes",
        bgcolor=st.BG_DARK,
        controls=[
            ft.AppBar(
                title=ft.Text("Configurações"),
                bgcolor="surfacevariant",
                leading=ft.IconButton("arrow_back", on_click=lambda _: page.go("/menu"))
            ),
            ft.Column([
                ft.Text("Configurações do Sistema", size=20, weight="bold"),
                ft.ElevatedButton("Voltar", on_click=lambda _: page.go("/menu"))
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        ]
    )