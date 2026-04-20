import flet as ft
import asyncio
import os
from supabase import create_client, Client
from dotenv import load_dotenv
import views.styles as st 

load_dotenv() 

url = os.getenv("SUPABASE_URL") 
key = os.getenv("SUPABASE_KEY") 

if url and key:
    supabase: Client = create_client(url, key)
else:
    print("⚠️ Aviso: Supabase não configurado no auth.py")

# --- NOVA FUNÇÃO ADICIONADA ---
def montar_tela_esqueci_senha(page: ft.Page):
    txt_email = ft.TextField(label="E-mail cadastrado", width=320, border_color=st.ACCENT_ORANGE)
    
    return ft.View(
        route="/esqueci_senha",
        bgcolor=st.BG_DARK,
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Icon(ft.icons.LOCK_RESET, size=80, color=st.ACCENT_ORANGE),
            ft.Text("Recuperar Senha", size=24, weight="bold", color=st.WHITE),
            ft.Container(height=10),
            txt_email,
            ft.ElevatedButton("Enviar Instruções", style=st.BTN_MAIN, width=320, on_click=lambda _: print("Enviando...")),
            ft.TextButton("Voltar ao Login", on_click=lambda _: page.go("/"))
        ]
    )

def criar_tela_login(page: ft.Page):
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
            auth_response = supabase.auth.sign_in_with_password({"email": txt_user.value, "password": txt_pass.value})
            if auth_response.user:
                await page.client_storage.set_async("user_email", txt_user.value)
                page.user_email = txt_user.value
                page.go("/menu")
        except Exception:
            lbl_erro.value = "E-mail ou senha incorretos."
            lbl_erro.visible = True
            page.update()

    return ft.View(
        route="/",
        bgcolor=st.BG_DARK,
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Container(
                content=ft.Column([
                    ft.Image(src="assets/logo.jpeg", width=120, height=120, border_radius=60, error_content=ft.Icon(ft.icons.WATER_DROP, size=100, color="blue")),
                    ft.Text("AguaFlow", style=st.TEXT_TITLE),
                    ft.Text("Vivere Prudente", style=st.TEXT_SUB),
                    ft.Divider(height=20, color="transparent"),
                    txt_user, txt_pass, lbl_erro,
                    ft.Divider(height=10, color="transparent"),
                    ft.ElevatedButton("ENTRAR", on_click=realizar_login, width=320, height=50, style=st.BTN_MAIN),
                    ft.Row([
                        ft.TextButton("Criar nova conta", on_click=lambda _: page.go("/autenticacao")),
                        ft.TextButton("Esqueci minha senha", on_click=lambda _: page.go("/esqueci_senha"))
                    ], alignment=ft.MainAxisAlignment.CENTER)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                padding=20,
            )
        ]
    )