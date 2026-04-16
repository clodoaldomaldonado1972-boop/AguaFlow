import flet as ft
import asyncio
import os
from supabase import create_client, Client
from dotenv import load_dotenv
import views.styles as st 

# 1. CARREGAMENTO DAS VARIÁVEIS
env_path = os.path.join(os.path.dirname(__file__), "..", ".env.txt")
# No topo do auth.py, mude para:
load_dotenv() # Sem passar caminho fixo, ele busca na raiz

url = os.getenv("SUPABASE_URL") # Nome simplificado
key = os.getenv("SUPABASE_KEY") # Nome simplificado

if url and key:
    supabase: Client = create_client(url, key)
else:
    print("⚠️ Aviso: Supabase não configurado no auth.py")

def criar_tela_login(page: ft.Page):
    # Campos de entrada
    txt_user = st.campo_estilo("E-mail", ft.icons.PERSON)
    txt_pass = st.campo_estilo("Senha", ft.icons.LOCK, password=True)
    lbl_erro = ft.Text("", color="red", size=12, weight=ft.FontWeight.BOLD)

    async def realizar_login(e):
        lbl_erro.value = ""
        lbl_erro.visible = False
        page.update()

        if not txt_user.value or not txt_pass.value:
            lbl_erro.value = "Preencha todos os campos!"
            lbl_erro.visible = True
            page.update()
            return

        try:
            # 1. Tenta autenticar no Supabase
            auth_response = supabase.auth.sign_in_with_password({
                "email": txt_user.value,
                "password": txt_pass.value
            })

            if auth_response.user:
                # 2. IMPLEMENTAÇÃO DE NÍVEIS DE ACESSO
                # Busca o 'role' dentro dos metadados do usuário (padrão é 'user')
                user_metadata = auth_response.user.user_metadata
                role = user_metadata.get("role", "user")

                # Armazena o role na sessão da página para uso em outras telas
                page.session.set("user_role", role)
                page.session.set("user_email", auth_response.user.email)

                # 3. Lógica de Redirecionamento
                if role == "admin":
                    print(f"DEBUG: Admin {auth_response.user.email} logado.")
                    page.go("/menu") # Admin vai para o menu completo
                else:
                    print(f"DEBUG: Usuário comum {auth_response.user.email} logado.")
                    page.go("/menu") # Você pode criar uma rota /menu_operador se preferir

        except Exception as ex:
            lbl_erro.value = "E-mail ou senha incorretos."
            lbl_erro.visible = True
            print(f"Erro de login: {ex}")
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
                        on_click=lambda _: page.go("/recuperar_senha")
                    )
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                padding=20,
            )
        ]
    )