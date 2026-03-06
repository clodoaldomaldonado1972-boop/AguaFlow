import flet as ft
import auth
import reports
import utils
import database as db
import medicao
import os


def main(page: ft.Page):
    # --- CONFIGURAÇÃO MESTRE ---
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#1A1C1E"
    page.window_bgcolor = "#1A1C1E"
    page.window_width = 450
    page.window_height = 800
    page.padding = 0

    db.init_db()

    # Este é o "Palco" onde os módulos vão aparecer
    # Ele NUNCA é removido, apenas o que tem dentro dele muda
    palco = ft.Container(expand=True, bgcolor="#1A1C1E")

    def navegar_menu(perfil):
        # Criamos a coluna do menu
        coluna = ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15)

        coluna.controls.extend([
            ft.Text(f"Perfil: {perfil.upper()}",
                    color="blue", weight="bold", size=20),
            ft.Divider(color="white10"),
            ft.FilledButton("INICIAR LEITURA", width=280,
                            on_click=lambda _: carregar_modulo(medicao.montar_tela(page, lambda: navegar_menu(perfil)))),
            ft.OutlinedButton("AJUDA / GUIA", width=280,
                              on_click=lambda _: carregar_modulo(utils.montar_tela_ajuda(lambda _: navegar_menu(perfil))))
        ])

        # Se for admin, adiciona os botões extras
        if perfil == "admin":
            coluna.controls.insert(3, ft.FilledButton(
                "RELATÓRIOS MENSAL", width=280))  # Exemplo

        coluna.controls.append(ft.TextButton(
            "SAIR", on_click=lambda _: iniciar_app()))

        carregar_modulo(coluna)

    def carregar_modulo(conteudo):
        # Limpa o conteúdo interno do palco
        # Usamos ft.Alignment(0, -1) que significa Centro (0) e Topo (-1)
        palco.content = ft.Container(
            content=conteudo,
            padding=20,
            expand=True,
            bgcolor="#1A1C1E",
            alignment=ft.Alignment(0, -1)
        )
        page.update()

    def iniciar_app():
        # Carrega o login dentro do palco
        carregar_modulo(auth.criar_tela_login(page, navegar_menu))

    # Adiciona o palco fixo na página
    page.add(palco)
    iniciar_app()


if __name__ == "__main__":
    os.environ["FLET_RENDERER"] = "skia"
    # Se quiser testar no navegador, use: ft.run(main, view=ft.AppView.WEB_BROWSER)
    ft.run(main)
