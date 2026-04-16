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
    # Inicializa o banco local de forma segura em uma thread separada
    try:
        await asyncio.to_thread(Database.init_db)
    except Exception as e:
        print(f"[DATABASE] Erro na inicialização: {e}")
    
    page.title = "AguaFlow - Gestão Vivere Prudente"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#121212"
    page.window_width = 400
    page.window_height = 700
    page.padding = 0
    page.spacing = 0

    # Instância única do botão de nuvem que gerencia o estado de sincronia
    botao_nuvem = BotaoSincronismo()

    async def route_change(e):
        try:
            # ESSENCIAL: Pequena pausa (0.4s) para o Flet estabilizar o ClientStorage e o Supabase
            # Isso resolve o erro de Timeout e RuntimeError: Event loop is closed
            await asyncio.sleep(0.4)
            
            page.views.clear()
            
            # Função para criar uma AppBar padronizada com o logo e botão de nuvem
            def criar_barra(titulo, mostrar_voltar=True):
                return ft.AppBar(
                    title=ft.Row([
                        # Logotipo da gota d'água (assets/logo.jpeg)
                        ft.Image(
                            src="assets/logo.jpeg", 
                            width=30, 
                            height=30, 
                            border_radius=15,
                            error_content=ft.Icon(ft.icons.WATER_DROP, color="blue")
                        ),
                        ft.Text(titulo, size=20, weight="bold")
                    ], alignment=ft.MainAxisAlignment.CENTER, spacing=10, tight=True),
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

            # --- ROTEAMENTO E MAPEAMENTO DE TELAS ---
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
                view = montar_tela_dashboard_saude(page, lambda _: page.go("/menu"))
                view.appbar = criar_barra("Saúde do Sistema")
                page.views.append(view)
            
            elif page.route == "/configuracoes":
                view = montar_tela_configs(page, lambda _: page.go("/menu"))
                view.appbar = criar_barra("Configurações")
                page.views.append(view)
            
            elif page.route == "/ajuda":
                # Rota de Suporte Técnico corrigida para voltar para configurações
                view = montar_tela_ajuda(page, lambda _: page.go("/configuracoes"))
                view.appbar = criar_barra("Suporte Técnico")
                page.views.append(view)
            
            elif page.route == "/recuperar_senha":
                page.views.append(criar_tela_recuperacao(page))

            page.update()
            
        except Exception as err:
            print(f"[ROTA] Erro crítico ao mudar para {page.route}: {err}")

    # Configura o evento de mudança de rota
    page.on_route_change = route_change
    
    # Inicializa o aplicativo na rota inicial
    page.go(page.route)

if __name__ == "__main__":
    # Garante que o Flet saiba onde buscar as imagens na pasta assets
    try:
        ft.app(target=main, assets_dir="assets")
    except RuntimeError:
        # Previne erro de encerramento de loop no Python 3.14
        pass