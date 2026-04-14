import flet as ft
import os
import sys
import warnings

# Garante que o Python encontre as pastas na raiz do projeto
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from database.database import Database
from views.auth import criar_tela_login
from views.menu_principal import montar_menu
from views.medicao import montar_tela_medicao
from views.qrcodes_view import montar_tela_qrcodes
from views.relatorio_view import montar_tela_relatorio
from views.configuracoes import montar_tela_configs
from views.dashboard import montar_tela_dashboard
from views.dashboard_saude import montar_tela_saude 
from views.recuperar_senha_email import criar_tela_recuperacao
from views.reset_password_view import reset_password_view

# Silencia avisos do Torch e do Python
warnings.filterwarnings("ignore", category=UserWarning)
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE" # Evita crash em algumas CPUs

async def main(page: ft.Page):
    # Inicializa o Banco de Dados Local (SQLite)
    Database.init_db()
    
    # Configurações iniciais da página
    page.title = "AguaFlow - Gestão de Consumo"
    page.theme_mode = ft.ThemeMode.DARK
    page.logado = False  # Estado de autenticação inicial

    async def route_change(route):
        """Gerenciador de Rotas: Decide qual tela carregar baseada na URL."""
        page.views.clear()
        
        # 1. LOGIN
        if page.route == "/":
            page.views.append(criar_tela_login(page))
            
        # 2. RECUPERAÇÃO
        elif page.route == "/recuperar":
            page.views.append(criar_tela_recuperacao(page))

        # 3. MENU PRINCIPAL
        elif page.route == "/menu":
            if not page.logado:
                page.go("/")
            else:
                page.views.append(montar_menu(page))
                
        # 4. MEDIÇÃO / SCANNER
        elif page.route == "/medicao":
            page.views.append(montar_tela_medicao(page))
            
        # 5. QR CODES
        elif page.route == "/qrcodes":
            page.views.append(montar_tela_qrcodes(page))
            
        # 6. RELATÓRIOS
        elif page.route == "/relatorios":
            page.views.append(montar_tela_relatorio(page, lambda _: page.go("/menu")))
            
        # 7. DASHBOARD (Ajustado para evitar erro de sintaxe e duplicidade)
        elif page.route == "/dashboard":
            try:
                from views.dashboard import montar_tela_dashboard
                # Removemos qualquer linha solta anterior e deixamos apenas esta:
                page.views.append(montar_tela_dashboard(page, lambda _: page.go("/menu")))
            except Exception as e:
                print(f"Erro ao carregar Dashboard: {e}")
                page.go("/menu")

        # 8. DASHBOARD SAÚDE
        elif page.route == "/dashboard_saude":
            try:
                from views.dashboard_saude import montar_tela_saude
                view_saude = montar_tela_saude(page, lambda _: page.go("/menu"))
                page.views.append(view_saude)
            except Exception as e:
                print(f"Erro ao carregar Saúde: {e}")
                page.go("/menu")
            
        # 9. CONFIGURAÇÕES
        elif page.route == "/configuracoes":
            try:
                from views.configuracoes import montar_tela_configs
                page.views.append(montar_tela_configs(page, lambda _: page.go("/menu")))
            except Exception as e:
                print(f"Erro ao carregar Configurações: {e}")
                page.go("/menu")

        page.update()
        
    async def view_pop(view):
        """Gerencia o botão 'Voltar' do sistema."""
        if len(page.views) > 1:
            page.views.pop()
            top_view = page.views[-1]
            page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    
    # Inicia na rota atual
    page.go(page.route)

if __name__ == "__main__":
    ft.app(target=main)