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

warnings.filterwarnings("ignore", category=DeprecationWarning)


async def main(page: ft.Page):
    # --- CONFIGURAÇÕES BÁSICAS ---
    page.title = "AguaFlow - Vivere Prudente"
    page.bgcolor = "#121417"
    page.window_width = 400
    page.window_height = 700
    page.theme_mode = ft.ThemeMode.DARK

    # Inicializa o banco de dados
    Database.init_db()

    # ESTA FUNÇÃO DEVE ESTAR EXATAMENTE 4 ESPAÇOS PARA DENTRO DO main
    async def rota_mudou(e):
        print(f"DEBUG: Rota solicitada -> {page.route}")

        # Limpa as views para evitar sobreposição
        page.views.clear()

        # Verifica autenticação
        user_email = getattr(page, "user_email", None)

        # --- CONTROLE DE ROTAS ---
        if page.route == "/login" or page.route == "/":
            page.views.append(criar_tela_login(page))

        elif page.route == "/menu":
            if not user_email:
                page.go("/login")
                return
            # Chamada blindada (certifique-se que o menu_principal use *args)
            page.views.append(montar_tela_menu(page))

        elif page.route == "/medicao":
            if not user_email:
                page.go("/login")
                return
            page.views.append(montar_tela_medicao(page))

        elif page.route == "/qrcodes":
            if not user_email:
                page.go("/login")
                return
            page.views.append(montar_tela_qrcodes(page))

        # O page.update() deve estar dentro da rota_mudou, no final
        page.update()

    # ESTES EVENTOS TAMBÉM ALINHADOS COM O INÍCIO DO rota_mudou
    def view_pop(e):
        if len(page.views) > 1:
            page.views.pop()
            top_view = page.views[-1]
            page.go(top_view.route)

    page.on_route_change = rota_mudou
    page.on_view_pop = view_pop

    # Inicia na rota de login
    page.go("/login")

# --- INICIALIZAÇÃO DO APP ---
if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")
