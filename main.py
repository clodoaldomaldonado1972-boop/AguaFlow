import flet as ft
import os
import auth
import reports
import utils
import medicao
import database as db


def main(page: ft.Page):
    # --- 1. CONFIGURAÇÃO DE INTERFACE ---
    page.title = "ÁguaFlow"
    page.window_bgcolor = "#1A1C1E"
    page.bgcolor = "#1A1C1E"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 450
    page.window_height = 800
    page.window_resizable = False
    page.padding = 0
    page.spacing = 0

    # Inicializa o banco
    db.init_db()

    # --- 2. PALCO PRINCIPAL ---
    palco = ft.Container(expand=True, bgcolor="#1A1C1E")

    # --- 3. FUNÇÕES DE NAVEGAÇÃO ---
    def carregar_modulo(conteudo):
        palco.content = ft.Container(
            content=conteudo,
            padding=20,
            expand=True,
            bgcolor="#1A1C1E",
            alignment=ft.Alignment(0, -1)
        )
        page.update()

    def navegar_menu(perfil):
        # Criamos a lista de botões organizada
        botoes = [
            ft.Text(f"PERFIL: {perfil.upper()}",
                    color="blue", weight="bold", size=20),
            ft.Divider(color="white10"),

            # BOTÃO INICIAR LEITURA (Configurado corretamente)
            ft.FilledButton(
                "INICIAR LEITURA",
                width=280,
                on_click=lambda _: carregar_modulo(
                    medicao.montar_tela(page, lambda: navegar_menu(perfil)))
            ),

            ft.FilledButton(
                "RELATÓRIOS MENSAL",
                width=280,
                on_click=lambda _: carregar_modulo(
                    reports.montar_tela_relatorios(page, lambda: navegar_menu(perfil)))
            ),

            ft.OutlinedButton(
                "AJUDA / SUPORTE",
                width=280,
                on_click=lambda _: carregar_modulo(
                    utils.montar_tela_ajuda(lambda: navegar_menu(perfil)))
            ),

            ft.Container(height=20),
            ft.TextButton("SAIR / LOGOUT", on_click=lambda _: iniciar_app())
        ]

        # Carrega a coluna de botões no palco
        carregar_modulo(ft.Column(
            botoes, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15))

    def iniciar_app():
        carregar_modulo(auth.criar_tela_login(page, navegar_menu))

    # --- 4. EXECUÇÃO ---
    page.add(palco)
    iniciar_app()
    page.update()


if __name__ == "__main__":
    os.environ["FLET_RENDERER"] = "skia"
    ft.run(main)
