import flet as ft
import warnings
from database.database import Database

# --- IMPORTS DAS VIEWS ---
from views.auth import criar_tela_login
from views.menu_principal import montar_menu as montar_tela_menu
from views.medicao import montar_tela_medicao
from views.relatorios import montar_tela_relatorios
from views.configuracoes import montar_tela_configs
from views.qrcodes_view import montar_tela_qrcodes

# Silencia avisos de depreciação para manter o console limpo
warnings.filterwarnings("ignore", category=DeprecationWarning)

async def main(page: ft.Page):
    # --- CONFIGURAÇÕES BÁSICAS ---
    page.title = "AguaFlow - Vivere Prudente"
    page.bgcolor = "#121417"
    page.window_width = 400
    page.window_height = 700
    page.theme_mode = ft.ThemeMode.DARK

    # --- SOLUÇÃO PARA O ERRO "Unknown control: FilePicker" ---
    # Registra o FilePicker no overlay para remover a linha vermelha
    if not any(isinstance(c, ft.FilePicker) for c in page.overlay):
        picker = ft.FilePicker()
        page.overlay.append(picker)

    # Inicializa o banco de dados
    Database.init_db()

    # --- GERENCIADOR DE ROTAS ---
    async def rota_mudou(e):
        print(f"DEBUG: Rota solicitada -> {page.route}")

        # Limpa as views para evitar sobreposição e libertar RAM (8GB)
        page.views.clear()

        # 1. Tela de Login / Raiz
        if page.route == "/login" or page.route == "/":
            page.views.append(criar_tela_login(page))

        # 2. Menu Principal
        elif page.route == "/menu":
            # Trava de user_email removida temporariamente para garantir que os menus apareçam
            page.views.append(montar_tela_menu(page))

        # 3. Telas Secundárias
        elif page.route == "/medicao":
            page.views.append(montar_tela_medicao(page))

        elif page.route == "/relatorios":
            page.views.append(montar_tela_relatorios(page))

        elif page.route == "/configuracoes":
            page.views.append(montar_tela_configs(page))

        elif page.route == "/qrcodes":
            page.views.append(montar_tela_qrcodes(page))

        # Atualiza a página após as mudanças
        page.update()

    # --- FUNÇÃO VOLTAR ---
    async def view_pop(e):
        if len(page.views) > 1:
            page.views.pop()
            top_view = page.views[-1]
            page.go(top_view.route)

    # Vinculação dos eventos
    page.on_route_change = rota_mudou
    page.on_view_pop = view_pop

    # Inicia na rota de login
    page.go("/login")

# --- INICIALIZAÇÃO DO APP ---
if __name__ == "__main__":
    # Garante que as aspas e parênteses estão fechados corretamente
    ft.app(target=main, assets_dir="assets")