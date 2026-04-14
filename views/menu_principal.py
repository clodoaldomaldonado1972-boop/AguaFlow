import flet as ft
from views import styles as st # Importando estilos para manter padronização

def montar_menu(page: ft.Page):
    # Recupera o nome ou email da sessão
    user_name = getattr(page, "user_email", "Operador")

    return ft.View(
        route="/menu", 
        bgcolor=st.BG_DARK, # Garante o fundo escuro padronizado
        controls=[
            ft.AppBar(
                title=ft.Text(f"AguaFlow - Olá, {user_name}", weight="bold"),
                bgcolor=ft.colors.BLUE_900,
                color="white",
                center_title=True,
            ),
            ft.Column(
                controls=[
                    ft.Container(height=40),
                    ft.Icon(ft.icons.WATER_DROP, size=80, color=ft.colors.BLUE_400),
                    ft.Text("PAINEL DE CONTROLE", size=28, weight="bold", color="white"),
                    ft.Container(height=20),
                    
                    ft.Column(
                        controls=[
                            ft.ElevatedButton(
                                "REALIZAR MEDIÇÃO", 
                                icon=ft.icons.SPEED, 
                                on_click=lambda _: page.go("/medicao"), 
                                style=st.BTN_MAIN, # Usa o estilo azul do styles.py
                                width=300, 
                                height=55
                            ),
                                             
                            ft.ElevatedButton(
                                "GERAR QR CODES", 
                                icon=ft.icons.QR_CODE_2, 
                                on_click=lambda _: page.go("/qrcodes"), 
                                style=st.BTN_MAIN,
                                width=300, 
                                height=55
                            ),
                                             
                            ft.ElevatedButton(
                                "RELATÓRIOS", 
                                icon=ft.icons.INSERT_CHART, 
                                on_click=lambda _: page.go("/relatorios"), 
                                style=st.BTN_MAIN,
                                width=300, 
                                height=55
                            ),
                            
                            ft.ElevatedButton(
                                "DASHBOARD DE CONSUMO", 
                                icon=ft.icons.DASHBOARD, 
                                on_click=lambda _: page.go("/dashboard"), # Deve ser igual ao main.py
                                width=280, 
                                height=50
                            ),
                                             
                            # BOTÃO DE CONFIGURAÇÕES
                            ft.ElevatedButton(
                                "CONFIGURAÇÕES", 
                                icon=ft.icons.SETTINGS, 
                                on_click=lambda _: page.go("/configuracoes"), 
                                style=st.BTN_SPECIAL, # Laranja para destacar
                                width=300, 
                                height=55
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=15
                    ),
                    ft.Container(height=40),
                    ft.TextButton(
                        "Sair do Sistema", 
                        icon=ft.icons.LOGOUT, 
                        icon_color="red",
                        on_click=lambda _: page.go("/")
                    )
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        ],
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )