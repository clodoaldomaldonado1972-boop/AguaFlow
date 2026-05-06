import flet as ft
import asyncio
import os
import views.styles as st
from database.database import Database, get_supabase_client
from utils.updater import AppUpdater


def montar_tela_esqueci_senha(page: ft.Page):
    try:
        txt_email = ft.TextField(label="E-mail cadastrado",
                                 width=320, border_color="orange")

        return ft.View(
            route="/esqueci_senha",
            bgcolor="#121417",
            vertical_alignment="center",
            horizontal_alignment="center",
            controls=[
                ft.Icon(ft.icons.LOCK_RESET, size=80, color="orange"),
                ft.Text("Recuperar Senha", size=24, weight="bold", color="white"),
                ft.Container(height=10),
                txt_email,
                ft.ElevatedButton(
                    "Enviar Instruções",
                    width=320,
                    on_click=lambda _: page.go("/recuperar-email"),
                ),
                ft.TextButton("Voltar ao Login", on_click=lambda _: page.go("/")),
                ft.Divider(color="white10"),
                ft.Text(AppUpdater.get_footer(), size=10, color="grey")
            ]
        )
    except Exception as e:
        return ft.View("/esqueci_senha", [ft.Text(f"Erro: {str(e)}", color="red")])


def criar_tela_login(page: ft.Page):
    # 1. DEFINIÇÃO DOS COMPONENTES DE INPUT
    txt_user = st.campo_estilo("E-mail")
    txt_pass = st.campo_estilo("Senha", password=True)
    txt_pass.can_reveal_password = True

    lbl_erro = ft.Text("", color="red", size=12, weight="bold", visible=False)

    progress_ring_login = ft.ProgressRing(
        width=16, height=16, stroke_width=2, color="white")
    text_loading_login = ft.Text("CARREGANDO SISTEMA...", size=14)

    # 2. DEFINIÇÃO DA LÓGICA DE LOGIN
    async def realizar_login(e):
        email = txt_user.value
        senha = txt_pass.value
        supabase_client = get_supabase_client()

        try:
            # Tenta Login Online (Supabase)
            if supabase_client:
                try:
                    auth_response = supabase_client.auth.sign_in_with_password({
                        "email": email, "password": senha
                    })
                    if auth_response.user:
                        role = auth_response.user.user_metadata.get(
                            "role", "user")
                        page.user_data = {"email": email, "role": role}
                        page.go("/menu")
                        return
                except Exception:
                    print("⚠️ Falha online, tentando offline...")

            # Fallback: Login Offline (SQLite)
            user_local = Database.validar_login_offline(email, senha)
            if user_local:
                page.user_data = {
                    "email": email,
                    "nome": user_local.get('nome'),
                    "role": user_local.get('role', 'user'),
                    "offline": True
                }
                page.go("/menu")
                return

            lbl_erro.value = "E-mail ou senha incorretos."
            lbl_erro.visible = True
            page.update()

        except Exception as ex:
            lbl_erro.value = "Erro técnico ao acessar o sistema."
            lbl_erro.visible = True
            page.update()

    # 3. CRIAÇÃO DO BOTÃO
    btn_entrar = ft.ElevatedButton(
        content=ft.Row(
            [progress_ring_login, text_loading_login],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10,
            tight=True
        ),
        on_click=realizar_login,
        width=320,
        height=50,
        disabled=False  # Mantenha False para o botão estar clicável e evitar loops
    )

    # --- SEÇÃO 4 REMOVIDA PARA EVITAR ERRO DE ATRIBUTO ---
    # Removidas as chamadas para page.session e page.client_storage

    try:
        return ft.View(
            route="/",
            bgcolor="#121417",
            vertical_alignment="center",
            horizontal_alignment="center",
            controls=[
                ft.Container(
                    content=ft.Column([
                        ft.Text("AguaFlow", size=32, weight="bold", color="white"),
                        ft.Text("CONDOMÍNIO EDIF. VIVERE PRUDENTE",
                                weight="bold", color="#0D47A1"),
                        ft.Divider(height=20, color="transparent"),
                        txt_user,
                        txt_pass,
                        lbl_erro,
                        ft.Divider(height=10, color="transparent"),
                        btn_entrar,
                        ft.Row([
                            ft.TextButton("Criar nova conta",
                                          on_click=lambda _: page.go("/registro")),
                            ft.TextButton(
                                "Esqueci minha senha", on_click=lambda _: page.go("/esqueci_senha"))
                        ], alignment="center"),
                        ft.Divider(height=30, color="transparent"),
                        ft.Divider(color="white10"),
                        ft.Text(AppUpdater.get_footer(), size=11,
                                color="grey", italic=True)
                    ], horizontal_alignment="center", spacing=10),
                    padding=20,
                )
            ]
        )
    except Exception as e:
        return ft.View("/", [ft.Text(f"Erro Crítico: {str(e)}", color="red")])
