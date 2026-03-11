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
    """
    Garante a integridade do ambiente antes do início do loop do app.
    Prepara o Banco de Dados e as pastas físicas para armazenamento.
    """
    # Inicializa o SQLite (Tabelas de leituras e histórico)
    db.init_db()

    # Cria diretórios necessários para evitar erros de FileNotFoundError
    # 'qrcodes' armazena as imagens geradas para colagem nos hidrômetros
    # 'audios' deve conter o arquivo de bipe para o operador
    for pasta in ["qrcodes", "audios"]:
        if not os.path.exists(pasta):
            os.makedirs(pasta)

    print("✅ SISTEMA AGUA FLOW - VIVERE PRUDENTE: CONECTADO E PRONTO")

# =============================================================================
# 2. ORQUESTRADOR PRINCIPAL (MAESTRO DO APP)
# =============================================================================


async def main(page: ft.Page):
    """
    Função principal que gerencia o estado global, navegação e ciclo de vida.
    """
    page.title = "Agua Flow - Vivere Prudente"
    page.theme_mode = ft.ThemeMode.DARK

    # --- CONFIGURAÇÃO DE VIEWPORT (Mobile-First) ---
    # Define dimensões que simulam a tela de um smartphone no navegador
    page.window_width = 450
    page.window_height = 800
    page.padding = 0
    page.spacing = 0
    # Mantém o layout fixo para evitar quebras em telas pequenas
    page.window_resizable = False

    # Executa a limpeza e preparação de pastas
    inicializar_sistema()

    # --- GERENCIAMENTO DE RECURSOS TÉCNICOS (ÁUDIO) ---
    # Carregamos os sons uma única vez no nível raiz para economia de memória.
    # Usamos a 'session' para que o módulo 'medicao.py' acesse o áudio sem recarregá-lo.
    som_alerta, som_sucesso = audio_utils.adicionar_sons(page)
    page.session.set("som_alerta", som_alerta)
    page.session.set("som_sucesso", som_sucesso)

    # --- ARQUITETURA DE NAVEGAÇÃO (PALCO) ---
    # O 'palco' é um container vazio que recebe os módulos (Login, Menu, Medição).
    # Isso evita o uso de rotas complexas em um app de campo offline-first.
    palco = ft.Container(expand=True, bgcolor="#1A1C1E")

    async def carregar_modulo(conteudo):
        """
        Mecanismo de 'Hot Swap' de conteúdo. 
        Limpa overlays (diálogos, pickers) antes de injetar a nova tela.
        """
        page.overlay.clear()
        palco.content = conteudo
        page.update()

    async def navegar_menu(perfil):
        """
        Centraliza a lógica de navegação após a autenticação.
        Recebe o 'perfil' do auth.py para personalizar a experiência.
        """

        async def voltar_ao_menu(recarregar_medicao=False):
            """
            Função de Callback: permite que as telas filhas (medicao/reports)
            solicitem o retorno ao menu principal ou reiniciem o ciclo.
            """
            if recarregar_medicao:
                # Reinicia o módulo de medição buscando o próximo apto pendente no DB
                tela = await medicao.montar_tela(page, voltar_ao_menu)
                await carregar_modulo(tela)
            else:
                await navegar_menu(perfil)

        # --- HANDLERS DE EVENTOS ASYNC ---
        async def ir_para_leitura(e):
            """Aciona o fluxo de medição andar por andar."""
            await voltar_ao_menu(recarregar_medicao=True)

        async def ir_para_relatorios(e):
            """Aciona o painel modular de geração de PDF e Etiquetas QR."""
            tela_rep = reports.montar_tela_relatorios(page, voltar_ao_menu)
            await carregar_modulo(tela_rep)

        async def sair(e):
            """Encerra a sessão e retorna ao Login."""
            await iniciar_app()

        # --- INTERFACE DO MENU PRINCIPAL (DASHBOARD) ---
        menu = ft.Column([
            ft.Container(height=60),  # Respiro superior
            ft.Icon(ft.Icons.WATER_DROP_ROUNDED, color="blue", size=80),
            ft.Text("AGUA FLOW", size=32, weight="bold", color="blue"),
            ft.Text(f"OPERADOR: {perfil.upper()}",
                    size=14, color="white70", weight="w500"),
            ft.Container(height=40),

            # Botão de ação primária (Início do trabalho de campo)
            ft.FilledButton(
                "INICIAR LEITURA",
                icon=ft.Icons.PLAY_ARROW_ROUNDED,
                width=300, height=60,
                on_click=ir_para_leitura
            ),

            # Botão de ação secundária (Administrativo)
            ft.OutlinedButton(
                "PAINEL DE RELATÓRIOS",
                icon=ft.Icons.ASSESSMENT_ROUNDED,
                width=300, height=60,
                on_click=ir_para_relatorios,
                style=ft.ButtonStyle(side={"": ft.BorderSide(1, "blue")})
            ),

            ft.Container(height=40),
            ft.TextButton(
                "LOGOUT / ENCERRAR SESSÃO",
                icon=ft.Icons.LOGOUT,
                on_click=sair,
                icon_color="red"
            )
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15)

        await carregar_modulo(menu)

    async def iniciar_app():
        """Ponto de entrada: Injeta o módulo de autenticação no palco."""
        await carregar_modulo(auth.criar_tela_login(page, navegar_menu))

    # Inicializa o palco na página
    page.add(palco)
    # Dispara o fluxo inicial
    await iniciar_app()

# =============================================================================
# 3. LANÇAMENTO MULTI-PLATAFORMA
# =============================================================================

if __name__ == "__main__":
    # Configurado para permitir acesso externo (ex: testar no celular via Wi-Fi do PC)
    # 'host=0.0.0.0' torna o app visível para outros dispositivos na mesma rede local.
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=8080, host="0.0.0.0")
