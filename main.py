from utils.updater import AppUpdater
import sys
import os
import warnings
import asyncio
import flet as ft
import gc
from flet import icons # Explicitly import flet.icons module

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

    import views.auth as auth_view
    from database.database import Database
    from database.sync_service import SyncService

    async def route_change(e):
        try:
            gc.collect()  # Limpa a RAM em cada mudança de rota
            print(f"Mudando rota para: {page.route}")
            page.views.clear()

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
            # O 'except' deve apenas tratar o erro, sem elifs operacionais dentro dele
            print(f"ERRO CRITICO NA ROTA {page.route}: {ex}")
            page.views.append(
                ft.View(
                    route=page.route,
                    controls=[
                        ft.Icon("error_outline", color="red", size=50),
                        ft.Text("Falha ao carregar tela",
                                size=20, weight="bold"),
                        ft.Text(str(ex), color="white70", text_align="center"),
                        ft.ElevatedButton("Voltar ao Menu",
                                          on_click=lambda _: page.go("/menu")),
                    ],
                    vertical_alignment="center",
                    horizontal_alignment="center",
                )
            )
            page.update()

    async def bootstrap_background():
        """Inicialização e Verificação de Atualização"""
        try:
            await asyncio.sleep(0.1)
            # VERIFICAÇÃO AUTOMÁTICA NO SUPABASE
            await AppUpdater.checar_atualizacao_supabase(page)

            await asyncio.to_thread(Database.inicializar_tabelas)
            await SyncService.init_sync_log_table()
            page.run_task(SyncService.processar_fila)
        except Exception as e:
            print(f"Erro no bootstrap: {e}")

    page.on_route_change = lambda e: page.run_task(route_change, e)

    page.views.clear()
    page.views.append(auth_view.criar_tela_login(page))
    page.go("/")
    page.run_task(bootstrap_background)

if __name__ == "__main__":
    ft.app(target=main)
