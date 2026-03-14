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
    # Criamos pastas essenciais se não existirem
    for pasta in ["qrcodes", "audios", "relatorios_pdf"]:
        if not os.path.exists(pasta):
            os.makedirs(pasta)
    print("✅ SISTEMA AGUA FLOW - VIVERE PRUDENTE: CONECTADO E PRONTO")

# =============================================================================
# 2. ORQUESTRADOR PRINCIPAL (MAESTRO DO APP)
# =============================================================================


async def main(page: ft.Page):
    # Configurações de Janela e Estética
    page.title = "Agua Flow - Vivere Prudente"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 450
    page.window_height = 800
    page.padding = 0
    page.spacing = 0
    page.window_resizable = False

    inicializar_sistema()

    # --- GERENCIAMENTO DE ÁUDIO ---
    # Carregamos os sons que serão usados para o "Bipe" de erro e sucesso
    som_alerta, som_sucesso = audio_utils.adicionar_sons(page)
    page.session.set("som_alerta", som_alerta)
    page.session.set("som_sucesso", som_sucesso)

    # Palco principal onde as telas (módulos) serão trocadas
    palco = ft.Container(expand=True, bgcolor="#1A1C1E")

    async def carregar_modulo(conteudo):
        """Limpa o palco e carrega um novo módulo (tela)"""
        page.overlay.clear()  # Limpa diálogos ou menus abertos anteriormente
        palco.content = conteudo
        page.update()

    async def navegar_menu(perfil):
        """Gerencia a navegação entre as funcionalidades do Dashboard"""

        async def voltar_ao_menu(recarregar_medicao=False):
            """Função de callback que os módulos chamam para retornar ao início"""
            if recarregar_medicao:
                # Se recarregar_medicao for True, ele abre a tela de leitura de andares
                tela = await medicao.montar_tela(page, voltar_ao_menu)
                await carregar_modulo(tela)
            else:
                await navegar_menu(perfil)

        async def ir_para_leitura(e):
            """Aciona o módulo de medição (Água/Gás)"""
            # Aqui o sistema verifica se há leitura pendente antes de montar a tela
            await voltar_ao_menu(recarregar_medicao=True)

        async def ir_para_relatorios(e):
            """Aciona o módulo de geração de PDF e envio de E-mail"""
            tela_rep = reports.montar_tela_relatorios(page, voltar_ao_menu)
            await carregar_modulo(tela_rep)

        async def sair(e):
            """Encerra a sessão e volta para o Login"""
            await iniciar_app()

        # --- INTERFACE DO MENU PRINCIPAL (DASHBOARD) ---
        menu = ft.Column([
            ft.Container(height=60),
            ft.Icon(ft.Icons.WATER_DROP_ROUNDED, color="blue", size=80),
            ft.Text("AGUA FLOW", size=28, weight="bold", letter_spacing=2),
            ft.Text(f"Perfil: {perfil.capitalize()}",
                    size=14, color="white70"),
            ft.Container(height=40),

            # Botão Central: Iniciar/Retomar Leitura
            ft.FilledButton(
                "INICIAR / RETOMAR LEITURA",
                icon=ft.Icons.PLAY_ARROW_ROUNDED,
                width=320, height=70,
                on_click=ir_para_leitura,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=10))
            ),

            # Botão Secundário: Relatórios e PDF
            ft.OutlinedButton(
                "GERAR RELATÓRIOS PDF",
                icon=ft.Icons.PICTURE_AS_PDF_ROUNDED,
                width=320, height=60,
                on_click=ir_para_relatorios,
                style=ft.ButtonStyle(side={"": ft.BorderSide(1, "blue")})
            ),

            ft.Container(height=60),
            ft.TextButton(
                "SAIR DO SISTEMA",
                icon=ft.Icons.POWER_SETTINGS_NEW_ROUNDED,
                on_click=sair,
                icon_color="red700"
            )
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15)

        await carregar_modulo(menu)

    async def iniciar_app():
        """Ponto de entrada: Tela de Login"""
        await carregar_modulo(auth.criar_tela_login(page, navegar_menu))

    page.add(palco)
    await iniciar_app()

# =============================================================================
# 3. LANÇAMENTO (CONFIGURADO PARA RODAR LOCAL OU WEB)
# =============================================================================

if __name__ == "__main__":
    # Host 0.0.0.0 permite acesso de outros dispositivos na mesma rede (Celular por exemplo)
    # Mudado para FLET_APP para suporte a bipe sonoro melhor
    ft.app(target=main, view=ft.AppView.FLET_APP)
