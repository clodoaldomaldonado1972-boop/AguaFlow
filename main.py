import flet as ft
from database.database import Database
from views.auth import criar_tela_login
from views.menu_principal import montar_menu
from views.medicao import montar_tela_medicao
from views.qrcodes_view import montar_tela_qrcodes
from views.relatorios import montar_tela_relatorios
from views.configuracoes import montar_tela_configs

async def main(page: ft.Page):
    # 1. REGISTRO DO FILEPICKER
    file_picker = ft.FilePicker()
    page.overlay.append(file_picker)
    page.file_picker = file_picker 
    
    # --- 2. CONFIGURAÇÕES ---
    page.title = "AguaFlow - Vivere Prudente"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 400
    page.window_height = 700

    # Inicializa o banco SQLite
    Database.init_db()

    # --- 3. GERENCIADOR DE ROTAS ---
    async def rota_mudou(e):
        page.views.clear()
        
        if page.route == "/login" or page.route == "/":
            page.views.append(criar_tela_login(page))
        elif page.route == "/menu":
            page.views.append(montar_menu(page))
        elif page.route == "/medicao":
            page.views.append(montar_tela_medicao(page))
        elif page.route == "/qrcodes":
            page.views.append(montar_tela_qrcodes(page))
        elif page.route == "/relatorios":
            page.views.append(montar_tela_relatorios(page, lambda _: page.push_route("/menu")))
        elif page.route == "/configuracoes":
            page.views.append(montar_tela_configs(page, lambda _: page.push_route("/menu")))
        
        # AJUSTE: Remova o 'await' do update
        page.update()

    page.on_route_change = rota_mudou

# --- 4. NAVEGAÇÃO INICIAL ---
    # push_route PRECISA de await para a tela carregar
    await page.push_route("/login")
    
    # update NÃO PRECISA de await nas versões novas (0.80+)
    page.update()

if __name__ == "__main__":
    # O aviso de 'app()' ser antigo não impede o funcionamento, 
    # pode manter assim para garantir os assets.
    ft.run(main, assets_dir="assets")