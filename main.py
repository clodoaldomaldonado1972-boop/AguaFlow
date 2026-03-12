from datetime import datetime
import flet as ft
import os
import auth
import reports
import medicao
import database as db
import asyncio
import audio_utils

# =============================================================================
# 1. INICIALIZAÇÃO DE INFRAESTRUTURA
# =============================================================================


def inicializar_sistema():
    db.init_db()
    for pasta in ["qrcodes", "audios"]:
        if not os.path.exists(pasta):
            os.makedirs(pasta)
    print("✅ SISTEMA AGUA FLOW - VIVERE PRUDENTE: CONECTADO E PRONTO")

# =============================================================================
# 2. ORQUESTRADOR PRINCIPAL (MAESTRO DO APP)
# =============================================================================


async def main(page: ft.Page):
    page.title = "Agua Flow - Vivere Prudente"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 450
    page.window_height = 800
    page.padding = 0
    page.spacing = 0
    page.window_resizable = False

    inicializar_sistema()

    som_alerta, som_sucesso = audio_utils.adicionar_sons(page)
    page.session.set("som_alerta", som_alerta)
    page.session.set("som_sucesso", som_sucesso)

    palco = ft.Container(expand=True, bgcolor="#1A1C1E")

    async def carregar_modulo(conteudo):
        page.overlay.clear()
        palco.content = conteudo
        page.update()

    async def navegar_menu(perfil):
        async def voltar_ao_menu(recarregar_medicao=False):
            if recarregar_medicao:
                tela = await medicao.montar_tela(page, voltar_ao_menu)
                await carregar_modulo(tela)
            else:
                await navegar_menu(perfil)

        async def ir_para_leitura(e):
            await voltar_ao_menu(recarregar_medicao=True)

        async def ir_para_relatorios(e):
            tela_rep = reports.montar_tela_relatorios(page, voltar_ao_menu)
            await carregar_modulo(tela_rep)

        async def sair(e):
            await iniciar_app()

        # --- INTERFACE DO MENU PRINCIPAL (DASHBOARD) ---
        menu = ft.Column([
            ft.Container(height=60),
            ft.Icon(ft.icons.WATER_DROP_ROUNDED, color="blue", size=80),
            ft.Text("MENU PRINCIPAL", size=24, weight="bold"),
            ft.Text(f"Perfil: {perfil.capitalize()}",
                    size=14, color="white70"),
            ft.Container(height=40),

            # Botão de ação primária
            ft.FilledButton(
                "INICIAR LEITURA",
                icon=ft.icons.PLAY_ARROW_ROUNDED,
                width=300, height=60,
                on_click=ir_para_leitura
            ),

            # Botão de ação secundária
            ft.OutlinedButton(
                "PAINEL DE RELATÓRIOS",
                icon=ft.icons.ASSESSMENT_ROUNDED,
                width=300, height=60,
                on_click=ir_para_relatorios,
                style=ft.ButtonStyle(side={"": ft.BorderSide(1, "blue")})
            ),

            ft.Container(height=40),
            ft.TextButton(
                "LOGOUT / ENCERRAR SESSÃO",
                icon=ft.icons.LOGOUT,
                on_click=sair,
                icon_color="red"
            )
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15)

        await carregar_modulo(menu)

    async def iniciar_app():
        await carregar_modulo(auth.criar_tela_login(page, navegar_menu))

    page.add(palco)
    await iniciar_app()

# =============================================================================
# 3. LANÇAMENTO MULTI-PLATAFORMA
# =============================================================================

if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=8080, host="0.0.0.0")
