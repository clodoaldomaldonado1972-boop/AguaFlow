from utils.updater import AppUpdater
import sys
import os
import warnings
import asyncio
import flet as ft
import gc
from database.database import Database
from database.sync_service import SyncService

# 1. AJUSTE DE PATH E COMPATIBILIDADE
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
warnings.filterwarnings("ignore", category=DeprecationWarning)


async def main(page: ft.Page):
    is_mobile = page.platform in [ft.PagePlatform.ANDROID, ft.PagePlatform.IOS]
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#121417"

    # CONFIGURAÇÃO AUTOMATIZADA DO TÍTULO E TEMA
    page.title = AppUpdater.get_footer()

    if not is_mobile:
        page.window_width = 450
        page.window_height = 850
        page.window_resizable = True

    # --- 1. LÓGICA DE ROTEAMENTO (ASYNC) ---
    async def route_change(e):
        try:
            print(f"🛣️ Tentando navegar para: {page.route}")

            # Armazenamos a view antiga temporariamente para evitar tela branca imediata
            nova_view = None

            # 1. ROTAS INICIAIS
            if page.route == "/":
                import views.auth as auth_view
                nova_view = auth_view.criar_tela_login(page)

            elif page.route == "/registro":
                from views.autenticacao import montar_tela_autenticacao
                nova_view = montar_tela_autenticacao(page)

            elif page.route == "/menu":
                from views.menu_principal import montar_menu
                nova_view = montar_menu(page)

            # 2. ROTAS OPERACIONAIS
            elif page.route == "/medicao":
                from views.medicao import montar_tela_medicao
                nova_view = montar_tela_medicao(page)

            elif page.route == "/scanner":
                from views.scanner_view import montar_tela_scanner
                nova_view = montar_tela_scanner(page)

            elif page.route == "/sincronizar":
                from views.sincronizacao import montar_tela_sincronizacao
                nova_view = montar_tela_sincronizacao(page)

            elif page.route == "/relatorios":
                from views.relatorio_view import montar_tela_relatorio
                nova_view = montar_tela_relatorio(page)

            elif page.route == "/usuarios":
                from views.gerenciamento_usuarios import montar_tela_usuarios
                nova_view = montar_tela_usuarios(page)

            # 3. ROTAS ADMINISTRATIVAS
            elif page.route == "/dashboard_saude":
                from views.dashboard_saude import montar_tela_saude
                nova_view = montar_tela_saude(page, lambda _: page.go("/menu"))

            elif page.route == "/configuracoes":
                from views.configuracoes import montar_tela_configs
                nova_view = montar_tela_configs(page)

            elif page.route == "/sobre":
                from views.sobre_view import montar_tela_sobre
                nova_view = montar_tela_sobre(page)

            if nova_view:
                page.views.clear()
                page.views.append(nova_view)
            else:
                print(f"⚠️ Rota não encontrada: {page.route}")
                page.go("/")  # Redireciona para login se a rota falhar

            page.update()

        except Exception as ex:
            print(f"❌ Erro crítico na rota: {ex}")
            page.views.append(
                ft.View("/", [ft.Text(f"Erro ao carregar rota: {ex}", color="red")]))
            page.update()

    # --- 3. ATRIBUIÇÃO DE EVENTOS ---
    page.on_route_change = route_change

    # Define o que acontece ao clicar em "voltar" (essencial para Android/APK)
    def view_pop(view):
        if len(page.views) > 1:
            page.views.pop()
            top_view = page.views[-1]
            page.go(top_view.route)

    page.on_view_pop = view_pop

    # --- 4. BOOT E SPLASH ---
    async def inicializar_background():
        """Inicializa serviços pesados sem travar a UI inicial."""
        try:
            # Limpeza de cache antigo (opcional, cuidado se quiser manter dados)
            # await page.client_storage.clear_async()

            # Inicialização de Banco e Serviços em threads separadas
            await asyncio.to_thread(Database.inicializar_tabelas)
            await SyncService.init_sync_log_table()

            # Habilita o botão de login se ele já estiver na tela
            btn_login = page.session.get("btn_login")
            if btn_login:
                btn_login.content = None  # Remove o Row com ProgressRing
                btn_login.disabled = False
                btn_login.text = "ENTRAR"
                page.update()

            # Inicia o worker de sincronização
            asyncio.create_task(SyncService.processar_fila())
            print("🚀 AguaFlow: Serviços de Segundo Plano OK.")
        except Exception as e:
            print(f"❌ Erro no boot em background: {e}")

    # 1. Dispara a inicialização em segundo plano (não bloqueante)
    asyncio.create_task(inicializar_background())

    # 2. Navega imediatamente para a rota inicial (Login)
    # Se o usuário estiver dando hot-reload, mantém a rota atual, senão vai para "/"
    initial_route = page.route if page.route != "/" else "/"
    await route_change(None)  # Força a carga da primeira view
    page.go(initial_route)

# 5. INICIALIZAÇÃO DO MOTOR FLET
if __name__ == "__main__":
    # O comando abaixo abre o aplicativo localmente no modo Desktop
    ft.app(target=main, assets_dir="assets")
