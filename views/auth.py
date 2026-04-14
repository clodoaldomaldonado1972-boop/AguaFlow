import flet as ft
import asyncio
import os
from supabase import create_client, Client
from dotenv import load_dotenv
# Importação do estilo que está na mesma pasta
import views.styles as st 

# 1. CARREGAMENTO DAS VARIÁVEIS (Subindo uma pasta para achar o .env.txt na raiz)
env_path = os.path.join(os.path.dirname(__file__), "..", ".env.txt")
load_dotenv(env_path)

# 2. INICIALIZAÇÃO DO CLIENTE SUPABASE
url: str = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
key: str = os.getenv("NEXT_PUBLIC_SUPABASE_PUBLISHABLE_DEFAULT_KEY")
supabase: Client = create_client(url, key)

def criar_tela_login(page: ft.Page):
    # Credenciais Administrativas do .env.txt
    USUARIO_CORRETO = os.getenv("EMAIL_USER")
    SENHA_CORRETA = os.getenv("EMAIL_PASS")
    # No componente de texto ou botão de "Esqueci minha senha"
    ft.TextButton(
        "Esqueci minha senha",
        on_click=lambda _: page.go("/recuperar_senha") # <--- O comando vital
    )

    # Campos de entrada
    txt_user = st.campo_estilo("E-mail", ft.icons.PERSON)
    txt_pass = st.campo_estilo("Senha", ft.icons.LOCK, password=True)
    lbl_erro = ft.Text("", color=st.ERROR_COLOR, size=14)

    async def realizar_login(e):
        print("DEBUG: Iniciando validação de acesso...")
        
        if txt_user.value == USUARIO_CORRETO and txt_pass.value == SENHA_CORRETA:
            page.user_email = USUARIO_CORRETO
            page.logado = True
            # Navega para o menu após sucesso
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
                    # Logotipo
                    ft.Image(
                        src="assets/logo.jpeg",
                        width=120,
                        height=120,
                        border_radius=60
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
                        style=ft.ButtonStyle(color=st.GREY),
                        # Ação que faltava: leva para a tela de recuperação por e-mail
                        on_click=lambda _: page.go("/recuperar-email")
                    )
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                padding=20,
            )
        ]
    )