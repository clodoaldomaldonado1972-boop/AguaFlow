import flet as ft
import views.styles as st  # Importar estilos para cores
from utils.auth_utils import validar_sessao


def montar_menu(page: ft.Page):
    """
    Monta a tela do menu principal, atuando como hub central para a navegação.
    """
    try:
        # Proteção de Rota
        auth_check = validar_sessao(page, "/menu")
        if auth_check:
            return auth_check

        # Recupera os dados do usuário de forma segura (.get)
        user_data = getattr(page, "user_data", {}) or {}
        user_email = user_data.get("email", "Usuário Desconhecido")
        user_name = user_data.get("nome") or user_email.split('@')[0].capitalize()

        # Verifica se o usuário está autenticado em modo offline
        is_offline = user_data.get("offline", False)
        user_role = user_data.get("role", "user")

        app_bar_actions = []
        if is_offline:
            app_bar_actions.append(
                ft.Container(
                    # Usando string para evitar AttributeError no Android
                    content=ft.Icon(ft.Icons.CLOUD_OFF, color="orange"),
                    tooltip="Modo Offline: As medições serão salvas apenas no dispositivo",
                    padding=ft.Padding.only(right=20)
                )
            )

        tema_icon = ft.Icons.LIGHT_MODE if page.theme_mode == ft.ThemeMode.DARK else ft.Icons.DARK_MODE
        tema_tooltip = "Mudar para tema claro" if page.theme_mode == ft.ThemeMode.DARK else "Mudar para tema escuro"

        async def alternar_tema(e):
            await page.toggle_tema()
            page.go("/menu")

        app_bar_actions.append(
            ft.IconButton(icon=tema_icon, tooltip=tema_tooltip, on_click=alternar_tema)
        )

        def confirmar_logout(e):
            async def realizar_logout(e):
                page.pop_dialog()
                if hasattr(page, "limpar_sessao"):
                    await page.limpar_sessao()
                page.user_data = {}
                page.show_dialog(ft.SnackBar(
                    content=ft.Text("Logout realizado com sucesso!"),
                    bgcolor=st.SUCCESS_GREEN
                ))
                page.go("/")
                page.update()

            def fechar_dialogo(e):
                page.pop_dialog()

            page.show_dialog(ft.AlertDialog(
                title=ft.Text("Confirmar Saída"),
                content=ft.Text("Deseja realmente sair do sistema?"),
                actions=[
                    ft.TextButton("Sim", on_click=realizar_logout),
                    ft.TextButton("Não", on_click=fechar_dialogo),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            ))

        # Adiciona o botão de Logout (Sair) na AppBar usando ícone universal
        app_bar_actions.append(
            ft.IconButton(
                icon=ft.Icons.POWER_SETTINGS_NEW,
                tooltip="Sair do Sistema",
                on_click=confirmar_logout
            )
        )

        return ft.View(
            route="/menu",
            bgcolor=st.get_bgcolor(page),
            appbar=ft.AppBar(
                title=ft.Column([
                    ft.Text(f"Olá, {user_name}!", size=16, weight="bold"),
                    ft.Text(user_email, size=12, color="white70")
                ],
                    horizontal_alignment=ft.CrossAxisAlignment.START,
                    spacing=2
                ),
                bgcolor=st.PRIMARY_BLUE,
                actions=app_bar_actions
            ),
            controls=[
                ft.Column(
                    [
                        ft.Column(
                            [
                                # Funcionalidades Comuns
                                ft.ElevatedButton(
                                    "Medição",
                                    icon="speed",
                                    on_click=lambda _: page.go("/medicao"),
                                    width=250, height=50
                                ),
                                ft.ElevatedButton("Dashboard", icon="dashboard", on_click=lambda _: page.go(
                                    "/dashboard"), width=250, height=50),
                                ft.ElevatedButton("Scanner", icon="qr_code_scanner", on_click=lambda _: page.go(
                                    "/scanner"), width=250, height=50),
                                ft.ElevatedButton("Sincronizar Dados", icon="cloud_upload", on_click=lambda _: page.go(
                                    "/sincronizar"), width=250, height=50),

                                # Funcionalidades Administrativas
                                ft.Column([
                                    ft.ElevatedButton("Dashboard de Saúde", icon="health_and_safety", on_click=lambda _: page.go(
                                        "/dashboard_saude"), width=250, height=50),
                                    ft.ElevatedButton("Gerenciar Usuários", icon="people_alt", on_click=lambda _: page.go(
                                        "/usuarios"), width=250, height=50),
                                    ft.ElevatedButton("Relatórios", icon="summarize", on_click=lambda _: page.go(
                                        "/relatorios"), width=250, height=50),
                                ], visible=user_role == "admin", horizontal_alignment="center"),

                                ft.ElevatedButton("Configurações", icon="settings", on_click=lambda _: page.go(
                                    "/configuracoes"), width=250, height=50),
                                ft.Row([
                                    ft.TextButton("Histórico", icon="history", on_click=lambda _: page.go("/historico")),
                                    ft.TextButton("Ajuda", icon="help_outline", on_click=lambda _: page.go("/ajuda")),
                                    ft.TextButton("Sobre", icon="info_outline", on_click=lambda _: page.go("/sobre")),
                                ], alignment=ft.MainAxisAlignment.CENTER, wrap=True),
                            ],
                            horizontal_alignment="center", spacing=10,
                            scroll=ft.ScrollMode.AUTO,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    horizontal_alignment="center",
                    expand=True,
                ),
            ],
            vertical_alignment=ft.MainAxisAlignment.START,
            horizontal_alignment="center",
        )

    except Exception as e:
        return ft.View(
            route="/menu",
            controls=[ft.Text(
                f"Erro ao carregar menu principal: {str(e)}", color="red")]
        )
