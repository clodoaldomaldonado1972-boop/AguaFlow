import flet as ft
import os
import sys
import warnings
import asyncio

# 1. CONFIGURAÇÃO DE AMBIENTE
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Supressão de avisos técnicos
warnings.filterwarnings("ignore", category=UserWarning)
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# --- IMPORTAÇÕES DO CORE (Caminhos atualizados) ---
from database.database import Database
from utils.updater import AppUpdater, VERSION 

# --- IMPORTAÇÕES DAS VIEWS (Caminhos atualizados) ---
from views.auth import criar_tela_login, montar_tela_esqueci_senha
from views.autenticacao import montar_tela_autenticacao
from views.menu_principal import montar_menu
from views.medicao import montar_tela_medicao
from views.qrcodes_view import montar_tela_qrcodes
from views.relatorio_view import montar_tela_relatorio
from views.configuracoes import montar_tela_configs
from views.dashboard import montar_tela_dashboard
from views.dashboard_saude import montar_tela_saude 
from views.ajuda_usuario import montar_tela_ajuda 

async def main(page: ft.Page):
    # 2. CONFIGURAÇÕES GERAIS DA PÁGINA
    page.title = f"AguaFlow {VERSION} - Edifício Vivere"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 400
    page.window_height = 800
    page.window_resizable = True

    # 3. SISTEMA DE ROTEAMENTO (Navegação)
    async def route_change(route):
        try:
            page.views.clear()
            
            # Rota Raiz - Login
            if page.route == "/":
                page.views.append(criar_tela_login(page))
            
            elif page.route == "/autenticacao":
                page.views.append(montar_tela_autenticacao(page))

            elif page.route == "/esqueci_senha":
                page.views.append(montar_tela_esqueci_senha(page))

            elif page.route == "/menu":
                page.views.append(montar_menu(page))

            elif page.route == "/medicao":
                page.views.append(montar_tela_medicao(page))

            elif page.route == "/qrcodes":
                page.views.append(montar_tela_qrcodes(page))

            elif page.route == "/relatorios":
                page.views.append(montar_tela_relatorio(page))

            elif page.route == "/dashboard":
                page.views.append(montar_tela_dashboard(page))

            elif page.route == "/saude":
                page.views.append(montar_tela_saude(page, lambda _: page.go("/menu")))
                            
            elif page.route == "/configuracoes":
                page.views.append(montar_tela_configs(page, lambda _: page.go("/menu")))
            
            elif page.route == "/ajuda":
                page.views.append(montar_tela_ajuda(page, lambda _: page.go("/configuracoes")))
                        
            page.update()
            
        except Exception as err:
            print(f"[ERRO NAVEGAÇÃO] Rota {page.route}: {err}")

    def view_pop(e):
        if len(page.views) > 1:
            page.views.pop()
            top_view = page.views[-1]
            page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop

    # 4. INICIALIZAÇÃO DO SISTEMA
    try:
        # Garante que o banco de dados e as tabelas (leituras, sync_log) existem
        await Database.init_db()
        
        # Inicia na tela de login
        page.go("/")
        
        # Verifica atualizações em background para Android APK
        try:
            updater = AppUpdater(page)
            await updater.check_for_updates()
        except Exception as up_err:
            print(f"[UPDATER] Erro ao verificar atualizações: {up_err}")

    except Exception as e:
        print(f"[ERRO CRÍTICO] Falha ao iniciar AguaFlow: {e}")

# Início do App
if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")