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
    page.theme_mode = ft.ThemeMode.DARK
    
    # Função para gerenciar a mudança de telas (Rotas)
    async def route_change(route):
        page.views.clear()
        
        # 1. TELA DE LOGIN (Porta de Entrada)
        if page.route == "/" or page.route == "/login":
            page.views.append(criar_tela_login(page))

        # 2. TELA DE CADASTRO LOCAL (Nova Rota solicitada)
        elif page.route == "/cadastrar":
            page.views.append(montar_tela_autenticacao(page))

        # 3. MENU PRINCIPAL
        elif page.route == "/menu":
            page.views.append(montar_menu(page))

        # 4. MEDIÇÃO (Leitura de QR Codes/Câmera)
        elif page.route == "/medicao":
            page.views.append(montar_tela_medicao(page, lambda _: page.go("/menu")))

        # 5. GERADOR DE ETIQUETAS (Ajustado para 4x4 e sem UNID)
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

        # 8. RECUPERAÇÃO DE SENHA (Caminhos existentes)
        elif page.route == "/recuperar_senha":
            page.views.append(criar_tela_recuperacao(page))
            
        elif page.route == "/reset-password":
            page.views.append(reset_password_view(page))

        page.update()

    async def view_pop(view):
        if len(page.views) > 1:
            page.views.pop()
            top_view = page.views[-1]
            page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    
    # Inicializa na rota atual
    await page.go_async(page.route)

if __name__ == "__main__":
    ft.app(target=main)