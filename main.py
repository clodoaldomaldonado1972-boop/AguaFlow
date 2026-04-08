import flet as ft
import warnings
from database.database import Database

# --- NOVOS IMPORTS DE ACORDO COM A ESTRUTURA ---
from views.auth import criar_tela_login
from views.menu_principal import montar_menu as montar_tela_menu
from views.medicao import montar_tela_medicao
from views.relatorios import montar_tela_relatorios
from views.dashboard_saude import montar_tela_saude
# Import da tela de configs que faltava
from views.configuracoes import montar_tela_configs

# Ignora avisos de comandos que serão alterados em versões futuras do Flet
warnings.filterwarnings("ignore", category=DeprecationWarning)


async def main(page: ft.Page):
    # --- CONFIGURAÇÕES BÁSICAS ---
    page.title = "AguaFlow - Vivere Prudente"
    page.bgcolor = "#121417"
    page.window_width = 400
    page.window_height = 700
    page.theme_mode = ft.ThemeMode.DARK

    # --- IMPORTANTE: CONFIGURAÇÃO DE IMAGENS ---
    # Isso diz ao Flet para procurar logos e fotos na pasta assets da raiz
    # page.assets_dir = "assets"  <-- Se você rodar pelo terminal use isto
    # Ou na chamada do app lá embaixo (ft.app)

    # Inicializa o banco de dados SQLite local
    Database.init_db()

    async def rota_mudou(e):
        # LOG de depuração para o terminal
        print(f"DEBUG: Rota solicitada -> {page.route}")

        # Limpa a pilha de visualização para evitar sobreposição de telas
        page.views.clear()

        # Verifica se o usuário está autenticado
        user_email = getattr(page, "user_email", None)

        # --- CONTROLE DE ROTAS ---

        # 1. TELA DE LOGIN
        if page.route == "/login" or page.route == "/":
            page.views.append(criar_tela_login(page))

        # 2. MENU PRINCIPAL
        elif page.route == "/menu":
            if not user_email:
                page.go("/login")
                return

            view_menu = montar_tela_menu(
                page,
                ir_para_leitura=lambda _: page.go("/medicao"),
                ir_para_relatorios=lambda _: page.go("/relatorios"),
                ir_para_configs=lambda _: page.go("/configuracoes")
            )
            page.views.append(view_menu)

        # 3. TELA DE MEDIÇÃO
        elif page.route == "/medicao":
            if not user_email:
                page.go("/login")
                return
            page.views.append(montar_tela_medicao(page))

        # 4. TELA DE RELATÓRIOS
        elif page.route == "/relatorios":
            if not user_email:
                page.go("/login")
                return
            page.views.append(
                montar_tela_relatorios(page, voltar=lambda _: page.go("/menu"))
            )

        # 5. TELA DE CONFIGURAÇÕES
        elif page.route == "/configuracoes":
            if not user_email:
                page.go("/login")
                return
            page.views.append(
                montar_tela_configs(page, voltar=lambda _: page.go("/menu"))
            )

        # 6. DASHBOARD DE SAÚDE
        elif page.route == "/dashboard_saude":
            if not user_email:
                page.go("/login")
                return
            # Agora redireciona corretamente voltando para configurações
            page.views.append(
                montar_tela_saude(
                    page, voltar=lambda _: page.go("/configuracoes"))
            )

        page.update()

    def view_pop(e):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = rota_mudou
    page.on_view_pop = view_pop

    # Inicia na rota de login
    page.go("/login")


# --- INICIALIZAÇÃO DO APP ---
if __name__ == "__main__":
    # Aqui definimos a pasta assets para o Flet encontrar suas fotos
    ft.app(target=main, assets_dir="assets")
