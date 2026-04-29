import flet as ft
import asyncio
import os
from supabase import create_client, Client
from dotenv import load_dotenv
import views.styles as st 

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
            ft.ElevatedButton(
                "Enviar Instruções",
                style=st.BTN_MAIN,
                width=320,
                on_click=lambda _: page.go("/recuperar-email"),
            ),
            ft.TextButton("Voltar ao Login", on_click=lambda _: page.go("/"))
        ]
    )

def criar_tela_login(page: ft.Page):
    txt_user = st.campo_estilo("E-mail")
    # ATIVAÇÃO DO OLHINHO: Recurso nativo do Flet
    txt_pass = st.campo_estilo("Senha", password=True)
    # Ativa o ícone de visibilidade (olhinho) automaticamente
    txt_pass.can_reveal_password = True

    lbl_erro = ft.Text("", color="red", size=12, weight=ft.FontWeight.BOLD, visible=False)

    def salvar_sessao_usuario(email: str):
        """Compatível com versões que não expõem page.client_storage."""
        if hasattr(page, "client_storage") and page.client_storage:
            page.client_storage.set("user_email", email)
        else:
            page.session.set("user_email", email)

    async def realizar_login(e):
        # ... (código de validação inicial permanece o mesmo)
        try:
            auth_response = supabase_client.auth.sign_in_with_password({
                "email": txt_user.value,
                "password": txt_pass.value
            })

            if auth_response.user:
                # CORREÇÃO: Salva o e-mail de forma direta no dicionário de sessão
                # Isso evita o erro 'attribute set'
                page.session["user_email"] = txt_user.value
                
                print(f"✅ Login aprovado para: {txt_user.value}")
                page.go("/menu")
                return

        except Exception as ex:
            print(f"❌ Erro no login: {ex}")
            lbl_erro.value = "E-mail ou senha incorretos."
            lbl_erro.visible = True
            page.update()
        except Exception as ex:
            print(f"❌ Erro no login: {ex}")
            lbl_erro.value = "E-mail ou senha incorretos."
            lbl_erro.visible = True
            page.update()
    # 3. Retorno da View Única
    # ... dentro de criar_tela_login, após definir realizar_login ...
    return ft.View(
        route="/",
        bgcolor=st.BG_DARK,
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Container(
                content=ft.Column([
                    # Fallback estável para evitar crashes de renderização no desktop
                    ft.Icon(ft.icons.WATER_DROP, size=96, color=st.PRIMARY_BLUE),
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
                        ft.TextButton("Criar nova conta", on_click=lambda _: page.go("/registro")),
                        ft.TextButton("Esqueci minha senha", on_click=lambda _: page.go("/esqueci_senha"))
                    ], alignment=ft.MainAxisAlignment.CENTER)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                padding=20,
            )
        ]
    )