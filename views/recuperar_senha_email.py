import flet as ft
from views.auth import supabase
from views import styles as st

def criar_tela_recuperacao(page: ft.Page):
    txt_email = st.campo_estilo("E-mail cadastrado", ft.icons.EMAIL)
    lbl_status = ft.Text("", size=14)

    async def enviar_link(e):
        if not txt_email.value:
            lbl_status.value = "Por favor, digite seu e-mail."
            lbl_status.color = st.ERROR_COLOR
            page.update()
            return

        try:
            # Comando oficial do Supabase para disparar o e-mail
            supabase.auth.reset_password_for_email(
                txt_email.value,
                {"redirect_to": "http://localhost:8550/reset-password"} # Ajuste a porta se necessário
            )
            lbl_status.value = "Link enviado! Verifique sua caixa de entrada."
            lbl_status.color = "green"
            page.update()
        except Exception as ex:
            lbl_status.value = f"Erro: {str(ex)}"
            lbl_status.color = st.ERROR_COLOR
            page.update()

    return ft.View(
        route="/recuperar-email",
        bgcolor=st.BG_DARK,
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.icons.MARK_EMAIL_READ, size=80, color="blue"),
                    ft.Text("Recuperar Senha", style=st.TEXT_TITLE),
                    ft.Text("Enviaremos um link para o seu e-mail", style=st.TEXT_SUB),
                    ft.Divider(height=20, color="transparent"),
                    txt_email,
                    lbl_status,
                    ft.ElevatedButton(
                        "ENVIAR LINK MÁGICO",
                        on_click=enviar_link,
                        width=320,
                        height=50,
                        style=st.BTN_MAIN
                    ),
                    ft.TextButton("Voltar ao Login", on_click=lambda _: page.go("/login"))
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15),
                padding=20
            )
        ]
    )