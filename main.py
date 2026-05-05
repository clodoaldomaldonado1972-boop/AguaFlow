from utils.updater import AppUpdater
import sys
import os
import warnings
import asyncio
import flet as ft
import gc
from flet import icons
import views.auth as auth_view
from database.database import Database
from database.sync_service import SyncService

# 1. AJUSTE DE PATH E COMPATIBILIDADE
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Ensure ft.icons refers to the imported icons module
ft.icons = icons


async def main(page: ft.Page):
    is_mobile = page.platform in [ft.PagePlatform.ANDROID, ft.PagePlatform.IOS]

    # CONFIGURAÇÃO AUTOMATIZADA DO TÍTULO
    page.title = AppUpdater.get_footer()
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#121417"

    if not is_mobile:
        page.window_width = 450
        page.window_height = 850
        page.window_resizable = True

    # --- 1. DEFINA A FUNÇÃO PRIMEIRO ---
    async def route_change(e):
        try:
            print(f"🛣️ Navegando para: {page.route}")
            gc.collect()  # Otimização agressiva de RAM para o APK
            page.views.clear()
            # ... suas outras rotas ...
            # 1. ROTAS INICIAIS
            if page.route == "/":
                page.views.append(auth_view.criar_tela_login(page))

            elif page.route == "/registro":
                from views.autenticacao import montar_tela_autenticacao
                page.views.append(montar_tela_autenticacao(page))

            elif page.route == "/menu":
                from views.menu_principal import montar_menu
                page.views.append(montar_menu(page))

            # 2. ROTAS OPERACIONAIS (LINHA 70 CORRIGIDA)
            elif page.route == "/medicao":
                from views.medicao import montar_tela_medicao
                page.views.append(montar_tela_medicao(page))

            elif page.route == "/scanner":
                from views.scanner_view import montar_tela_scanner
                page.views.append(montar_tela_scanner(page))

            elif page.route == "/sincronizar":
                from views.sincronizacao import montar_tela_sincronizacao
                page.views.append(montar_tela_sincronizacao(page))

            elif page.route == "/relatorios":
                from views.reports import montar_tela_relatorios
                page.views.append(montar_tela_relatorios(page))

            # 3. ROTAS ADMINISTRATIVAS
            elif page.route in ["/dashboard_saude", "/configuracoes"]:
                if page.route == "/dashboard_saude":
                    from views.dashboard_saude import montar_tela_saude
                    page.views.append(montar_tela_saude(
                        page, lambda _: page.go("/menu")))
                elif page.route == "/configuracoes":
                    from views.configuracoes import montar_tela_configs
                    page.views.append(montar_tela_configs(page))

            page.update()
        except Exception as ex:
            print(f"Erro na rota: {ex}")

    # --- 2. DEPOIS ATRIBUA E CHAME ---
    page.on_route_change = route_change

    # 3. BOOTSTRAP DE FUNDO (TELEMETRIA E BANCO)
    async def bootstrap_seguro():
        try:
            await asyncio.sleep(1)  # Delay para a UI carregar primeiro

            # Inicializa tabelas e logs (Offline-First)
            await asyncio.to_thread(Database.inicializar_tabelas)
            await SyncService.init_sync_log_table()

            # Inicia sincronização em background (não bloqueante)
            asyncio.create_task(SyncService.processar_fila())

            print("🚀 AguaFlow: Sistemas de Telemetria Ativos.")
        except Exception as e:
            print(f"Erro no boot: {e}")

    # --- 4. EXECUÇÃO E RENDERIZAÇÃO ---
    page.on_route_change = lambda e: page.run_task(route_change, e)

    # Inicia os serviços de telemetria e banco de dados em segundo plano
    page.run_task(bootstrap_seguro)

    # Força a carga da tela inicial (Login) antes de finalizar a main
    page.go("/")

    # Atualiza a página para garantir que a interface saia do buffer para a tela
    page.update()

# 5. INICIALIZAÇÃO DO MOTOR FLET (FORA DA FUNÇÃO MAIN)
if __name__ == "__main__":
    import asyncio
    # O comando abaixo abre o aplicativo.
    # Para o APK final, o Flet gerencia isso automaticamente.
    ft.app(target=main)
