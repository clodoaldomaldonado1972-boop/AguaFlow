import flet as ft
from database.database import Database
# Importamos os estilos para manter o padrão visual do AguaFlow
from views import styles as st 

def montar_tela_autenticacao(page: ft.Page):
    # Componentes de interface com o estilo do projeto
    nome_input = ft.TextField(label="Nome Completo", width=320, border_radius=10, border_color="blue", color="white")
    email_input = ft.TextField(label="E-mail", width=320, border_radius=10, border_color="blue", color="white")
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

        # Tenta criar o utilizador (Adicione este método no seu database.py)
        try:
            # Verificação temporária enquanto o método não existe no database.py
            if hasattr(Database, 'criar_usuario'):
                sucesso = Database.criar_usuario(
                    nome_input.value, 
                    email_input.value, 
                    senha_input.value
                )
            else:
                # Fallback para teste
                print("Aviso: Método Database.criar_usuario ainda não implementado.")
                sucesso = True 

            if sucesso:
                page.user_email = email_input.value
                page.client_storage.set("user_email", email_input.value)
                page.go("/menu")
            else:
                lbl_mensagem.value = "Erro ao criar conta. Tente outro e-mail."
                lbl_mensagem.color = "red"
        except Exception as err:
            lbl_mensagem.value = f"Erro técnico: {err}"
            lbl_mensagem.color = "red"
        
        page.update()

    return ft.View(
        route="/registro", # ALTERADO: Sincronizado com o botão do login
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        bgcolor="#121417",
        controls=[
            ft.Column([
                # Usando ícone caso a logo.jpeg falhe
                ft.Icon(ft.icons.PERSON_ADD_ROUNDED, size=80, color="blue"),
                ft.Text("Novo Cadastro", size=26, weight="bold", color="white"),
                ft.Text("Crie sua conta para acesso offline", size=14, color="grey"),
                
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
                ft.TextButton("Já tenho conta? Entrar", on_click=lambda _: page.go("/")),
                
                # Rodapé do Vivere
                ft.Text("AguaFlow v1.0.2 - Residencial Vivere Prudente", size=10, color="grey")
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        ]
    )