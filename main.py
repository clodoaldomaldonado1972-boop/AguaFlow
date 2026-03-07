import flet as ft
import os
# Importando seus módulos
import auth
import reports
import utils
import medicao
import database as db  # Vamos usar apenas 'db' para facilitar


def main(page: ft.Page):
    # --- CONFIGURAÇÃO DE INTERFACE ---
    page.title = "ÁguaFlow"
    page.window_bgcolor = ft.Colors.TRANSPARENT
    page.bgcolor = "#1A1C1E"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 450
    page.window_height = 800
    page.window_resizable = False  # Mantém o design estável
    page.padding = 0
    page.spacing = 0

    # Inicializa o banco de dados aqui dentro
    db.init_db()

    # O "Palco" que vai receber os módulos
    palco = ft.Container(expand=True, bgcolor="#1A1C1E")

    def navegar_menu(perfil):
        # Menu atualizado: Removido QR Code redundante e adicionada Ajuda
        botoes = [
            ft.Text(f"PERFIL: {perfil.upper()}", color="blue", weight="bold", size=20),
            ft.Divider(color="white10"),

            # 1. BOTÃO MEDIÇÃO
            ft.FilledButton("INICIAR LEITURA", width=280,
                on_click=lambda _: carregar_modulo(medicao.montar_tela(page, lambda: navegar_menu(perfil)))),

            # 2. BOTÃO RELATÓRIOS (Onde os QR Codes já são gerados)
            ft.FilledButton("RELATÓRIOS MENSAL", width=280,
                on_click=lambda _: carregar_modulo(reports.montar_tela_relatorios(page, lambda: navegar_menu(perfil)))),

            # 3. NOVO BOTÃO AJUDA (Substituindo o QR Code direto)
            ft.OutlinedButton("AJUDA / SUPORTE", width=280,
                on_click=lambda _: carregar_modulo(utils.montar_tela_ajuda(lambda: navegar_menu(perfil)))),
            
            ft.Container(height=20),
            ft.TextButton("SAIR / LOGOUT", on_click=lambda _: iniciar_app())
        ]

        carregar_modulo(ft.Column(botoes, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15))

        carregar_modulo(ft.Column(
            botoes, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15))

    def carregar_modulo(conteudo):
        # Limpa o palco e insere o novo conteúdo
        palco.content = ft.Container(
            content=conteudo,
            padding=20,
            expand=True,
            bgcolor="#1A1C1E",
            alignment=ft.Alignment(0, -1)
        )
        page.update()

    def iniciar_app():
        # Tela inicial de Login
        carregar_modulo(auth.criar_tela_login(page, navegar_menu))

    page.add(palco)
    iniciar_app()


if __name__ == "__main__":
    os.environ["FLET_RENDERER"] = "skia"
    ft.run(main) # Mudamos de ft.app para ft.run
