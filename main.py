import flet as ft
import os
import sys
import warnings
import asyncio

# Garante que o Python encontre as pastas na raiz do projeto
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from database.database import Database
from utils.sync_interface import BotaoSincronismo

# --- IMPORTAÇÕES DAS VIEWS ---
from views.auth import criar_tela_login
from views.menu_principal import montar_menu
from views.medicao import montar_tela_medicao
from views.qrcodes_view import montar_tela_qrcodes
from views.relatorio_view import montar_tela_relatorio
from views.configuracoes import montar_tela_configs
from views.dashboard import montar_tela_dashboard
from views.dashboard_saude import montar_tela_saude 
from views.recuperar_senha_email import criar_tela_recuperacao
from views.ajuda_view import montar_tela_ajuda

# Suprime avisos técnicos
warnings.filterwarnings("ignore", category=UserWarning)
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

async def main(page: ft.Page):
    # Inicializa o banco local sem travar a UI
    await asyncio.to_thread(Database.init_db)
    
    page.title = "AguaFlow - Gestão Vivere Prudente"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#121212"
    page.window_width = 400
    page.window_height = 700
    page.padding = 0
    page.spacing = 0

    # Instância única do botão de nuvem
    botao_nuvem = BotaoSincronismo()

    async def route_change(e):
        try:
            # Pequeno delay para garantir que o ClientStorage esteja pronto
            # Isso resolve o erro de "Timeout waiting for invokeMethod"
            await asyncio.sleep(0.1)
            
            page.views.clear()
            
            def criar_barra(titulo, mostrar_voltar=True):
                return ft.AppBar(
                    title=ft.Text(titulo, size=20, weight="bold"),
                    center_title=True,
                    bgcolor="#1A1A1A",
                    leading=(
                        ft.IconButton(
                            icon=ft.icons.ARROW_BACK_IOS_NEW_ROUNDED,
                            on_click=lambda _: page.go("/menu"),
                            icon_size=20
                        ) if mostrar_voltar else None
                    ),
                    actions=[botao_nuvem]
                )

            # --- ROTEAMENTO ---
            if page.route == "/" or page.route == "/login":
                page.views.append(criar_tela_login(page))
            elif page.route == "/menu":
                view = montar_menu(page)
                view.appbar = criar_barra("AguaFlow", False)
                page.views.append(view)
            elif page.route == "/medicao":
                view = montar_tela_medicao(page, lambda _: page.go("/menu"))
                view.appbar = criar_barra("Medição")
                page.views.append(view)
            elif page.route == "/qrcodes":
                view = montar_tela_qrcodes(page, lambda _: page.go("/menu"))
                view.appbar = criar_barra("Gerar QR Codes")
                page.views.append(view)
            elif page.route == "/relatorios":
                view = montar_tela_relatorio(page, lambda _: page.go("/menu"))
                view.appbar = criar_barra("Relatórios")
                page.views.append(view)
            elif page.route == "/dashboard":
                view = montar_tela_dashboard(page, lambda _: page.go("/menu"))
                view.appbar = criar_barra("Consumo Mensal")
                page.views.append(view)
            elif page.route == "/dashboard_saude":
                view = montar_tela_saude(page, lambda _: page.go("/menu"))
                view.appbar = criar_barra("Saúde do Sistema")
                page.views.append(view)
            elif page.route == "/configuracoes":
                view = montar_tela_configs(page, lambda _: page.go("/menu"))
                view.appbar = criar_barra("Configurações")
                page.views.append(view)
            elif page.route == "/ajuda":
                view = montar_tela_ajuda(page, lambda _: page.go("/configuracoes"))
                view.appbar = criar_barra("Suporte Técnico")
                page.views.append(view)
            elif page.route == "/recuperar_senha":
                page.views.append(criar_tela_recuperacao(page))

            page.update()
        except Exception as err:
            print(f"Erro ao mudar rota: {err}")

    page.on_route_change = route_change
    
    # Inicialização segura
    page.go(page.route)

if __name__ == "__main__":
    # Rodar o app
    ft.app(target=main)