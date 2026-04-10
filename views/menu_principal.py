import flet as ft


def montar_menu(page: ft.Page, *args, **kwargs):
    # Recupera o usuário ou define padrão
    perfil = getattr(page, "user_email", "Operador")

    # Criamos a coluna de botões
    conteudo_central = ft.Column(
        controls=[
            ft.Container(height=40),  # Espaçador superior
            ft.Icon("water_drop", size=100, color="#2196F3"),
            ft.Text(f"Olá, {perfil}", size=24, weight="bold", color="white"),
            ft.Text("O que deseja fazer hoje?", color="#B0B0B0"),
            ft.Container(height=30),

            # Botão 1: QR Codes
            ft.ElevatedButton(
                content=ft.Text("GERAR QR CODES", weight="bold"),
                icon="qr_code",
                on_click=lambda _: page.go("/qrcodes"),
                width=300,
                height=60,
                style=ft.ButtonStyle(bgcolor="#2196F3", color="white")
            ),

            ft.Container(height=10),

            # Botão 2: Sair
            ft.ElevatedButton(
                content=ft.Text("SAIR DO SISTEMA"),
                icon="logout",
                on_click=lambda _: page.go("/login"),
                width=300,
                height=60,
                style=ft.ButtonStyle(color="#FF5252")
            ),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )

    # Retornamos a View de forma plana (sem containers aninhados)
    return ft.View(
        route="/menu",
        controls=[
            ft.AppBar(
                title=ft.Text("AguaFlow - Menu Principal"),
                bgcolor="#1A1C1E",
                center_title=True
            ),
            # O ListView garante que o conteúdo apareça mesmo em telas pequenas
            ft.ListView(
                controls=[conteudo_central],
                expand=True,
                padding=20
            )
        ],
        bgcolor="#121417"
    )
