from datetime import datetime
import flet as ft
import os
import auth
import reports
import utils
import medicao
import database as db

# 1. INICIALIZAÇÃO


def inicializar_sistema():
    db.init_db()
    pasta_mensal = datetime.now().strftime("Relatorios_%Y_%m")
    if not os.path.exists(pasta_mensal):
        os.makedirs(pasta_mensal)
    print("✅ SISTEMA AGUA FLOW CONECTADO E PRONTO!")

# 2. MAESTRO DO APP


async def main(page: ft.Page):
    page.title = "Agua Flow - Vivere Prudente"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 450
    page.window_height = 800

    inicializar_sistema()

    palco = ft.Container(expand=True, bgcolor="#1A1C1E")

    async def carregar_modulo(conteudo):
        page.overlay.clear()
        palco.content = conteudo
        page.update()

    async def navegar_menu(perfil):
        async def voltar_e_recarregar(recarregar_medicao=False):
            if recarregar_medicao:
                # Aqui o await é obrigatório
                tela = await medicao.montar_tela(page, voltar_e_recarregar)
                await carregar_modulo(tela)
            else:
                await navegar_menu(perfil)

        # FUNÇÕES DE CLIQUE DIRETAS (Sem Lambda para não travar)
        async def ir_para_leitura(e):
            await voltar_e_recarregar(True)

        async def sair(e):
            await iniciar_app()

        # INTERFACE DO MENU
        menu = ft.Column([
            ft.Icon(ft.Icons.WATER_DROP, color="blue", size=100),
            ft.Text(f"OPERADOR: {perfil.upper()}", size=20, weight="bold"),
            ft.Container(height=20),
            ft.FilledButton(
                "INICIAR LEITURA",
                icon=ft.Icons.QR_CODE_SCANNER,
                width=300, height=60,
                on_click=ir_para_leitura
            ),
            ft.TextButton("Sair", icon=ft.Icons.LOGOUT, on_click=sair)
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20)

        await carregar_modulo(menu)

    async def iniciar_app():
        await carregar_modulo(auth.criar_tela_login(page, navegar_menu))

    page.add(palco)
    await iniciar_app()

# 3. EXECUÇÃO
if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=8080, host="0.0.0.0")
