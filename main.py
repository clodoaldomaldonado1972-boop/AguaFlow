from datetime import datetime
import flet as ft
import os
import auth
import reports
import utils
import medicao
import database as db

# =============================================================================
# 1. INICIALIZAÇÃO E MANUTENÇÃO DO SISTEMA
# =============================================================================


def inicializar_sistema():
    """Garante a infraestrutura necessária antes do app rodar."""
    # 1. Cérebro: Inicializa o SQLite e as tabelas de unidades
    db.init_db()

    # 2. Gráfica: Cria pastas para os relatórios mensais do Vivere Prudente
    pasta_mensal = datetime.now().strftime("Relatorios_%Y_%m")
    if not os.path.exists(pasta_mensal):
        os.makedirs(pasta_mensal)

    # 3. Modularidade: Verifica se a base de QR Codes está pronta
    if not os.path.exists("qrcodes") or len(os.listdir("qrcodes")) < 10:
        print("🚀 Gerando base de QR Codes inicial via reports.py...")
        # Lógica de geração em lote integrada ao reports

    print("✅ SISTEMA AGUA FLOW CONECTADO E PRONTO!")

# =============================================================================
# 2. APP PRINCIPAL (O MAESTRO)
# =============================================================================


def main(page: ft.Page):
    # Configurações de Interface otimizadas para o Samsung M14
    page.title = "Agua Flow - Vivere Prudente"
    page.window_bgcolor = "#1A1C1E"
    page.bgcolor = "#1A1C1E"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 450
    page.window_height = 800
    page.window_resizable = False
    page.padding = 0
    page.spacing = 0

    inicializar_sistema()

    # Palco Principal: Container onde as telas (módulos) serão trocadas
    palco = ft.Container(expand=True, bgcolor="#1A1C1E")

    def carregar_modulo(conteudo):
        """
        Limpa o palco e injeta o novo conteúdo.
        Fundamental para evitar sobreposição de controles antigos (Erro Unknown Control).
        """
        # Limpeza crítica do overlay da página antes de trocar de tela
        page.overlay.clear()

        palco.content = ft.Container(
            content=conteudo,
            padding=20,
            expand=True,
            bgcolor="#1A1C1E",
            alignment=ft.Alignment(0, -1)
        )
        page.update()

    def navegar_menu(perfil):
        """Gerencia o menu principal após a autenticação bem-sucedida."""
        print(f"🚀 LOGIN DETECTADO: Perfil {perfil}")

        try:
            page.clean()
            page.add(palco)

            # FUNÇÃO DE RETORNO: Mantém o fluxo contínuo de medição
            def voltar_e_recarregar(recarregar_medicao=False):
                """
                Se 'recarregar_medicao' for True, busca a próxima unidade do prédio.
                Se False, volta para este menu.
                """
                if recarregar_medicao:
                    carregar_modulo(medicao.montar_tela(
                        page, voltar_e_recarregar))
                else:
                    navegar_menu(perfil)

            # Componentes do Menu
            botoes = [
                ft.Icon(ft.Icons.WATER_DROP, color="blue", size=60),
                ft.Text(f"OPERADOR: {perfil.upper()}",
                        color="white", weight="bold", size=20),
                ft.Divider(color="white10", height=40),

                ft.FilledButton(
                    "INICIAR LEITURA",
                    width=300, height=50,
                    icon=ft.Icons.QR_CODE_SCANNER,
                    on_click=lambda _: carregar_modulo(
                        medicao.montar_tela(page, voltar_e_recarregar))
                ),

                ft.FilledButton(
                    "PAINEL DE RELATÓRIOS",
                    width=300, height=50,
                    icon=ft.Icons.PIE_CHART,
                    on_click=lambda _: carregar_modulo(
                        reports.montar_tela_relatorios(page, lambda: navegar_menu(perfil)))
                ),

                ft.TextButton("Sair do Sistema", icon=ft.Icons.LOGOUT,
                              on_click=lambda _: iniciar_app())
            ]

            carregar_modulo(ft.Column(
                botoes,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=15
            ))
            print("✅ Menu carregado com sucesso!")

        except Exception as erro:
            print(f"❌ ERRO NA TROCA DE TELA: {erro}")

    def iniciar_app():
        """Inicia o fluxo pela tela de login (módulo auth)."""
        carregar_modulo(auth.criar_tela_login(page, navegar_menu))

    # Inicialização da interface
    page.add(palco)
    iniciar_app()


# Execução em modo servidor para acesso externo via IP
if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=8080, host="0.0.0.0")
