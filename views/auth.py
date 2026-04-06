from database.supabase_client import get_supabase_client
import asyncio
import flet as ft
# REMOVA O "IMPORT MAIN" DAQUI!


def logar_usuario(p, uid, email):
    # Criamos um atributo 'logado' dinamicamente na página
    p.logado = True
    p.user_email = email
    p.go("/menu")


def permitir_entrada_admin(page):
    """Fallback direto para o Grupo 8"""
    page.logado = True
    page.user_email = "admin@offline.local"
    page.overlay.clear()
    page.go("/menu")


def criar_tela_login(page, ao_logar_sucesso):
    # Componentes de entrada
    email_f = ft.TextField(
        label="E-mail Institucional",
        width=300,
        autofocus=True,
        bgcolor=ft.Colors.GREY_900
    )
    pass_f = ft.TextField(
        label="Senha",
        password=True,
        width=300,
        can_reveal_password=True,
        bgcolor=ft.Colors.GREY_900
    )

    msg_erro = ft.Text("", color=ft.Colors.RED, size=12)
    progress_ring = ft.ProgressRing(visible=False)
    btn_login = ft.ElevatedButton("ENTRAR", width=300)

    async def handle_login_async():
        msg_erro.value = ""
        if not email_f.value or not pass_f.value:
            msg_erro.value = "Preencha e-mail e senha."
            page.update()
            return

        btn_login.disabled = True
        progress_ring.visible = True
        page.update()

        try:
            # Teste rápido de senha local antes de chamar o Supabase
            if email_f.value == "admin@aguaflow.com" and pass_f.value == "123456":
                logar_usuario(page, "admin_id", "admin@aguaflow.com")
                return

            supabase = get_supabase_client()
            if not supabase:
                msg_erro.value = "Erro: Conexão com banco ausente."
                return

            # Tentativa de login real
            response = await asyncio.to_thread(
                lambda: supabase.auth.sign_in_with_password({
                    "email": email_f.value,
                    "password": pass_f.value
                })
            )

            if response and response.user:
                logar_usuario(page, response.user.id, response.user.email)
            else:
                msg_erro.value = "Credenciais inválidas."

        except Exception as erro:
            msg_erro.value = "Erro na autenticação."
            print(f"Erro Auth: {erro}")
        finally:
            progress_ring.visible = False
            btn_login.disabled = False
            page.update()

    btn_login.on_click = lambda _: asyncio.create_task(handle_login_async())

    return ft.View(
        route="/",
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        bgcolor="#121417",
        controls=[
            ft.Column([
                ft.Icon(ft.Icons.WATER_DROP, size=100, color=ft.Colors.BLUE),
                ft.Text("AguaFlow", size=32, weight="bold", color="white"),
                ft.Text("Vivere Prudente", size=16, color="white70"),
                ft.Container(height=20),
                email_f,
                pass_f,
                progress_ring,
                msg_erro,
                btn_login,
                ft.TextButton(
                    "Modo Offline (Grupo 8)",
                    on_click=lambda _: permitir_entrada_admin(page),
                    width=300
                )
            ], horizontal_alignment="center", spacing=15, width=400)
        ]
    )
