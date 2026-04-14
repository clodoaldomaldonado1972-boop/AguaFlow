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
from views.ajuda_view import montar_tela_ajuda

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
            
        # 2. RECUPERAÇÃO / ESQUECI MINHA SENHA
        elif page.route == "/recuperar_senha":
            try:
                page.views.append(criar_tela_recuperacao(page))
            except Exception as e:
                print(f"Erro ao carregar Recuperação: {e}")
                page.go("/")

        # 3. MENU PRINCIPAL
        elif page.route == "/menu":
            if not page.logado:
                page.go("/")
            else:
                page.views.append(montar_menu(page))
                
        # 4. MEDIÇÃO / SCANNER
        elif page.route == "/medicao":
            page.views.append(montar_tela_medicao(page))
            
        # 5. GERADOR DE QR CODE (Unificado e Corrigido)
        elif page.route == "/qrcodes":
            try:
                # Importação local para evitar dependência circular
                from views.qrcodes_view import montar_tela_qrcodes
                page.views.append(montar_tela_qrcodes(page, lambda _: page.go("/menu")))
            except Exception as e:
                print(f"ERRO NO QR CODE: {e}")
                page.go("/menu")

        # 6. RELATÓRIOS
        elif page.route == "/relatorios":
            page.views.append(montar_tela_relatorio(page, lambda _: page.go("/menu")))
            
        # 7. DASHBOARD
        elif page.route == "/dashboard":
            try:
                page.views.append(montar_tela_dashboard(page, lambda _: page.go("/menu")))
            except Exception as e:
                print(f"Erro ao carregar Dashboard: {e}")
                page.go("/menu")

        # 8. DASHBOARD SAÚDE
        elif page.route == "/dashboard_saude":
            try:
                page.views.append(montar_tela_saude(page, lambda _: page.go("/menu")))
            except Exception as e:
                print(f"Erro ao carregar Saúde: {e}")
                page.go("/menu")
            
        # 9. CONFIGURAÇÕES
        elif page.route == "/configuracoes":
            try:
                page.views.append(montar_tela_configs(page, lambda _: page.go("/menu")))
            except Exception as e:
                print(f"Erro ao carregar Configurações: {e}")
                page.go("/menu")

        # 10. GUIA MANUAL
        elif page.route == "/ajuda":
            try:
                page.views.append(montar_tela_ajuda(page, lambda _: page.go("/configuracoes")))
            except Exception as e:
                print(f"Erro ao carregar Ajuda: {e}")
                page.go("/configuracoes")

        page.update()

    # CORREÇÃO DE INDENTAÇÃO: Alinhado com o 'def route_change'
    async def view_pop(view):
        """Gerencia o botão 'Voltar' do sistema."""
        if len(page.views) > 1:
            page.views.pop()
            top_view = page.views[-1]
            page.route = top_view.route
            page.update()

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    
    page.go(page.route)

if __name__ == "__main__":
    ft.app(target=main)