import flet as ft
from views import styles as st


def criar_tela_login(page, ao_logar_sucesso):
    # Campos de entrada
    # Certifique-se de que st.campo_estilo retorna um ft.TextField válido
    # Mudado para Icon constante
    email_f = st.campo_estilo("E-mail Institucional", ft.Icons.EMAIL_OUTLINED)
    # Mudado para Icon constante
    pass_f = st.campo_estilo("Senha", ft.Icons.LOCK_OUTLINED)
    pass_f.password = True

    # IMPORTANTE: st.ERROR_COLOR deve ser algo como ft.Colors.RED (com C maiúsculo)
    msg_erro = ft.Text("", color=st.ERROR_COLOR, size=12)

    def handle_login(e):
        # Validação simples para o Condomínio Vivere Prudente
        if email_f.value == "admin@vivere.com" and pass_f.value == "ADMIN123":
            page.session.set("perfil", "Zelador")
            # Correção: O callback deve ser compatível com o que o main.py espera
            ao_logar_sucesso(e)
        else:
            msg_erro.value = "E-mail ou senha incorretos."
            msg_erro.update()  # Use update direto no controle para performance

    return ft.View(
        route="/",
        # No Flet 0.84, use as constantes com letra MAIÚSCULA
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        padding=20,
        controls=[
            ft.Container(
                bgcolor=st.BG_DARK,
                padding=30,
                border_radius=15,
                content=ft.Column([
                    # Ícone com letra maiúscula na cor se st.PRIMARY_BLUE for ft.Colors
                    ft.Icon(ft.Icons.WATER_DROP, size=80,
                            color=st.PRIMARY_BLUE),
                    ft.Text("AguaFlow", size=32,
                            weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    email_f,
                    pass_f,
                    msg_erro,
                    ft.ElevatedButton(
                        "ENTRAR NO SISTEMA",
                        on_click=handle_login,
                        width=300,
                        height=50,
                        # Adicionando um estilo básico caso o padrão falhe
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=10),
                        )
                    )
                ],
                    # Mudado de string para constante
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=15
                )
            )
        ]
    )
