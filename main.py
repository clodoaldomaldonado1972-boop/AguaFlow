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
from views.styles import BG_DARK, BG_LIGHT

setup_logging()  # Inicializa o sistema de logs profissional
logger = logging.getLogger(__name__)

db_ready = False

# 1. AJUSTE DE PATH E COMPATIBILIDADE
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


async def main(page: ft.Page):
    global db_ready
    is_mobile = page.platform in [ft.PagePlatform.ANDROID, ft.PagePlatform.IOS]
    from utils.camera_service import CameraService
    _prefs = ft.SharedPreferences()
    _file_picker = ft.FilePicker()
    _camera = CameraService()
    page.services = [_prefs, _file_picker, _camera]
    page.file_picker = _file_picker
    page.camera = _camera
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = BG_DARK
    page.title = AppUpdater.get_footer()

    async def toggle_tema():
        if page.theme_mode == ft.ThemeMode.DARK:
            page.theme_mode = ft.ThemeMode.LIGHT
            page.bgcolor = BG_LIGHT
            await _prefs.set("tema", "light")
        else:
            page.theme_mode = ft.ThemeMode.DARK
            page.bgcolor = BG_DARK
            await _prefs.set("tema", "dark")
        page.update()

    page.toggle_tema = toggle_tema

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
            elif page.route == "/dashboard_saude":
                from views.dashboard_saude import montar_tela_saude
                nova_view = montar_tela_saude(page, ao_voltar=lambda _: page.go("/menu"))
            elif page.route == "/recuperar-email":
                from views.recuperar_senha_email import criar_tela_recuperacao
                nova_view = criar_tela_recuperacao(page)
            elif page.route == "/sobre":
                from views.sobre_view import montar_tela_sobre
                nova_view = montar_tela_sobre(page)
            elif page.route == "/ajuda":
                from views.ajuda_view import montar_tela_ajuda
                nova_view = montar_tela_ajuda(page, on_back=lambda _: page.go("/menu"))
            elif page.route == "/historico":
                from views.historico import montar_tela_historico
                nova_view = await montar_tela_historico(page)
            elif page.route == "/dashboard":
                from views.dashboard import montar_tela_dashboard
                nova_view = montar_tela_dashboard(page, ao_voltar=lambda _: page.go("/menu"))


            if nova_view:
                page.views.clear()
                page.views.append(nova_view)
                page.update()
            else:
                await page.push_route("/")
                logger.warning(
                    f"⚠️ Rota não encontrada: {page.route}. Redirecionando para /.")

        except Exception as ex:
            logger.error(f"❌ Erro na rota: {ex}", exc_info=True)
            page.views.clear()
            page.views.append(ft.View(
                route="/",
                bgcolor="#121417",
                vertical_alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon(ft.Icons.ERROR_OUTLINE, size=64, color="red"),
                    ft.Text("Erro ao carregar tela", size=18, color="white"),
                    ft.Text(str(ex), size=12, color="grey", text_align=ft.TextAlign.CENTER),
                    ft.ElevatedButton("Voltar ao Menu", on_click=lambda _: page.go("/menu")),
                ]
            ))
            page.update()

    # --- 2. ATRIBUIÇÃO DE EVENTOS ---
    page.on_route_change = route_change
    page.on_view_pop = lambda view: page.go("/menu")

    # --- 1.1 EVENTO DE FECHAMENTO EXPLÍCITO ---
    async def handle_close(e):
        logger.info(f"🔌 Sessão {id(page)} encerrada pelo cliente.")

    page.on_close = handle_close

    # --- 2.1 SISTEMA KEEP ALIVE (HEARTBEAT) ---
    async def heartbeat():
        """Mantém a sessão viva interagindo minimamente com a página."""
        while True:
            try:
                # Reduzido para 20s para evitar timeouts de proxy/firewall
                await asyncio.sleep(20)
                page.user_data["heartbeat"] = True
                page.update()
            except Exception:
                logger.debug(
                    f"💓 Heartbeat: erro transitório na sessão {id(page)}, aguardando para tentar novamente.")
                await asyncio.sleep(5)
                continue

    page.user_data = {}
    asyncio.create_task(heartbeat())

    # --- 2.2 CARREGA TEMA PERSISTIDO ---
    async def carregar_tema():
        try:
            tema_salvo = await _prefs.get("tema")
            if tema_salvo == "light":
                page.theme_mode = ft.ThemeMode.LIGHT
                page.bgcolor = BG_LIGHT
                page.update()
        except Exception:
            pass

    # --- 2.3 SESSÃO PERSISTIDA ---
    async def salvar_sessao(user_data: dict):
        try:
            await _prefs.set("sessao_email", user_data.get("email", ""))
            await _prefs.set("sessao_role", user_data.get("role", "user"))
            await _prefs.set("sessao_nome", user_data.get("nome", ""))
            await _prefs.set("sessao_offline", str(user_data.get("offline", False)))
        except Exception as ex:
            logger.warning(f"⚠️ Não foi possível salvar sessão: {ex}")

    async def limpar_sessao():
        try:
            for k in ["sessao_email", "sessao_role", "sessao_nome", "sessao_offline"]:
                await _prefs.remove(k)
        except Exception as ex:
            logger.warning(f"⚠️ Não foi possível limpar sessão: {ex}")

    async def restaurar_sessao():
        try:
            email = await _prefs.get("sessao_email")
            if email:
                role = await _prefs.get("sessao_role") or "user"
                nome = await _prefs.get("sessao_nome") or ""
                offline_str = await _prefs.get("sessao_offline") or "False"
                page.user_data = {
                    "email": email,
                    "role": role,
                    "nome": nome,
                    "offline": offline_str == "True",
                }
                logger.info(f"🔑 Sessão restaurada: {email}")
                page.go("/menu")
        except Exception as ex:
            logger.warning(f"⚠️ Não foi possível restaurar sessão: {ex}")

    page.salvar_sessao = salvar_sessao
    page.limpar_sessao = limpar_sessao

    # --- 3. BOOT EM BACKGROUND ---
    async def inicializar_background():
        global db_ready
        try:
            logger.info("⚙️ Iniciando boot do banco de dados e sincronia...")

            # Verificação silenciosa do serviço de e-mail
            from utils.logger_config import testar_configuracao_email
            await asyncio.to_thread(testar_configuracao_email)

            await Database.configurar_db_path(page)
            await asyncio.to_thread(Database.inicializar_tabelas)
            db_ready = True
            await SyncService.init_sync_log_table()
            asyncio.create_task(SyncService.processar_fila())
            logger.info("🚀 AguaFlow: Banco de dados e Sync prontos.")
        except Exception as e:
            logger.critical(f"🛑 Erro fatal no boot: {e}", exc_info=True)

    # --- 4. EXECUÇÃO INICIAL ---
    asyncio.create_task(inicializar_background())

    # Navegação inicial manual para garantir que a tela apareça
    await route_change(None)

    asyncio.create_task(carregar_tema())
    asyncio.create_task(restaurar_sessao())

    # Manter a corrotina main viva para evitar Garbage Collection da sessão
    while True:
        await asyncio.sleep(3600)

# --- 5. MOTOR FLET ---
if __name__ == "__main__":
    ft.run(main, assets_dir="assets")
