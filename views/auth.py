import flet as ft
import asyncio
import os
from supabase import create_client, Client
import views.styles as st
from database.database import Database, get_supabase_client
# 1. IMPORTAÇÃO DA AUTOMAÇÃO DE VERSÃO
from utils.updater import AppUpdater


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

    progress_ring_login = ft.ProgressRing(width=16, height=16, stroke_width=2, color="white")
    text_loading_login = ft.Text("CARREGANDO SISTEMA...", size=14)

    btn_entrar = ft.ElevatedButton(
        content=ft.Row( # O conteúdo inicial do botão é um Row com o ProgressRing e o texto
            [
                progress_ring_login,
                text_loading_login,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10,
            tight=True
        ),
        on_click=realizar_login,
        width=320,
        height=50,
        disabled=True  # Inicia travado até o DB estar pronto
    )
    # Armazena a referência para o main.py habilitar depois
    page.session["btn_login"] = btn_entrar
    page.session["progress_ring_login"] = progress_ring_login
    page.session["text_loading_login"] = text_loading_login

    lbl_erro = ft.Text("", color="red", size=12,
                       weight="bold", visible=False)

    async def realizar_login(e):
        email = txt_user.value
        senha = txt_pass.value
        supabase_client = get_supabase_client()
        try:
            # 1. Tenta Login Online (Supabase)
            if supabase_client:
                try:
                    auth_response = supabase_client.auth.sign_in_with_password({
                        "email": email,
                        "password": senha
                    })

                    if auth_response.user:
                        # Extrai a role do metadata do Supabase (definido via SQL ou script admin)
                        role = auth_response.user.user_metadata.get(
                            "role", "user")
                        page.user_data = {"email": email, "role": role}
                        print(f"✅ Login online aprovado: {email} ({role})")
                        page.go("/menu")
                        return
                except Exception as ex:
                    print(
                        f"⚠️ Falha no login online, tentando offline... ({ex})")

            # 2. Fallback: Tenta Login Offline (SQLite)
            user_local = Database.validar_login_offline(email, senha)
            if user_local:
                page.user_data = {
                    "email": email,
                    "nome": user_local.get('nome'),
                    "role": user_local.get('role', 'user'),
                    "offline": True
                }
                print(
                    f"✅ Login offline aprovado: {email} ({page.user_data['role']})")
                page.go("/menu")
                return

            # 3. Se ambos falharem
            lbl_erro.value = "E-mail ou senha incorretos."
            lbl_erro.visible = True
            page.update()

        except Exception as ex:
            print(f"❌ Erro crítico no login: {ex}")
            lbl_erro.value = "Erro técnico ao acessar o sistema."
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
                    # logo = ft.Image(src="logo.jpeg", width=220, height=220), # COMENTE ESTA LINHA
                    # ft.Icon(ft.icons.WATER, size=96, color="blue"), # COMENTADO TAMBÉM
                    ft.Text("AguaFlow", size=32, weight="bold", color="white"),
                    ft.Text("CONDOMÍNIO EDIF. VIVERE PRUDENTE",
                            weight="bold", color="#0D47A1"),  # Usando Hex para 'blue900' mais seguro
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
