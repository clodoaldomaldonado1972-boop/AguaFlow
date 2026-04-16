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
    # Campos de entrada da tela principal
    txt_user = st.campo_estilo("E-mail Real", ft.icons.PERSON)
    txt_pass = st.campo_estilo("Sua Senha", ft.icons.LOCK, password=True)
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
            # Autenticação no Supabase
            auth_response = supabase.auth.sign_in_with_password({
                "email": txt_user.value.strip().lower(),
                "password": txt_pass.value
            })

            if auth_response.user:
                # Recupera o nível de acesso dos metadados (definido no cadastro)
                user_metadata = auth_response.user.user_metadata
                role = user_metadata.get("role", "user") 

                # Armazena na sessão para uso em outras telas (como no Dashboard de Saúde)
                page.session.set("user_role", role)
                page.session.set("user_email", auth_response.user.email)

                print(f"DEBUG: Login realizado. Usuário: {auth_response.user.email} | Nível: {role}")
                page.go("/menu")

        except Exception as ex:
            lbl_erro.value = "E-mail ou senha incorretos."
            lbl_erro.visible = True
            print(f"Erro de login: {ex}")
            page.update()

    # --- FUNÇÃO DE CADASTRO (CORRIGIDA) ---
    async def abrir_cadastro(e):
        # Definição dos campos para a janela de cadastro
        email_cad = st.campo_estilo("E-mail Real para Cadastro", ft.icons.EMAIL)
        senha_cad = st.campo_estilo("Crie sua Senha", ft.icons.LOCK, password=True)
        lbl_msg_cad = ft.Text("", size=12)

        async def processar_cadastro(e):
            try:
                # Validação básica
                if not email_cad.value or not senha_cad.value:
                    lbl_msg_cad.value = "Preencha todos os campos!"
                    lbl_msg_cad.color = "orange"
                    page.update()
                    return

                # Chamada de criação de usuário no Supabase
                # Ajustado de .cad para .value para evitar o erro anterior
                res = supabase.auth.sign_up({
                    "email": email_cad.value.strip().lower(),
                    "password": senha_cad.value, 
                    "options": {
                        "data": { "role": "user" } # Novos cadastros entram como usuário comum
                    }
                })
                
                if res.user:
                    bs.open = False
                    page.snack_bar = ft.SnackBar(
                        ft.Text("Cadastro realizado! Verifique seu e-mail para confirmar."),
                        bgcolor="green"
                    )
                    page.snack_bar.open = True
                    page.update()
                    
            except Exception as ex:
                lbl_msg_cad.value = f"Erro ao cadastrar: {str(ex)}"
                lbl_msg_cad.color = "red"
                page.update()

        # Interface de Cadastro (BottomSheet)
        bs = ft.BottomSheet(
            ft.Container(
                padding=20,
                bgcolor=st.BG_DARK,
                content=ft.Column([
                    ft.Text("Criar Nova Conta", size=20, weight="bold", color="white"),
                    ft.Text("Use um e-mail real para poder recuperar a senha depois.", size=12, color="white54"),
                    email_cad,
                    senha_cad,
                    lbl_msg_cad,
                    ft.ElevatedButton(
                        "FINALIZAR CADASTRO", 
                        on_click=processar_cadastro, 
                        width=320, height=50, 
                        style=st.BTN_MAIN
                    ),
                    ft.TextButton("Cancelar", on_click=lambda _: setattr(bs, "open", False) or page.update())
                ], tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15)
            ),
            open=True
        )
        page.overlay.append(bs)
        page.update()

    # Layout Principal da View de Login
    return ft.View(
        route="/login",
        bgcolor=st.BG_DARK,
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Container(
                content=ft.Column([
                    # Logotipo do ÁguaFlow
                    # Dentro de criar_tela_login em views/auth.py
                    ft.Image(
                        src="assets/logo.jpeg", # Certifique-se que o arquivo está em C:\AguaFlow\assets\logo.jpeg
                        width=120,
                        height=120,
                        border_radius=60,
                        error_content=ft.Icon(ft.icons.WATER_DROP, size=100, color="blue") # Backup caso a imagem falhe
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

                    ft.Row([
                        ft.TextButton("Criar nova conta", on_click=abrir_cadastro),
                        ft.TextButton(
                            "Esqueci minha senha", 
                            on_click=lambda _: page.go("/recuperar_senha")
                        ),
                    ], alignment=ft.MainAxisAlignment.CENTER)
                    
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                padding=20,
            )
        ]
    )