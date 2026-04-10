import flet as ft

def montar_menu(page: ft.Page, *args, **kwargs):
    perfil = getattr(page, "user_email", "Operador")

    # Criamos os controles diretamente em uma lista
    meu_conteudo = [
        ft.Container(height=50), # Espaço para não bater no topo
        ft.Icon("water_drop", size=80, color="#2196F3"),
        ft.Text(f"Bem-vindo, {perfil}", size=20, weight="bold", color="white"),
        ft.Container(height=30),
        
        ft.ElevatedButton(
            content=ft.Text("GERAR QR CODES", weight="bold"),
            icon="qr_code",
            on_click=lambda _: page.go("/qrcodes"),
            width=300,
            height=60,
            style=ft.ButtonStyle(bgcolor="#2196F3", color="white")
        ),
        
        ft.Container(height=10),
        
        ft.ElevatedButton(
            content=ft.Text("SAIR"),
            icon="logout",
            on_click=lambda _: page.go("/login"),
            width=300,
            height=60,
            style=ft.ButtonStyle(color="#FF5252")
        ),
    ]

    # Retornamos a View usando uma Column simples SEM expand
    return ft.View(
        route="/menu",
        controls=[
            ft.AppBar(
                title=ft.Text("AguaFlow - Menu Principal"),
                bgcolor="#1A1C1E",
                center_title=True
            ),
            ft.Column(
                controls=meu_conteudo,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                scroll=ft.ScrollMode.AUTO # Isso substitui o ListView com segurança
            )
        ],
        bgcolor="#121417"
    )