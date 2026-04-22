import flet as ft
from views import styles as st 

# Importação dinâmica da versão
try:
    from utils.updater import VERSION
except ImportError:
    VERSION = "1.1.0"

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
                    # LOGO ✅
                    ft.Image(
                        src="logo.jpeg",
                        width=150,
                        height=150,
                        fit=ft.ImageFit.CONTAIN,
                    ),
                    ft.Text("Menu Principal", size=20, weight="bold", color="white"),
                    ft.Container(height=20),
                    
                    # Coluna Interna para os Botões
                    ft.Column(
                        [
                            criar_botao_menu("REALIZAR MEDIÇÃO", ft.icons.SPEED_ROUNDED, "/medicao"),
                            criar_botao_menu("SAÚDE DO SISTEMA", ft.icons.HEALTH_AND_SAFETY, "/saude"),
                            criar_botao_menu("GERAR QR CODES", ft.icons.QR_CODE_2_ROUNDED, "/qrcodes"),
                            criar_botao_menu("HISTÓRICO / RELATÓRIO", ft.icons.ASSIGNMENT_OUTLINED, "/relatorios"),
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
                    ft.Text(f"Versão {VERSION} - Grupo 8 - Univesp", size=10, color=ft.colors.GREY_600),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                scroll=ft.ScrollMode.ADAPTIVE 
            )
        ],
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )