import flet as ft
import os
import sys
import warnings

# Garante que o Python encontre as pastas na raiz
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Importação do Banco de Dados
from database.database import Database

# --- 1. IMPORTAÇÃO DAS VIEWS (TELAS) ---
# Importamos o auth e o cliente supabase da pasta views
from views.auth import criar_tela_login, supabase 
from views.menu_principal import montar_menu
from views.medicao import montar_tela_medicao
from views.qrcodes_view import montar_tela_qrcodes
from views.relatorio_view import montar_tela_relatorio as montar_tela_relatorios
from views.configuracoes import montar_tela_configs

# Importação dos Dashboards
from views.dashboard import montar_tela_dashboard
from views.dashboard_saude import montar_tela_saude

# IMPORTAÇÃO DAS NOVAS ROTAS DE SENHA
from views.recuperar_senha_email import criar_tela_recuperacao
from views.reset_password_view import reset_password_view

# Ignorar avisos de depreciação do Flet para o vídeo ficar limpo
warnings.filterwarnings("ignore", category=DeprecationWarning)

async def main(page: ft.Page):
    # --- 2. CONFIGURAÇÕES GERAIS ---
    page.title = "AguaFlow - Gestão de Consumo"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 400
    page.window_height = 750
    
    # Variáveis de sessão
    page.logado = False
    page.user_email = None

    # Picker de ficheiros para relatórios
    file_picker = ft.FilePicker()
    page.overlay.append(file_picker)
    page.file_picker = file_picker 

    def route_change(e):
        page.views.clear()
        
        # Rota Raiz / Login
        if page.route == "/login" or page.route == "/":
            page.views.append(criar_tela_login(page))
            
        # --- NOVAS ROTAS DE AUTENTICAÇÃO ---
        elif page.route == "/recuperar-email":
            page.views.append(criar_tela_recuperacao(page))
            
        elif page.route == "/reset-password":
            page.views.append(reset_password_view(page))
            
        # --- ROTAS DO SISTEMA (PROTEGIDAS) ---
        elif page.route == "/menu":
            if not page.logado:
                page.go("/login")
            else:
                page.views.append(montar_menu(page))
                
        elif page.route == "/medicao":
            page.views.append(montar_tela_medicao(page))
            
        elif page.route == "/qrcodes":
            page.views.append(montar_tela_qrcodes(page))
            
        elif page.route == "/relatorios":
            page.views.append(montar_tela_relatorios(page, lambda _: page.go("/menu")))
            
        elif page.route == "/dashboard":
            page.views.append(montar_tela_dashboard(page, lambda _: page.go("/menu")))
            
        elif page.route == "/dashboard_saude":
            page.views.append(montar_tela_saude(page, lambda _: page.go("/menu")))
            
        elif page.route == "/configuracoes":
            page.views.append(montar_tela_configs(page, lambda _: page.go("/menu")))
        
        page.update()

    async def view_pop(e):
        if len(page.views) > 1:
            page.views.pop()
            top_view = page.views[-1]
            page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    
    # Inicia na rota atual
    page.go(page.route)

if __name__ == "__main__":
    # Define a pasta de assets para carregar a logo.jpeg
    ft.app(target=main, assets_dir="assets")