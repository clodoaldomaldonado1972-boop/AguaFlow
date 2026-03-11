from datetime import datetime
import flet as ft
import os
import auth
import reports
import utils
import medicao
import database as db

# 1. INICIALIZAÇÃO (Deve vir antes do main para o Python reconhecê-la)


def inicializar_sistema():
    """Garante que o banco e pastas existam antes do app carregar."""
    db.init_db()
    pasta_mensal = datetime.now().strftime("Relatorios_%Y_%m")
    if not os.path.exists(pasta_mensal):
        os.makedirs(pasta_mensal)
    print("✅ SISTEMA AGUA FLOW CONECTADO E PRONTO!")

# 2. APP PRINCIPAL (O MAESTRO)


async def main(page: ft.Page):
    # Configurações de Interface
    page.title = "Agua Flow - Vivere Prudente"
    page.window_bgcolor = "#1A1C1E"
    page.bgcolor = "#1A1C1E"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 450
    page.window_height = 800
    page.window_resizable = False

    inicializar_sistema()

    # DEFINIÇÃO DO PALCO (Onde as telas aparecem)
    palco = ft.Container(expand=True, bgcolor="#1A1C1E")

    async def carregar_modulo(conteudo):
        """Troca o conteúdo do palco com suporte assíncrono."""
        page.overlay.clear()
        palco.content = conteudo
        page.update()  # Remova o _async se der erro, o update simples resolve em funções asynccls

    async def navegar_menu(perfil):
        """Gerencia o menu principal após o login."""

        async def voltar_e_recarregar(recarregar_medicao=False):
            """Lógica de fluxo contínuo para as medições do Grupo 8."""
            if recarregar_medicao:
                conteudo = await medicao.montar_tela(page, voltar_e_recarregar)
                await carregar_modulo(conteudo)
            else:
                await navegar_menu(perfil)

        # Botões do Menu Principal
        botoes = ft.Column([
            ft.Icon(ft.Icons.WATER_DROP, color="blue", size=60),
            ft.Text(f"OPERADOR: {perfil.upper()}",
                    color="white", weight="bold"),
            ft.FilledButton(
                "INICIAR LEITURA",
                icon=ft.Icons.QR_CODE_SCANNER,
                on_click=lambda _: page.run_task(
                    lambda: voltar_e_recarregar(True))
            ),
            ft.TextButton(
                "Sair", on_click=lambda _: page.run_task(iniciar_app))
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20)

        await carregar_modulo(botoes)

    async def iniciar_app():
        """Inicia o fluxo pelo módulo de autenticação."""
        await carregar_modulo(auth.criar_tela_login(page, navegar_menu))

    # Adiciona o palco vazio e inicia o login
    page.add(palco)
    await iniciar_app()

# 3. EXECUÇÃO EM MODO SERVIDOR
if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=8080, host="0.0.0.0")
