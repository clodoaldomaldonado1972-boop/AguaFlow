import flet as ft
from views import styles as st 
# Importação dinâmica da versão para automação total
try:
    from utils.updater import VERSION
except ImportError:
    VERSION = "1.1.0" # Fallback caso o arquivo não seja encontrado

def montar_menu(page: ft.Page):
    user_name = getattr(page, "user_email", "Operador")

    def criar_botao_menu(texto, icone, rota, estilo=st.BTN_MAIN):
        return ft.Container(
            content=ft.ElevatedButton(
                content=ft.Row(
                    [
                        ft.Icon(icone, size=28),
                        ft.Text(texto, size=16, weight="bold"),
                    ],
                    alignment=ft.MainAxisAlignment.START,
                ),
                style=estilo,
                width=320, 
                height=65, 
                on_click=lambda _: page.go(rota),
            ),
            padding=ft.padding.symmetric(horizontal=10),
        )

    return ft.View(
        route="/menu",
        bgcolor=st.BG_DARK,
        controls=[
            ft.AppBar(
                title=ft.Text(f"AguaFlow - {user_name}", size=18),
                bgcolor=ft.colors.SURFACE_VARIANT,
                center_title=True,
            ),
            ft.Column(
                [
                    ft.Container(height=20),
                    ft.Image(src="assets/logo.png", width=150, height=150), # Logo do projeto
                    
                    ft.Column(
                        [
                            # --- BLOCO DE BOTÕES OPERACIONAIS ---
                            criar_botao_menu("REALIZAR MEDIÇÃO", ft.icons.SPEED_ROUNDED, "/medicao"),
                            
                            # Botão de Saúde que contém o Sincronizador para o Supabase
                            # No ficheiro views/menu_principal.py
                            criar_botao_menu("SAÚDE DO SISTEMA", ft.icons.DASHBOARD_CUSTOMIZE, "/dashboard_saude"),
                            
                            criar_botao_menu("GERAR QR CODES", ft.icons.QR_CODE_2_ROUNDED, "/gerar_qrcode"),
                            
                            criar_botao_menu("HISTÓRICO / RELATÓRIO", ft.icons.ASSIGNMENT_OUTLINED, "/relatorios"),
                            
                            # Dashboard interativo com gráficos de evolução
                            criar_botao_menu("DASHBOARD DE CONSUMO", ft.icons.DASHBOARD_ROUNDED, "/dashboard"),
                            
                            criar_botao_menu("CONFIGURAÇÕES", ft.icons.SETTINGS_OUTLINED, "/configuracoes", estilo=st.BTN_SPECIAL),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=12
                    ),
                    
                    ft.Container(height=30),
                    
                    ft.TextButton(
                        "Sair do Sistema", 
                        icon=ft.icons.LOGOUT, 
                        icon_color="red",
                        on_click=lambda _: page.go("/") 
                    ),
                    
                    # Rodapé Dinâmico: Altera automaticamente ao mudar o utils/updater.py
                    ft.Text(f"Versão {VERSION} - Grupo 8 - Univesp", size=10, color=ft.colors.GREY_600),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                scroll=ft.ScrollMode.ADAPTIVE 
            )
        ],
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )