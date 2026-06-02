import flet as ft
import views.styles as st
from utils.auth_utils import validar_sessao

# Gradientes verticais — paleta AguaFlow brand (guia ov9ngi)
_GRAD_BLUE   = ["#5580FF", "#1235D8"]   # Agua: azul elétrico claro → escuro
_GRAD_ORANGE = ["#FFB870", "#E06000"]   # Flow: laranja quente claro → escuro
_GRAD_TEAL   = ["#20C8D8", "#006878"]   # teal para Dashboard de Saúde


def _btn_menu(label, icon, grad_colors, on_click):
    return ft.Container(
        content=ft.Row(
            [
                ft.Container(
                    content=ft.Icon(icon, color="white", size=22),
                    width=36,
                    height=36,
                    border_radius=8,
                    bgcolor=ft.Colors.with_opacity(0.18, "white"),
                    alignment=ft.alignment.Alignment(0, 0),
                ),
                ft.Text(label, color="white", size=15, weight=ft.FontWeight.BOLD),
            ],
            spacing=14,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        gradient=ft.LinearGradient(
            begin=ft.alignment.Alignment(0, -1),
            end=ft.alignment.Alignment(0, 1),
            colors=grad_colors,
        ),
        border_radius=12,
        padding=ft.padding.symmetric(horizontal=16, vertical=13),
        on_click=on_click,
        ink=True,
        shadow=ft.BoxShadow(
            blur_radius=8,
            spread_radius=0,
            color=ft.Colors.with_opacity(0.30, "black"),
            offset=ft.Offset(0, 4),
        ),
    )


def montar_menu(page: ft.Page):
    try:
        auth_check = validar_sessao(page, "/menu")
        if auth_check:
            return auth_check

        user_data = getattr(page, "user_data", {}) or {}
        user_email = user_data.get("email", "Usuário Desconhecido")
        user_name = user_data.get("nome") or user_email.split("@")[0].capitalize()
        is_offline = user_data.get("offline", False)
        user_role  = user_data.get("role", "user")
        is_dark    = page.theme_mode == ft.ThemeMode.DARK

        async def alternar_tema(e):
            await page.toggle_tema()

        def confirmar_logout(e):
            async def realizar_logout(e):
                page.pop_dialog()
                if hasattr(page, "limpar_sessao"):
                    await page.limpar_sessao()
                page.user_data = {}
                page.show_dialog(ft.SnackBar(
                    content=ft.Text("Logout realizado com sucesso!"),
                    bgcolor=st.SUCCESS_GREEN,
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

        # Cores adaptadas ao tema — paleta AguaFlow brand
        name_color    = "white"        if is_dark else st.AGUA_BLUE
        sub_color     = "#BDBDBD"      if is_dark else "#444444"
        icon_color    = "white"        if is_dark else st.AGUA_BLUE
        divider_color = "#1E2A40"      if is_dark else "#D0DCF8"

        # ── Cabeçalho ──────────────────────────────────────────────
        header = ft.Container(
            content=ft.Row(
                [
                    ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Text(
                                        f"Olá {user_name}",
                                        size=17,
                                        weight=ft.FontWeight.BOLD,
                                        color=name_color,
                                        expand=True,
                                        overflow=ft.TextOverflow.ELLIPSIS,
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.POWER_SETTINGS_NEW,
                                        icon_color="#FF6600",
                                        icon_size=19,
                                        tooltip="Sair do Sistema",
                                        on_click=confirmar_logout,
                                        padding=ft.padding.all(0),
                                    ),
                                ],
                                spacing=2,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            ft.Text(user_email, size=12, color=sub_color),
                        ],
                        spacing=1,
                        expand=True,
                    ),
                    ft.Row(
                        [
                            ft.Container(
                                content=ft.Icon(ft.Icons.CLOUD_OFF, color="#FF6600", size=20),
                                tooltip="Modo Offline",
                                visible=is_offline,
                            ),
                            ft.IconButton(
                                icon=ft.Icons.LIGHT_MODE if is_dark else ft.Icons.DARK_MODE,
                                icon_color=icon_color,
                                icon_size=20,
                                tooltip="Alternar tema",
                                on_click=alternar_tema,
                            ),
                        ],
                        spacing=0,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.symmetric(horizontal=20, vertical=12),
        )

        # ── Logo centralizado ───────────────────────────────────────
        logo_section = ft.Container(
            content=st.logo_aguaflow_com_texto(size=100, text_size=30),
            alignment=ft.alignment.Alignment(0, 0),
            padding=ft.padding.symmetric(vertical=14),
        )

        # ── Botões admin (apenas role=admin) ───────────────────────
        admin_buttons = (
            [
                _btn_menu("Dashboard de Saúde", ft.Icons.HEALTH_AND_SAFETY, _GRAD_TEAL,   lambda _: page.go("/dashboard_saude")),
                _btn_menu("Gerenciar Usuários",  ft.Icons.PEOPLE_ALT,        _GRAD_BLUE,   lambda _: page.go("/usuarios")),
                _btn_menu("Relatórios",          ft.Icons.SUMMARIZE,          _GRAD_BLUE,   lambda _: page.go("/relatorios")),
            ]
            if user_role == "admin"
            else []
        )

        botoes = ft.Column(
            [
                _btn_menu("Medição",           ft.Icons.MONITOR_HEART,   _GRAD_BLUE,   lambda _: page.go("/medicao")),
                _btn_menu("Scanner",           ft.Icons.QR_CODE_SCANNER, _GRAD_ORANGE, lambda _: page.go("/scanner")),
                _btn_menu("Dashboard",         ft.Icons.BAR_CHART,       _GRAD_BLUE,   lambda _: page.go("/dashboard")),
                _btn_menu("Sincronizar Dados", ft.Icons.CLOUD_SYNC,      _GRAD_ORANGE, lambda _: page.go("/sincronizar")),
                *admin_buttons,
                _btn_menu("Configurações",     ft.Icons.SETTINGS,        _GRAD_ORANGE, lambda _: page.go("/configuracoes")),
            ],
            spacing=10,
        )

        # ── Footer ─────────────────────────────────────────────────
        def _footer_btn(label, route):
            return ft.TextButton(
                content=ft.Row(
                    [
                        ft.Icon(ft.Icons.PLAY_CIRCLE, color="#FF6600", size=15),
                        ft.Text(label, size=13, color=sub_color),
                    ],
                    spacing=4,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                on_click=lambda _: page.go(route),
            )

        footer = ft.Container(
            content=ft.Row(
                [
                    _footer_btn("Histórico", "/historico"),
                    _footer_btn("Ajuda",     "/ajuda"),
                    _footer_btn("Sobre",     "/sobre"),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            padding=ft.padding.symmetric(vertical=8),
        )

        corpo = ft.Container(
            content=ft.Column(
                [
                    logo_section,
                    botoes,
                    ft.Container(height=8),
                    ft.Divider(height=1, color=divider_color),
                    footer,
                    ft.Container(height=64),  # safe area — cobre nav bar do Android
                ],
                spacing=0,
                scroll=ft.ScrollMode.AUTO,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            ),
            padding=ft.padding.symmetric(horizontal=20),
            expand=True,
        )

        return ft.View(
            route="/menu",
            bgcolor=st.get_bgcolor(page),
            padding=0,
            controls=[
                ft.Column(
                    [
                        header,
                        ft.Divider(height=1, color=divider_color),
                        corpo,
                    ],
                    spacing=0,
                    expand=True,
                )
            ],
        )

    except Exception as e:
        return ft.View(
            route="/menu",
            controls=[
                ft.Text(f"Erro ao carregar menu principal: {str(e)}", color="red")
            ],
        )
