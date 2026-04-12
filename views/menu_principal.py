import flet as ft

def montar_menu(page: ft.Page):
    """
    Constrói a visualização do Menu Principal do AguaFlow.
    Utiliza navegação via page.go() para compatibilidade com Flet 0.80+.
    """
    return ft.View(
        route="/menu",
        controls=[
            # Barra superior personalizada
            ft.AppBar(
                title=ft.Text("AguaFlow - Vivere Prudente", weight="bold"),
                bgcolor="blue800",
                color="white",
                center_title=True,
            ),
            
            # Conteúdo centralizado
            ft.Column(
                controls=[
                    ft.Container(height=30), # Espaçamento superior
                
                    ft.Icon("water_drop_outlined", size=80, color="blue"),
                    
                    ft.Text(
                        "MENU PRINCIPAL", 
                        size=28, 
                        weight="bold", 
                        color=ft.colors.BLUE_GREY_700
                    ),
                    
                    ft.Container(height=20), # Espaçamento
                    
                    # Grupo de botões de ação
                    ft.Column(
                        controls=[
                            # Botão para Medição (O coração do app)
                            ft.ElevatedButton(
                                "REALIZAR MEDIÇÃO", 
                                icon=ft.icons.SPEED,
                                on_click=lambda _: page.go("/medicao"), 
                                width=280,
                                height=50,
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=10)
                                )
                            ),
                            
                            # Botão para QR Codes
                            ft.ElevatedButton(
                                "GERAR QR CODES", 
                                icon=ft.icons.QR_CODE_2,
                                on_click=lambda _: page.go("/qrcodes"), 
                                width=280,
                                height=50,
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=10)
                                )
                            ),
                            
                            # Botão para Relatórios
                            ft.ElevatedButton(
                                "RELATÓRIOS", 
                                icon=ft.icons.INSERT_CHART,
                                on_click=lambda _: page.go("/relatorios"), 
                                width=280,
                                height=50,
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=10)
                                )
                            ),

                            # Botão para Configurações
                            ft.ElevatedButton(
                                "CONFIGURAÇÕES", 
                                icon=ft.icons.SETTINGS,
                                on_click=lambda _: page.go("/configuracoes"), 
                                width=280,
                                height=50,
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=10)
                                )
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=15
                    ),
                    
                    ft.Container(height=40), # Espaçamento antes do sair
                    
                    # Botão Sair (Volta para o Login)
                    ft.TextButton(
                        "Sair do Sistema", 
                        icon=ft.icons.LOGOUT,
                        icon_color="red",
                        on_click=lambda _: page.go("/login")
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        ],
        # Garante que tudo fique centralizado na tela do dispositivo
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )