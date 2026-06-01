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
        appbar=ft.AppBar(
            title=ft.Text("Sobre o AguaFlow"),
            bgcolor=st.PRIMARY_BLUE,
            leading=ft.IconButton(
                icon=ft.Icons.ARROW_BACK, on_click=lambda _: page.go("/menu"))
        ),
        controls=[
            ft.Column(
                [
                    ft.Container(height=20),
                    st.logo_aguaflow_com_texto(size=80, text_size=24),
                    ft.Text(AppUpdater.get_footer(),
                            size=14, color=st.GREY_TEXT),
                    ft.Container(height=20),
                    ft.Text("Licença de Uso", size=18,
                            weight="bold", color=st.WHITE),
                    ft.Text(
                        "Este aplicativo é distribuído gratuitamente sob a Licença MIT. "
                        "É permitido o uso, cópia e modificação do software, desde que mantidos "
                        "os créditos dos autores originais, aplicando-se o princípio de isenção de responsabilidade.",
                        size=12,
                        color=st.GREY_TEXT,
                        text_align=ft.TextAlign.CENTER
                    ),
                    ft.Container(height=20),
                    ft.TextButton(
                        "Ver Licença Completa (Online)",
                        url="https://github.com/clodoaldomaldonado1972-boop/AguaFlow/blob/main/LICENSE",
                    ),
                    ft.Container(expand=True),
                    ft.TextButton("Voltar ao Menu",
                                  on_click=lambda _: page.go("/menu")),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True,
                scroll=ft.ScrollMode.AUTO
            )
        ]
    )
