import flet as ft
from database.database import Database

def montar_tela_autenticacao(page: ft.Page):
    # Componentes de interface
    nome_input = ft.TextField(label="Nome Completo", width=320, border_radius=10)
    email_input = ft.TextField(label="E-mail", width=320, border_radius=10)
    senha_input = ft.TextField(
        label="Senha", 
        width=320, 
        border_radius=10, 
        password=True, 
        can_reveal_password=True
    )
    
    lbl_mensagem = ft.Text("", size=14)

    def executar_cadastro(e):
        if not nome_input.value or not email_input.value or not senha_input.value:
            lbl_mensagem.value = "Por favor, preencha todos os campos."
            lbl_mensagem.color = "orange"
            page.update()
            return

        # Tenta criar o utilizador no SQLite (database.py)
        sucesso = Database.criar_usuario(
            nome_input.value, 
            email_input.value, 
            senha_input.value
        )

        if sucesso:
            page.snack_bar = ft.SnackBar(
                ft.Text("Usuário cadastrado com sucesso!"), 
                bgcolor="green", 
                open=True
            )
            page.go("/login") # Redireciona para a tela de login
        else:
            lbl_mensagem.value = "Erro: Este e-mail já está em uso."
            lbl_mensagem.color = "red"
        page.update()

    def acao_recuperar(e):
        if not email_input.value:
            lbl_mensagem.value = "Introduza o seu e-mail para recuperar."
            lbl_mensagem.color = "blue"
        else:
            # Exibe um alerta de instrução
            page.dialog = ft.AlertDialog(
                title=ft.Text("Recuperar Senha"),
                content=ft.Text(f"A solicitação para o e-mail {email_input.value} foi enviada ao administrador Clodoaldo."),
                actions=[ft.TextButton("Ok", on_click=lambda _: setattr(page.dialog, "open", False))]
            )
            page.dialog.open = True
        page.update()

    return ft.View(
        route="/cadastrar",
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Column([
                ft.Image(src="assets/logo.jpeg", width=100, height=100, border_radius=50),
                ft.Text("Novo Cadastro", size=26, weight="bold"),
                nome_input,
                email_input,
                senha_input,
                lbl_mensagem,
                ft.ElevatedButton(
                    "CRIAR CONTA", 
                    width=320, 
                    height=50, 
                    bgcolor="blue", 
                    color="white",
                    on_click=executar_cadastro
                ),
                ft.TextButton("Já tenho conta? Entrar", on_click=lambda _: page.go("/login")),
                ft.TextButton("Esqueci a senha", on_click=acao_recuperar),
            ], horizontal_alignment="center", spacing=15)
        ]
    )