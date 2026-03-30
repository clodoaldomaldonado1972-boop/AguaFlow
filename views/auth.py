import flet as ft
from views import styles as st
import re

def validar_email(email):
    # Regex ajustada para ser mais flexível com domínios
    regex = r'^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
    return re.search(regex, email.lower())

def criar_tela_login(page, ao_logar_sucesso):
    
    email_f = st.campo_estilo("E-mail Institucional", ft.icons.EMAIL)
    pass_f = st.campo_estilo("Senha", ft.icons.LOCK, password=True)
    
    # Texto de erro dinâmico
    msg_erro = ft.Text("", color=st.ERROR_COLOR, size=12)

    async def handle_login(e):
        msg_erro.value = ""
        page.update()
        
        # 1. Validação de Campo Vazio
        if not email_f.value or not pass_f.value:
            msg_erro.value = "Por favor, preencha todos os campos."
            page.update()
            return

        # 2. Validação de Formato de Email (limpando espaços e jogando para minúsculo)
        email_digitado = email_f.value.lower().strip()
        if not validar_email(email_digitado):
            msg_erro.value = "Formato de e-mail inválido."
            page.update()
            return

        # 3. Simulação de Login (admin@vivere.com / ADMIN123)
        if email_digitado == "admin@vivere.com" and pass_f.value == "ADMIN123":
            # Chama a função de sucesso passando o perfil
            # Como definimos no main.py, isso disparará a troca de tela no palco
            await ao_logar_sucesso("admin")
        else:
            msg_erro.value = "E-mail ou senha não reconhecidos."
        
        page.update()

    def recuperar_senha(e):
        page.snack_bar = ft.SnackBar(ft.Text(f"Link de recuperação enviado para {email_f.value}"))
        page.snack_bar.open = True
        page.update()

    return ft.Container(
        bgcolor=st.BG_DARK,
        expand=True,
        content=ft.Column([
            ft.Icon(ft.icons.WATER_DROP_ROUNDED, size=100, color=st.PRIMARY_BLUE),
            ft.Text("AguaFlow", size=32, weight="bold", color=st.WHITE),
            ft.Text("Gestão Residencial Vivere Prudente", color=st.GREY),
            
            ft.Divider(height=40, color=ft.colors.TRANSPARENT),
            
            ft.Container(
                content=ft.Column([
                    email_f,
                    pass_f,
                    msg_erro,
                    ft.Divider(height=10, color=ft.colors.TRANSPARENT),
                    ft.ElevatedButton(
                        "ENTRAR NO SISTEMA",
                        style=st.BTN_MAIN,
                        width=320,
                        height=50,
                        on_click=handle_login # O Flet gerencia a chamada async automaticamente
                    ),
                    ft.TextButton(
                        "Esqueci minha senha", 
                        on_click=recuperar_senha,
                        style=ft.ButtonStyle(color=st.GREY)
                    ),
                ], horizontal_alignment="center"),
                width=350
            )
            
        ], horizontal_alignment="center", alignment="center")
    )