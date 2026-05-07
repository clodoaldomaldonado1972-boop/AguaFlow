# 0. CONFIGURAÇÃO DE LOG
import logging
from database.sync_service import SyncService
from database.database import Database
import flet as ft
import asyncio
import os
import sys
from utils.updater import AppUpdater
from utils.logger_config import setup_logging

setup_logging()  # Inicializa o sistema de logs profissional
logger = logging.getLogger(__name__)

db_ready = False

# 1. AJUSTE DE PATH E COMPATIBILIDADE
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


async def main(page: ft.Page):
    global db_ready
    is_mobile = page.platform in [ft.PagePlatform.ANDROID, ft.PagePlatform.IOS]
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#121417"
    page.title = AppUpdater.get_footer()

    if not is_mobile:
        page.window_width = 450
        page.window_height = 850
        page.window_resizable = True

    # --- 1. LÓGICA DE ROTEAMENTO (VERSÃO LIMPA) ---
    async def route_change(e):
        try:
            logger.debug(f"🛣️ Rota acessada: {page.route}")
            nova_view = None

            if page.route == "/" or page.route == "" or page.route is None:
                import views.auth as auth_view
                nova_view = auth_view.criar_tela_login(page)
            elif page.route == "/registro":
                from views.autenticacao import montar_tela_autenticacao
                nova_view = montar_tela_autenticacao(page)
            elif page.route == "/esqueci_senha":
                import views.auth as auth_view
                nova_view = auth_view.montar_tela_esqueci_senha(page)
            elif page.route == "/menu":
                from views.menu_principal import montar_menu
                logger.info("🔄 Carregando view: Menu Principal")
                nova_view = montar_menu(page)
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
            elif page.route == "/configuracoes":
                from views.configuracoes import montar_tela_configs
                nova_view = montar_tela_configs(page)
            elif page.route == "/sobre":
                from views.sobre_view import montar_tela_sobre
                nova_view = montar_tela_sobre(page)

            if nova_view:
                page.views.clear()
                page.views.append(nova_view)
                page.update()
            else:
                page.go("/")
                logger.warning(
                    f"⚠️ Rota não encontrada: {page.route}. Redirecionando para /.")

        except Exception as ex:
            logger.error(f"❌ Erro na rota: {ex}", exc_info=True)
            page.views.append(
                ft.View("/", [ft.Text(f"Erro de carregamento: {ex}", color="red")]))
            page.update()

    # --- 2. ATRIBUIÇÃO DE EVENTOS ---
    page.on_route_change = route_change
    page.on_view_pop = lambda view: page.go(
        "/menu") if len(page.views) > 1 else None

    # --- 2.1 SISTEMA KEEP ALIVE (HEARTBEAT) ---
    async def heartbeat():
        """Mantém a sessão viva interagindo minimamente com a página."""
        while True:
            try:
                await asyncio.sleep(30)  # Ping a cada 30 segundos
                if page.session_id:
                    # Atualização silenciosa de metadados da sessão
                    page.user_data["heartbeat"] = True
                    # page.update() # Opcional: descomente se a sessão cair mesmo assim
            except Exception:
                break

    asyncio.create_task(heartbeat())

    # --- 3. BOOT EM BACKGROUND ---
    async def inicializar_background():
        global db_ready
        try:
            logger.info("⚙️ Iniciando boot do banco de dados e sincronia...")

            # Verificação silenciosa do serviço de e-mail
            from utils.logger_config import testar_configuracao_email
            await asyncio.to_thread(testar_configuracao_email)

            await asyncio.to_thread(Database.inicializar_tabelas)
            db_ready = True
            asyncio.create_task(SyncService.processar_fila())
            logger.info("🚀 AguaFlow: Banco de dados e Sync prontos.")
        except Exception as e:
            logger.critical(f"🛑 Erro fatal no boot: {e}", exc_info=True)

    # --- 4. EXECUÇÃO INICIAL ---
    asyncio.create_task(inicializar_background())

    # Navegação inicial manual para garantir que a tela apareça
    await route_change(None)

    # Manter a corrotina main viva para evitar Garbage Collection da sessão
    while True:
        await asyncio.sleep(3600)

# --- 5. MOTOR FLET ---
if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")
