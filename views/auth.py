import flet as ft
import asyncio
# --- IMPORT DOS ESTILOS UNIFICADOS ---
from views import styles as st


def criar_tela_login(page: ft.Page):
    # Campos de entrada usando os estilos padronizados
    txt_user = st.campo_estilo("Usuário", ft.Icons.PERSON)
    txt_pass = st.campo_estilo("Senha", ft.Icons.LOCK, password=True)
    lbl_erro = ft.Text("", color=st.ERROR_COLOR, size=14)

    async def realizar_login(e):
        print("DEBUG: Tentativa de login iniciada")

        # Simulação de autenticação (Pode ser conectada ao Database futuramente)
        if txt_user.value == "admin" and txt_pass.value == "123":
            # 1. Define as credenciais na sessão da página
            page.user_email = "operador@aguaflow.com"
            page.logado = True

            # 2. Muda a rota e navega
            page.go("/menu")
        else:
            lbl_erro.value = "Usuário ou senha incorretos!"
            page.update()

    # Layout da View de Login
    return ft.View(
        route="/login",
        bgcolor=st.BG_DARK,
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Container(
                content=ft.Column([
                    # Logotipo (Agora buscando da pasta assets da raiz)
                    ft.Image(
                        src="logo.jpeg",
                        width=150,
                        height=150,
                        border_radius=75
                    ),
                    ft.Text("AguaFlow", style=st.TEXT_TITLE),
                    ft.Text("Vivere Prudente", style=st.TEXT_SUB),

                    ft.Divider(height=20, color="transparent"),

                    txt_user,
                    txt_pass,
                    lbl_erro,

                    ft.Divider(height=10, color="transparent"),

                    ft.ElevatedButton(
                        "ENTRAR",
                        on_click=realizar_login,
                        width=320,
                        height=50,
                        style=st.BTN_MAIN
                    ),

                    ft.TextButton(
                        "Esqueci minha senha",
                        style=ft.ButtonStyle(color=st.GREY)
                    )
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                padding=20,
            )
        ]
    )
