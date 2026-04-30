import flet as ft
import asyncio
import os
from supabase import create_client, Client
from dotenv import load_dotenv
import views.styles as st
# 1. IMPORTAÇÃO DA AUTOMAÇÃO DE VERSÃO
from utils.updater import AppUpdater

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

# Configuração do Cliente Supabase
if url and key:
    supabase_client = create_client(url, key)
else:
    supabase_client = None
    print("⚠️ Aviso: Supabase não configurado no auth.py")


def montar_tela_esqueci_senha(page: ft.Page):
    txt_email = ft.TextField(label="E-mail cadastrado",
                             # Cor segura[cite: 3]
                             width=320, border_color="orange")

    return ft.View(
        route="/esqueci_senha",
        bgcolor="#121417",  # Cor estável[cite: 8]
        vertical_alignment="center",  # String literal[cite: 3]
        horizontal_alignment="center",
        controls=[
            ft.Icon("lock_reset", size=80, color="orange"),
            ft.Text("Recuperar Senha", size=24, weight="bold", color="white"),
            ft.Container(height=10),
            txt_email,
            ft.ElevatedButton(
                "Enviar Instruções",
                width=320,
                on_click=lambda _: page.go("/recuperar-email"),
            ),
            ft.TextButton("Voltar ao Login", on_click=lambda _: page.go("/")),
            # 2. RODAPÉ AUTOMÁTICO NA RECUPERAÇÃO
            ft.Divider(color="white10"),
            ft.Text(AppUpdater.get_footer(), size=10, color="grey")
        ]
    )


def criar_tela_login(page: ft.Page):
    txt_user = st.campo_estilo("E-mail")
    txt_pass = st.campo_estilo("Senha", password=True)
    txt_pass.can_reveal_password = True

    lbl_erro = ft.Text("", color="red", size=12,
                       weight=ft.FontWeight.BOLD, visible=False)

    async def realizar_login(e):
        try:
            auth_response = supabase_client.auth.sign_in_with_password({
                "email": txt_user.value,
                "password": txt_pass.value
            })

            if auth_response.user:
                page.user_data = {"email": txt_user.value}
                print(f"✅ Login aprovado para: {txt_user.value}")
                page.go("/menu")
                return

        except Exception as ex:
            print(f"❌ Erro no login: {ex}")
            lbl_erro.value = "E-mail ou senha incorretos."
            lbl_erro.visible = True
            page.update()

    return ft.View(
        route="/",
        bgcolor="#121417",
        vertical_alignment="center",
        horizontal_alignment="center",
        controls=[
            ft.Container(
                content=ft.Column([
                    # Usando string para evitar AttributeError
                    ft.Icon("water", size=96, color="blue"),
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
                        height=50
                    ),
                    ft.Row([
                        ft.TextButton("Criar nova conta",
                                      on_click=lambda _: page.go("/registro")),
                        ft.TextButton(
                            "Esqueci minha senha", on_click=lambda _: page.go("/esqueci_senha"))
                    ], alignment="center"),

                    # 3. RODAPÉ AUTOMÁTICO NO LOGIN
                    ft.Divider(height=30, color="transparent"),
                    ft.Divider(color="white10"),
                    ft.Text(
                        AppUpdater.get_footer(),  # Puxa v1.1.2 do updater.py
                        size=11,
                        color="grey",
                        italic=True
                    )
                ], horizontal_alignment="center", spacing=10),
                padding=20,
            )
        ]
    )
