import flet as ft

def montar_menu(page: ft.Page):
    user_name = getattr(page, "user_email", "Operador")

    return ft.View(
        route="/main_menu",
        controls=[
            ft.AppBar(
                title=ft.Text(f"AguaFlow - Olá, {user_name}", weight="bold"),
                bgcolor="blue800", color="white", center_title=True,
            ),
            ft.Column(
                controls=[
                    ft.Container(height=20),
                    ft.Icon("water_drop", size=80, color="blue"),
                    ft.Text("MENU PRINCIPAL", size=24, weight="bold"),
                    
                    ft.Column(
                        controls=[
                            ft.ElevatedButton("REALIZAR MEDIÇÃO", icon=ft.icons.SPEED, 
                                             on_click=lambda _: page.go("/medicao"), width=280, height=50),
                            ft.ElevatedButton("GERAR QR CODES", icon=ft.icons.QR_CODE_2, 
                                             on_click=lambda _: page.go("/qrcodes"), width=280, height=50),
                            ft.ElevatedButton("RELATÓRIOS", icon=ft.icons.INSERT_CHART, 
                                             on_click=lambda _: page.go("/relatorios"), width=280, height=50),
                            # Novo Botão de Dashboard
                            ft.ElevatedButton("DASHBOARD DE CONSUMO", icon=ft.icons.DASHBOARD, 
                                             on_click=lambda _: page.go("/dashboard"), width=280, height=50),
                            ft.ElevatedButton("CONFIGURAÇÕES", icon=ft.icons.SETTINGS, 
                                             on_click=lambda _: page.go("/configuracoes"), width=280, height=50),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15
                    ),
                    ft.TextButton("Sair do Sistema", icon=ft.icons.LOGOUT, icon_color="red",
                                 on_click=lambda _: page.go("/login")),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        ],
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )