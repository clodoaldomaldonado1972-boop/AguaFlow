import flet as ft
import views.styles as st  # Importar estilos para cores
from utils.auth_utils import validar_sessao


def montar_menu(page: ft.Page):
    """
    Monta a tela do menu principal, atuando como hub central para a navegação.
    """
    # Proteção de Rota
    auth_check = validar_sessao(page, "/menu")
    if auth_check:
        return auth_check

    # Recupera os dados do usuário
    user_email = page.user_data.get(
        "email", "Usuário Desconhecido") if page.user_data else "Usuário Desconhecido"
    user_name = page.user_data.get("nome", user_email.split(
        '@')[0].capitalize()) if page.user_data else user_email.split('@')[0].capitalize()

    # Verifica se o usuário está autenticado em modo offline
    is_offline = page.user_data.get(
        "offline", False) if page.user_data else False
    user_role = page.user_data.get(
        "role", "user") if page.user_data else "user"

    app_bar_actions = []
    if is_offline:
        app_bar_actions.append(
            ft.Container(
                content=ft.Icon(ft.icons.CLOUD_OFF, color="orange"),
                tooltip="Modo Offline: As medições serão salvas apenas no dispositivo",
                padding=ft.padding.only(right=20)
            )
        )

    def confirmar_logout(e):
        def realizar_logout(e):
            page.dialog.open = False
            # Limpa os dados da sessão por segurança
            page.user_data = None

            # Exibe mensagem de confirmação
            page.snack_bar = ft.SnackBar(
                content=ft.Text("Logout realizado com sucesso!"),
                bgcolor=st.SUCCESS_GREEN
            )
            page.snack_bar.open = True

            page.go("/")
            page.update()

        def fechar_dialogo(e):
            page.dialog.open = False
            page.update()

        page.dialog = ft.AlertDialog(
            title=ft.Text("Confirmar Saída"),
            content=ft.Text("Deseja realmente sair do sistema?"),
            actions=[
                ft.TextButton("Sim", on_click=realizar_logout),
                ft.TextButton("Não", on_click=fechar_dialogo),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.dialog.open = True
        page.update()

    # Adiciona o botão de Logout (Sair) na AppBar
    app_bar_actions.append(
        ft.IconButton(
            icon=ft.icons.LOGOUT_ROUNDED,
            tooltip="Sair do Sistema",
            on_click=confirmar_logout
        )
    )

    return ft.View(
        "/menu",
        [
            ft.AppBar(  # ft.Text("Menu Principal")
                title=ft.Column([
                    ft.Text(f"Olá, {user_name}!", size=16, weight="bold"),
                    ft.Text(user_email, size=12, color=ft.colors.WHITE70)
                ],
                    horizontal_alignment=ft.CrossAxisAlignment.START,
                    spacing=2
                ),
                bgcolor=st.PRIMARY_BLUE,
                actions=app_bar_actions
            ),
            ft.Column(
                [
                    # Funcionalidades Comuns
                    ft.ElevatedButton(
                        "Medição",
                        icon="speed",
                        on_click=lambda _: page.go("/medicao"),
                        width=250,
                        height=50
                    ),
                    ft.ElevatedButton(
                        "Scanner",
                        icon="qr_code_scanner",
                        on_click=lambda _: page.go("/scanner"),
                        width=250,
                        height=50
                    ),
                    ft.ElevatedButton(
                        "Sincronizar Dados",
                        icon="cloud_upload",
                        on_click=lambda _: page.go("/sincronizar"),
                        width=250,
                        height=50
                    ),

                    # Funcionalidades Administrativas (Visíveis apenas para Admin)
                    ft.Column([
                        ft.ElevatedButton(
                            "Dashboard de Saúde",
                            icon="health_and_safety",
                            on_click=lambda _: page.go("/dashboard_saude"),
                            width=250,
                            height=50
                        ),
                        ft.ElevatedButton(
                            "Gerenciar Usuários",
                            icon="people_alt",
                            on_click=lambda _: page.go("/usuarios"),
                            width=250,
                            height=50
                        ),
                        ft.ElevatedButton(
                            "Relatórios",
                            icon="summarize",
                            on_click=lambda _: page.go("/relatorios"),
                            width=250,
                            height=50
                        ),
                    ], visible=user_role == "admin", horizontal_alignment="center"),

                    ft.ElevatedButton(
                        "Configurações",
                        icon="settings",
                        on_click=lambda _: page.go("/configuracoes"),
                        width=250,
                        height=50
                    ),
                ],
                alignment="center",
                horizontal_alignment="center",
                expand=True
            ),
        ],
        vertical_alignment="center",
        horizontal_alignment="center",
    )
