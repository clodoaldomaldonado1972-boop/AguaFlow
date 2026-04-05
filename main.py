import flet as ft
from views.auth import criar_tela_login
# from database.database import Database # Comente por enquanto se for usar apenas Supabase na web

async def main(page: ft.Page):
    # 1. Configurações Iniciais
    page.title = "AguaFlow - Vivere Prudente"
    page.theme_mode = ft.ThemeMode.DARK
    
    # IMPORTANTE: Remova ou comente a linha abaixo para o Deploy no Vercel
    # Database.init_db() 

    # Configurações de janela (são ignoradas no navegador, mas boas para o mobile)
    page.window_width = 400
    page.window_height = 800

    def rota_mudou(e):
        page.views.clear()

        # Rota de Login
        if page.route == "/" or page.route == "/login":
            # Certifique-se que criar_tela_login retorna um objeto ft.View
            view_login = criar_tela_login(page, lambda _: page.go("/menu"))
            page.views.append(view_login)

        # Rota do Menu
        elif page.route == "/menu":
            page.views.append(
                ft.View(
                    "/menu",
                    [ft.AppBar(title=ft.Text("Menu Principal")), ft.Text("Bem-vindo ao AguaFlow!")]
                )
            )
        page.update()

    page.on_route_change = rota_mudou
    page.go(page.route) # Use a rota atual para evitar loops

if __name__ == "__main__":
    # Para o Vercel, o ideal é não usar o if __name__ == "__main__" para o ft.app
    # mas manter como está não costuma quebrar se o target estiver certo.
    ft.app(target=main)
