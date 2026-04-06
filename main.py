import flet as ft
import warnings
import asyncio
from database.database import Database

# Imports das suas views (Certifique-se que os arquivos existem nas pastas)
from views.auth import criar_tela_login
from views.menu_principal import montar_menu as montar_tela_menu
from views.medicao import montar_tela_medicao
from views.dashboard import montar_tela_dashboard
from views.relatorios import montar_tela_relatorios

warnings.filterwarnings("ignore", category=DeprecationWarning)

def main(page: ft.Page):
    page.title = "AguaFlow - Vivere Prudente"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 400
    page.window_height = 700

    # Inicializa o banco de dados SQLite
    Database.init_db()

    # --- HANDLERS (Ações dos botões) ---
    async def gerar_pdf_handler(e):
        page.snack_bar = ft.SnackBar(ft.Text("Gerando PDF..."))
        page.snack_bar.open = True
        page.update()

    async def sync_nuvem_handler(e):
        page.snack_bar = ft.SnackBar(ft.Text("Sincronizando com a nuvem..."))
        page.snack_bar.open = True
        page.update()

    # --- LÓGICA DE NAVEGAÇÃO ---
    def rota_mudou(e):
        page.overlay.clear()
        page.views.clear()

        # Verifica se está logado usando o atributo dinâmico que criamos
        is_logado = getattr(page, "logado", False)

        if not is_logado and page.route not in ["/", "/login"]:
            page.go("/")
            return

        # 1. ROTA: LOGIN
        if page.route == "/" or page.route == "/login":
            page.views.append(criar_tela_login(page, lambda: page.go("/menu")))

        # 2. ROTA: MENU PRINCIPAL
        elif page.route == "/menu":
            # Criar view segura para v0.84.0
            view = ft.View("/menu", vertical_alignment=ft.MainAxisAlignment.START)
            view.controls.extend([
                montar_tela_menu(
                    page,
                    ir_para_medicao=lambda _: page.go("/medicao"),
                    ir_para_relatorios=lambda _: page.go("/relatorios"),
                    ir_para_configs=lambda _: page.go("/configuracoes")
                )
            ])
            page.views.append(view)

        # 3. ROTA: MEDIÇÃO (Água/Gás)
        elif page.route == "/medicao":
            view = ft.View("/medicao")
            view.controls.extend([montar_tela_medicao(page)])
            page.views.append(view)

        # 4. ROTA: RELATÓRIOS E DASHBOARD
        elif page.route == "/relatorios":
            view = ft.View("/relatorios")
            view.controls.extend([
                montar_tela_relatorios(
                    page,
                    voltar=lambda _: page.go("/menu"),
                    gerar_e_enviar_pdf=gerar_pdf_handler,
                    sync_nuvem=sync_nuvem_handler,
                    gerar_qr=lambda _: print("Gerar QR")
                )
            ])
            page.views.append(view)

        page.update()

    # Configuração inicial de rotas
    page.on_route_change = rota_mudou
    page.go("/")

if __name__ == "__main__":
    ft.run(main) # Versão recomendada para v0.84.0