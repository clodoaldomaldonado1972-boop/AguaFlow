import flet as ft
import views.styles as st

def montar_tela_qrcodes(page: ft.Page, on_back):
    return ft.View(
        route="/qrcodes",
        bgcolor=st.BG_DARK,
        controls=[
            ft.AppBar(
                title=ft.Text("Gerenciador de QR Codes"),
                bgcolor="surfacevariant", # Usando string para evitar erro de atributo
                leading=ft.IconButton("arrow_back", on_click=lambda _: page.go("/menu"))
            ),
            ft.Column([
                ft.Container(height=20),
                ft.Icon("qr_code_2", size=64, color="blue"),
                ft.Text("Módulo de QR Codes", size=20, weight="bold"),
                ft.Text("Em desenvolvimento para o Edifício Vivere", size=14, color="grey"),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        ]
    )