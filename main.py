import flet as ft
import os
import sys

# Garante que o Python encontre as pastas
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# IMPORTAÇÃO DO BANCO (Essa é a linha que falta!)
from database.database import Database

# --- 1. IMPORTAÇÃO DE TODAS AS VIEWS (TELAS) ---
from views.auth import criar_tela_login
from views.menu_principal import montar_menu
from views.medicao import montar_tela_medicao
from views.qrcodes_view import montar_tela_qrcodes
# Note a correção do nome da função 'montar_tela_relatorio'
from views.relatorio_view import montar_tela_relatorio as montar_tela_relatorios
# Certifique-se que o nome aqui bate com o arquivo na pasta views
from views.configuracoes import montar_tela_configs

# Importação dos novos Dashboards
from views.dashboard import montar_tela_dashboard
from views.dashboard_saude import montar_tela_saude

async def main(page: ft.Page):
    # --- 2. REGISTRO DE UTILITÁRIOS ---
    # O FilePicker é essencial para selecionar fotos ou salvar relatórios
    file_picker = ft.FilePicker()
    page.overlay.append(file_picker)
    page.file_picker = file_picker 
    
    # --- 3. CONFIGURAÇÕES GERAIS DA JANELA ---
    page.title = "AguaFlow - Vivere Prudente"
    page.theme_mode = ft.ThemeMode.DARK
    
    # Dimensões simulando um smartphone (evita quebra de layout)
    page.window_width = 400
    page.window_height = 700
    page.window_resizable = False # Mantém o layout estável para a apresentação

    # Inicializa o banco SQLite local
    Database.init_db()

    # --- 4. GERENCIADOR DE ROTAS (O CORAÇÃO DO APP) ---
    async def rota_mudou(e):
        """Função disparada toda vez que page.go() é chamado"""
        page.views.clear()
        
        # Rota Inicial / Login
        if page.route == "/login" or page.route == "/":
            page.views.append(criar_tela_login(page))
            
        # Menu Principal (Hub central)
        elif page.route == "/menu":
            page.views.append(montar_menu(page))
            
        # Operação de Medição (OCR/Câmera)
        elif page.route == "/medicao":
            page.views.append(montar_tela_medicao(page))
            
        # Logística de QR Codes
        elif page.route == "/qrcodes":
            page.views.append(montar_tela_qrcodes(page))
            
        # Relatórios (Geração de PDF e envio de E-mail)
        # Relatórios (Geração de PDF e envio de E-mail)
        elif page.route == "/relatorios":
            # Certifique-se de que montar_tela_relatorios (que é o seu alias) 
            # está recebendo os argumentos corretos.
            page.views.append(montar_tela_relatorios(page, lambda _: page.go("/menu")))
            
        # Dashboard de Consumo (Gráficos)
        elif page.route == "/dashboard":
            page.views.append(montar_tela_dashboard(page, lambda _: page.go("/menu")))
            
        # Dashboard de Saúde (Status de Rede e Banco)
        elif page.route == "/dashboard_saude":
            page.views.append(montar_tela_saude(page, lambda _: page.go("/menu")))
            
        # Configurações do Sistema e Reset
        elif page.route == "/configuracoes":
            page.views.append(montar_tela_configs(page, lambda _: page.go("/menu")))
        
        page.update()

    # Função para gerenciar o botão 'Voltar' físico do Android ou do navegador
    async def view_pop(e):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = rota_mudou
    page.on_view_pop = view_pop

    # --- 5. INICIALIZAÇÃO ---
    # Define a rota inicial e renderiza a primeira tela
    page.go("/menu")

if __name__ == "__main__":
    ft.app(target=main)