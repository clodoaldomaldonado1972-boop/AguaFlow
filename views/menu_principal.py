import flet as ft
from views import styles as st # Importando estilos para manter padronização

def montar_menu(page: ft.Page):
    # 1. RECUPERAÇÃO DE DADOS DA SESSÃO
    # Tenta pegar o e-mail do usuário logado para personalizar a saudação.
    user_name = getattr(page, "user_email", "Operador")

    # 2. DEFINIÇÃO DA VIEW
    return ft.View(
        route="/menu", 
        bgcolor=st.BG_DARK, # Fundo escuro definido no styles.py
        controls=[
            # O main.py injetará a AppBar com o botão de sincronismo automaticamente.
            # Aqui focamos no conteúdo central da tela.
            ft.Column(
                controls=[
                    ft.Container(height=40), # Espaçamento superior
                    
                    # Ícone e Título Principal
                    ft.Icon(ft.icons.WATER_DROP, size=80, color=ft.colors.BLUE_400),
                    ft.Text("PAINEL DE CONTROLE", size=24, weight="bold", color="white"),
                    ft.Text(f"Bem-vindo, {user_name}", size=16, color=ft.colors.GREY_400),
                    
                    ft.Container(height=30), # Espaçamento entre título e botões
                    
                    # 3. GRADE DE BOTÕES DE NAVEGAÇÃO
                    ft.Column(
                        controls=[
                            # Botão para a tela de Medição (Operacional)
                            ft.ElevatedButton(
                                "REALIZAR MEDIÇÃO", 
                                icon=ft.icons.SPEED, 
                                on_click=lambda _: page.go("/medicao"), 
                                style=st.BTN_MAIN, 
                                width=300, 
                                height=55
                            ),
                            
                            # Botão para Gestão de QR Codes
                            ft.ElevatedButton(
                                "GERAR QR CODES", 
                                icon=ft.icons.QR_CODE_2, 
                                on_click=lambda _: page.go("/qrcodes"), 
                                width=280, 
                                height=50
                            ),

                            # Botão para Visualização de Relatórios (Onde ocorre o envio de e-mail)
                            ft.ElevatedButton(
                                "RELATÓRIOS", 
                                icon=ft.icons.ASSIGNMENT, 
                                on_click=lambda _: page.go("/relatorios"), 
                                width=280, 
                                height=50
                            ),
                            
                            # Botão para Dashboards e Gráficos
                            ft.ElevatedButton(
                                "DASHBOARDS", 
                                icon=ft.icons.DASHBOARD, 
                                on_click=lambda _: page.go("/dashboard"),
                                width=280, 
                                height=50
                            ),
                                             
                            # Botão de Configurações (Destaque em Laranja)
                            ft.ElevatedButton(
                                "CONFIGURAÇÕES", 
                                icon=ft.icons.SETTINGS, 
                                on_click=lambda _: page.go("/configuracoes"), 
                                style=st.BTN_SPECIAL, 
                                width=300, 
                                height=55
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=15
                    ),
                    
                    ft.Container(height=40),
                    
                    # 4. BOTÃO DE LOGOUT
                    ft.TextButton(
                        "Sair do Sistema", 
                        icon=ft.icons.LOGOUT, 
                        icon_color="red",
                        on_click=lambda _: page.go("/") # Volta para a tela de login
                    )
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        ],
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )