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

from database.database import Database
from utils.updater import AppUpdater

# --- IMPORTAÇÕES DAS VIEWS ---
from views.auth import criar_tela_login
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
    page.title = "AguaFlow - Gestão Residencial"
    page.theme_mode = ft.ThemeMode.DARK # Alterado para Dark para combinar com o Vivere
    page.window_width = 400
    page.window_height = 800
    
    # Gerenciador de Mudança de Rotas
    def route_change(e):
        try:
            # Limpa as views atuais para evitar sobreposição
            page.views.clear()
            
            # --- MAPEAMENTO DE ROTAS ---
            
            # ROTA RAIZ / LOGIN
            if page.route == "/" or page.route == "/login":
                page.views.append(criar_tela_login(page))
            
            # ROTA REGISTRO / AUTENTICAÇÃO (Corrigido)
            elif page.route == "/registro" or page.route == "/autenticacao":
                page.views.append(montar_tela_autenticacao(page))
                
            # ROTA MENU PRINCIPAL
            elif page.route == "/menu":
                page.views.append(montar_menu(page))

            # ROTA MEDIÇÃO
            elif page.route == "/medicao":
                page.views.append(montar_tela_medicao(page, lambda _: page.go("/menu")))
                
            # ROTA RELATÓRIOS
            elif page.route == "/relatorios":
                page.views.append(montar_tela_relatorio(page, lambda _: page.go("/menu")))
                
            # ROTA QR CODES (Sincronizado com qrcodes_view.py)
            elif page.route == "/gerar_qrcode":
                page.views.append(montar_tela_qrcodes(page, lambda _: page.go("/menu")))

            # ROTA DASHBOARDS
            elif page.route == "/dashboard":
                page.views.append(montar_tela_dashboard(page, lambda _: page.go("/menu")))
                
            elif page.route == "/dashboard_saude":
                page.views.append(montar_tela_saude(page, lambda _: page.go("/menu")))
                
            # ROTA CONFIGURAÇÕES
            elif page.route == "/configuracoes":
                page.views.append(montar_tela_configs(page, lambda _: page.go("/menu")))
            
            # ROTA AJUDA
            elif page.route == "/ajuda":
                page.views.append(montar_tela_ajuda(page, lambda _: page.go("/configuracoes")))
                        
            page.update()
            
        except Exception as err:
            print(f"[ERRO NAVEGAÇÃO] Rota {page.route}: {err}")

    # Gerenciador do botão "Voltar" (Android)
    def view_pop(e):
        if len(page.views) > 1:
            page.views.pop()
            top_view = page.views[-1]
            page.go(top_view.route)

    # Atribuição dos eventos
    page.on_route_change = route_change
    page.on_view_pop = view_pop

    # 3. INICIALIZAÇÃO DO SISTEMA
    try:
        # Inicializa o Banco Local
        await Database.init_db()
        
        # Inicia na rota inicial
        page.go("/")
        
        # Verificação de Updates (em segundo plano para não travar o início)
        try:
            updater = AppUpdater(page)
            await updater.check_for_updates()
        except Exception as up_err:
            print(f"Aviso Updater: {up_err}")
        
    except Exception as e:
        print(f"Erro crítico na inicialização: {e}")

# Execução do Aplicativo
if __name__ == "__main__":
    ft.app(target=main)