import flet as ft

def montar_menu(page: ft.Page):
    # Versão ultra-segura e limpa
    return ft.View(
        route="/menu",
        # Mude de ft.colors.BLUE_800 para ft.Colors.BLUE_800
        ft.AppBar(
            title=ft.Text("AguaFlow - Menu"), 
            bgcolor=ft.Colors.BLUE_800,  # <-- O "C" precisa ser maiúsculo
            center_title=True
        ),
            ft.Column(
                controls=[
                    ft.Container(height=20),
                    ft.Icon(ft.icons.WATER_DROP, size=50, color="blue"),
                    ft.Text("MENU PRINCIPAL", size=25, weight="bold"),
                    ft.Container(height=20),
                    
                    # BOTÃO QR CODES
                    ft.ElevatedButton(
                        "GERAR QR CODES", 
                        icon=ft.icons.QR_CODE_2,
                        on_click=lambda _: page.go("/qrcodes"), 
                        width=250,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
                    ),

                    # BOTÃO MEDIÇÃO
                    ft.ElevatedButton(
                        "REALIZAR MEDIÇÃO", 
                        icon=ft.icons.SPEED,
                        on_click=lambda _: page.go("/medicao"), 
                        width=250,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
                    ),
                    
                    # BOTÃO RELATÓRIOS (Adicionei para você testar a rota)
                    ft.ElevatedButton(
                        "RELATÓRIOS", 
                        icon=ft.icons.INSERT_CHART,
                        on_click=lambda _: page.go("/relatorios"), 
                        width=250,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
                    ),

                    ft.Container(height=20),
                    
                    # BOTÃO SAIR
                    ft.TextButton(
                        "Sair", 
                        icon=ft.icons.LOGOUT,
                        on_click=lambda _: page.go("/login")
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        ],
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )