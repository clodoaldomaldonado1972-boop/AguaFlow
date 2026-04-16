import flet as ft
import os
import sys
import warnings

# Garante que o Python encontre as pastas na raiz do projeto
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# --- IMPORTAÇÕES DAS VIEWS ---
from database.database import Database
from views.auth import criar_tela_login
from views.autenticacao import montar_tela_autenticacao # NOVA ROTA
from views.menu_principal import montar_menu
from views.medicao import montar_tela_medicao
from views.qrcodes_view import montar_tela_qrcodes
from views.relatorio_view import montar_tela_relatorio
from views.configuracoes import montar_tela_configs
from views.dashboard import montar_tela_dashboard
from views.dashboard_saude import montar_tela_saude 
from views.recuperar_senha_email import criar_tela_recuperacao
from views.reset_password_view import reset_password_view
from views.ajuda_view import montar_tela_ajuda

# Configurações de sistema
warnings.filterwarnings("ignore", category=UserWarning)
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

async def main(page: ft.Page):
    # Inicializa o Banco de Dados Local (SQLite)
    Database.init_db()
    
    page.title = "AguaFlow - Gestão Vivere Prudente"
    
    # --- CONFIGURAÇÃO DE TEMA DARK (BLACK) ---
    page.theme_mode = ft.ThemeMode.DARK  # Força o modo escuro em todo o app
    page.bgcolor = "#121212"            # Fundo preto profundo para destaque profissional
    
    page.window_width = 400
    page.window_height = 700
    
    # Configurações de navegação e layout
    page.padding = 0
    page.spacing = 0

    def route_change(e):
        page.views.clear()
        
        # 1. TELA DE LOGIN (INICIAL)
        if page.route == "/" or page.route == "/login":
            page.views.append(criar_tela_login(page))

        # 2. RECUPERAÇÃO DE SENHA
        elif page.route == "/recuperar_senha":
            page.views.append(criar_tela_recuperacao(page))

        # 3. AUTENTICAÇÃO/VERIFICAÇÃO
        elif page.route == "/autenticacao":
            page.views.append(montar_tela_autenticacao(page))

        # 4. MENU PRINCIPAL
        elif page.route == "/menu":
            page.views.append(montar_menu(page))

        # 5. OPERAÇÕES DE CAMPO (OCR E QR CODE)
        elif page.route == "/medicao":
            page.views.append(montar_tela_medicao(page, lambda _: page.go("/menu")))

        elif page.route == "/qrcodes":
            page.views.append(montar_tela_qrcodes(page, lambda _: page.go("/menu")))

        # 6. RELATÓRIOS E DASHBOARDS
        elif page.route == "/relatorios":
            page.views.append(montar_tela_relatorio(page, lambda _: page.go("/menu")))
            
        elif page.route == "/dashboard":
            page.views.append(montar_tela_dashboard(page, lambda _: page.go("/menu")))

        elif page.route == "/dashboard_saude":
            page.views.append(montar_tela_saude(page, lambda _: page.go("/menu")))

        # 7. CONFIGURAÇÕES E AJUDA
        elif page.route == "/configuracoes":
            page.views.append(montar_tela_configs(page, lambda _: page.go("/menu")))

        elif page.route == "/ajuda":
            page.views.append(montar_tela_ajuda(page, lambda _: page.go("/configuracoes")))
            
        elif page.route == "/reset-password":
            page.views.append(reset_password_view(page))

        page.update()

    def view_pop(e):
        if len(page.views) > 1:
            page.views.pop()
            top_view = page.views[-1]
            page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    
    # Início do App
    page.go(page.route)

# Execução do Aplicativo
if __name__ == "__main__":
    # O uso do ft.app(target=main) no Flet moderno gerencia o loop de eventos automaticamente
    ft.app(target=main)