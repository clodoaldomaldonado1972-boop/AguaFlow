import flet as ft
import views.styles as st
from utils.updater import AppUpdater


def montar_tela_sobre(page: ft.Page):
    # Você pode adicionar validação de sessão aqui se esta tela exigir autenticação
    # from utils.auth_utils import validar_sessao
    # auth_check = validar_sessao(page, "/sobre")
    # if auth_check:
    #     return auth_check

    return ft.View(
        route="/sobre",
        bgcolor=st.BG_DARK,
        controls=[
            ft.AppBar(
                title=ft.Text("Sobre o AguaFlow"),
                bgcolor=st.PRIMARY_BLUE,
                leading=ft.IconButton(
                    "arrow_back", on_click=lambda _: page.go("/configuracoes"))
            ),
            ft.Column(
                [
                    ft.Container(height=20),
                    ft.Icon(ft.icons.INFO_OUTLINE, size=64,
                            color=st.PRIMARY_BLUE),
                    ft.Text("AguaFlow", size=24,
                            weight="bold", color=st.WHITE),
                    ft.Text(AppUpdater.get_footer(),
                            size=14, color=st.GREY_TEXT),
                    ft.Container(height=20),
                    ft.Text("Licença de Uso", size=18,
                            weight="bold", color=st.WHITE),
                    ft.Text(
                        "Este aplicativo é distribuído sob a licença MIT. "
                        "Você pode encontrar os termos completos da licença no repositório do projeto "
                        "ou na documentação oficial.",
                        size=12,
                        color=st.GREY_TEXT,
                        text_align=ft.TextAlign.CENTER
                    ),
                    ft.Container(height=20),
                    ft.TextButton("Ver Licença Completa (Online)", on_click=lambda e: page.launch_url(
                        "https://opensource.org/licenses/MIT")),
                    ft.Container(expand=True),
                    ft.TextButton("Voltar às Configurações",
                                  on_click=lambda _: page.go("/configuracoes")),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True,
                scroll=ft.ScrollMode.ADAPTIVE
            )
        ]
    )
