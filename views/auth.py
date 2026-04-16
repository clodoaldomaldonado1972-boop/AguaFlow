import flet as ft
import asyncio
import os
from supabase import create_client, Client
from dotenv import load_dotenv
import views.styles as st 

# 1. CARREGAMENTO DAS VARIÁVEIS
load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

if url and key:
    supabase: Client = create_client(url, key)
else:
    print("⚠️ Aviso: Supabase não configurado no auth.py")

def criar_tela_login(page: ft.Page):
    # Campos de entrada
    txt_user = st.campo_estilo("E-mail Real", ft.icons.PERSON)
    txt_pass = st.campo_estilo("Sua Senha", ft.icons.LOCK, password=True)
    lbl_erro = ft.Text("", color="red", size=12, weight=ft.FontWeight.BOLD)

    async def realizar_login(e):
        lbl_erro.value = ""
        lbl_erro.visible = False
        page.update()

        email_input = txt_user.value.strip().lower()
        senha_input = txt_pass.value

        if not email_input or not senha_input:
            lbl_erro.value = "Preencha todos os campos!"
            lbl_erro.visible = True
            page.update()
            return

        try:
            # Tenta autenticação real no Supabase
            auth_response = supabase.auth.sign_in_with_password({
                "email": email_input,
                "password": senha_input
            })

            if auth_response.user:
                # Verifica se é você (Admin) ou um novo usuário
                # No Supabase, você pode definir 'role' nos metadados do usuário
                user_metadata = auth_response.user.user_metadata
                role = user_metadata.get("role", "user") 

                # Armazena os dados na sessão do Flet
                page.session.set("user_email", auth_response.user.email)
                page.session.set("user_role", role)

                print(f"DEBUG: Login realizado com sucesso. Role: {role}")
                page.go("/menu")

        except Exception as ex:
            lbl_erro.value = "E-mail ou senha incorretos."
            lbl_erro.visible = True
            print(f"Erro de login: {ex}")
            page.update()

    # --- FUNÇÃO DE CADASTRO PARA NOVOS USUÁRIOS ---
    async def abrir_cadastro(e):
        # Campos para a tela de cadastro
        novo_email = st.campo_estilo("E-mail Real", ft.icons.EMAIL)
        nova_senha = st.campo_estilo("Crie sua Senha", ft.icons.LOCK, password=True)
        btn_registrar = ft.ElevatedButton("CADASTRAR E ENTRAR", width=320, height=50, style=st.BTN_MAIN)
        
        def fechar_bs(e):
            bs.open = False
            page.update()

        async def processar_registro(e):
            try:
                # Cria o usuário no Supabase com e-mail real e senha
                # Passamos 'role': 'user' para diferenciar do Admin
                res = supabase.auth.sign_up({
                    "email": novo_email.value.strip().lower(),
                    "password": nova_senha.value,
                    "options": {"data": {"role": "user"}}
                })
                
                if res.user:
                    bs.open = False
                    page.snack_bar = ft.SnackBar(ft.Text("Cadastro realizado! Faça login agora."))
                    page.snack_bar.open = True
                    page.update()
            except Exception as ex:
                print(f"Erro no cadastro: {ex}")

        btn_registrar.on_click = processar_registro

        bs = ft.BottomSheet(
            ft.Container(
                padding=20,
                content=ft.Column([
                    ft.Text("Crie sua Conta no ÁguaFlow", size=20, weight="bold"),
                    novo_email,
                    nova_senha,
                    btn_registrar,
                    ft.TextButton("Cancelar", on_click=fechar_bs)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15, tight=True)
            ),
            open=True,
        )
        page.overlay.append(bs)
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
                    ft.Image(src="assets/logo.jpeg", width=120, height=120, border_radius=60),
                    ft.Text("AguaFlow", style=st.TEXT_TITLE),
                    ft.Text("Vivere Prudente", style=st.TEXT_SUB),
                    ft.Divider(height=20, color="transparent"),
                    txt_user,
                    txt_pass,
                    lbl_erro,
                    ft.Divider(height=10, color="transparent"),
                    ft.ElevatedButton("ENTRAR", on_click=realizar_login, width=320, height=50, style=st.BTN_MAIN),
                    
                    ft.Row([
                        ft.TextButton("Esqueci minha senha", on_click=lambda _: page.go("/recuperar_senha")),
                        ft.TextButton("Criar nova conta", on_click=abrir_cadastro),
                    ], alignment=ft.MainAxisAlignment.CENTER)
                    
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                padding=20,
            )
        ]
    )