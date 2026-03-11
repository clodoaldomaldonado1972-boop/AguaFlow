from datetime import datetime
import flet as ft
import os
import auth
import reports
import utils
import medicao
import database as db
import asyncio

# 1. INICIALIZAÇÃO SEGURA


def inicializar_sistema():
    db.init_db()
    # Cria pasta de relatórios do mês atual conforme plano de ação
    pasta_mensal = datetime.now().strftime("Relatorios_%Y_%m")
    if not os.path.exists(pasta_mensal):
        os.makedirs(pasta_mensal)
    print("✅ SISTEMA AGUA FLOW - VIVERE PRUDENTE: CONECTADO")

# 2. MAESTRO DO APP


async def main(page: ft.Page):
    page.title = "Agua Flow - Vivere Prudente"
    page.theme_mode = ft.ThemeMode.DARK

    # Configurações para simular Mobile no navegador
    page.window_width = 450
    page.window_height = 800
    page.padding = 0
    page.spacing = 0

    inicializar_sistema()

    # Container principal (Palco) onde os módulos serão montados
    palco = ft.Container(expand=True, bgcolor="#1A1C1E")

    async def carregar_modulo(conteudo):
        """Limpa o overlay e troca o conteúdo do palco de forma segura."""
        page.overlay.clear()
        palco.content = conteudo
        page.update()

    async def navegar_menu(perfil):
        async def voltar_e_recarregar(recarregar_medicao=False):
            # Garante que qualquer resquício de tela anterior suma
            page.overlay.clear()
            page.update()

            if recarregar_medicao:
                # Chama o montar_tela do medicao.py que já ajustamos
                tela = await medicao.montar_tela(page, voltar_e_recarregar)
                await carregar_modulo(tela)
            else:
                await navegar_menu(perfil)

        # AÇÕES DO MENU (Todas Async para evitar ID Errors)
        async def ir_para_leitura(e):
            await voltar_e_recarregar(True)

        async def gerar_relatorio_clique(e):
            # Integração com o módulo de reports
            caminho = reports.gerar_pdf_mensal()
            page.snack_bar = ft.SnackBar(
                ft.Text(f"Relatório gerado em: {caminho}"))
            page.snack_bar.open = True
            page.update()

        async def sair(e):
            await iniciar_app()

        # INTERFACE DO MENU PRINCIPAL
        menu = ft.Column([
            ft.Container(height=40),
            ft.Icon(ft.Icons.WATER_DROP_ROUNDED, color="blue", size=100),
            ft.Text("AGUA FLOW", size=32, weight="bold", color="blue"),
            ft.Text(f"OPERADOR: {perfil.upper()}", size=16, color="white70"),
            ft.Container(height=30),

            ft.FilledButton(
                "INICIAR LEITURA",
                icon=ft.Icons.PLAY_ARROW_ROUNDED,
                width=300, height=60,
                on_click=ir_para_leitura
            ),

            ft.OutlinedButton(
                "GERAR RELATÓRIO PDF",
                icon=ft.Icons.PICTURE_AS_PDF,
                width=300, height=50,
                on_click=gerar_relatorio_clique
            ),

            ft.Container(height=20),
            ft.TextButton("LOGOUT / SAIR", icon=ft.Icons.LOGOUT,
                          on_click=sair, icon_color="red")
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15)

        await carregar_modulo(menu)

    async def iniciar_app():
        # Chama a tela de login do auth.py
        await carregar_modulo(auth.criar_tela_login(page, navegar_menu))

    page.add(palco)
    await iniciar_app()

# 3. EXECUÇÃO MULTI-PLATAFORMA
if __name__ == "__main__":
    # Mantemos WEB_BROWSER para facilitar seus testes no Samsung M14 via rede local
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=8080, host="0.0.0.0")
