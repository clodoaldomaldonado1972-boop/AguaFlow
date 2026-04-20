import flet as ft
import asyncio
import os
from supabase import create_client, Client
from dotenv import load_dotenv
import views.styles as st 

# 1. CARREGAMENTO DAS VARIÁVEIS DE AMBIENTE
load_dotenv() 

url = os.getenv("SUPABASE_URL") 
key = os.getenv("SUPABASE_KEY") 

if url and key:
    supabase: Client = create_client(url, key)
else:
    print("⚠️ Aviso: Supabase não configurado no auth.py")

def criar_tela_login(page: ft.Page):
    # Componentes de interface utilizando o estilo padronizado
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
            # Autenticação no Cloud (Supabase)
            auth_response = supabase.auth.sign_in_with_password({
                "email": txt_user.value,
                "password": txt_pass.value
            })

            if auth_response.user:
                # --- AJUSTE PARA AUTO-LOGIN ---
                # 1. Salva o e-mail no armazenamento permanente do celular
                await page.client_storage.set_async("user_email", txt_user.value)
                # 2. Define a variável de sessão para uso imediato nas outras telas
                page.user_email = txt_user.value
                
                page.go("/menu")
        
        except Exception as ex:
            lbl_erro.value = "E-mail ou senha incorretos."
            lbl_erro.visible = True
            page.update()

    def abrir_cadastro(e):
        page.go("/autenticacao")

    # CONSTRUÇÃO DA VIEW
    return ft.View(
        route="/",
        bgcolor=st.BG_DARK,
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Container(
                content=ft.Column([
                    ft.Image(
                        src="assets/logo.jpeg",
                        width=120,
                        height=120,
                        border_radius=60,
                        error_content=ft.Icon(ft.icons.WATER_DROP, size=100, color="blue")
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