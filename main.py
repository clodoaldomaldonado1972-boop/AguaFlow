import flet as ft
from views.auth import criar_tela_login
# Importe as outras views conforme for criando
# from views.menu_principal import criar_menu
from database.database import Database


async def main(page: ft.Page):
    # 1. Configurações Iniciais
    page.title = "AguaFlow - Vivere Prudente"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 400
    page.window_height = 800
    page.window_resizable = False  # Mantém o aspecto de app mobile

    # 2. Inicializa o Banco de Dados Local
    Database.init_db()

    def rota_mudou(e):
        page.views.clear()

        # Rota de Login
        if page.route == "/" or page.route == "/login":
            page.views.append(
                criar_tela_login(page, lambda _: page.go("/menu"))
            )

        # Rota do Menu (Exemplo de como expandir)
        elif page.route == "/menu":
            # page.views.append(criar_menu(page))
            pass

        page.update()

    def view_pop(e):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = rota_mudou
    page.on_view_pop = view_pop  # Lida com o botão "voltar" do sistema/navegador

    page.go("/")

if __name__ == "__main__":
    # Para o desenvolvimento no VS Code, o AppView.FLET_APP costuma ser melhor
    # para simular o celular, mas WEB_BROWSER é ótimo para testes rápidos.
    ft.app(target=main)
