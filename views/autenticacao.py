import flet as ft
from database.database import Database
# Importamos os estilos para manter o padrão visual do AguaFlow
# Certifique-se do caminho correto do import
from utils.updater import AppUpdater
from views import styles as st


def montar_tela_autenticacao(page: ft.Page):
    try:
        # Componentes de interface com o estilo do projeto
        nome_input = ft.TextField(label="Nome Completo", width=320,
                                  border_radius=10, border_color="blue", color="white")
        email_input = ft.TextField(
            label="E-mail", width=320, border_radius=10, border_color="blue", color="white")
        senha_input = ft.TextField(
            label="Senha",
            width=320,
            border_radius=10,
            password=True,
            can_reveal_password=True,
            border_color="blue",
            color="white"
        )

        lbl_mensagem = ft.Text("", size=14)

        async def executar_cadastro(e):
            if not nome_input.value or not email_input.value or not senha_input.value:
                lbl_mensagem.value = "Por favor, preencha todos os campos."
                lbl_mensagem.color = "orange"
                page.update()
                return

            # Tenta criar o utilizador
            try:
                if hasattr(Database, 'criar_usuario'):
                    sucesso = Database.criar_usuario(
                        nome_input.value,
                        email_input.value,
                        senha_input.value
                    )
                else:
                    sucesso = True

                if sucesso:
                    # Salva dados na sessão temporária da página (user_data)
                    page.user_data = {"email": email_input.value,
                                      "role": "user", "offline": True}
                    page.push_route("/menu")
                else:
                    lbl_mensagem.value = "Erro ao criar conta. Tente outro e-mail."
                    lbl_mensagem.color = "red"
            except Exception as err:
                lbl_mensagem.value = f"Erro técnico: {err}"
                lbl_mensagem.color = "red"

            page.update()

        return ft.View(
            route="/registro",
            vertical_alignment="center",
            horizontal_alignment="center",
            bgcolor="#121417",
            controls=[
                ft.Column([
                    ft.Icon(ft.Icons.PERSON_ADD, size=80, color="blue"),
                    ft.Text("Novo Cadastro", size=26,
                            weight="bold", color="white"),
                    ft.Text("Crie sua conta para acesso offline",
                            size=14, color="grey"),
                    ft.Container(height=10),
                    nome_input,
                    email_input,
                    senha_input,
                    lbl_mensagem,
                    ft.Container(height=10),
                    ft.ElevatedButton(
                        "CRIAR CONTA E ENTRAR",
                        width=320,
                        height=50,
                        bgcolor="blue",
                        color="white",
                        on_click=executar_cadastro
                    ),
                    ft.TextButton("Já tenho conta? Entrar",
                                  on_click=lambda _: page.push_route("/")),
                    ft.Text(AppUpdater.get_footer(),
                            size=10, color="grey")
                ], horizontal_alignment="center")
            ]
        )
    except Exception as e:
        return ft.View(route="/registro", controls=[ft.Text(f"Erro ao carregar cadastro: {str(e)}", color="red")])
