import flet as ft
import asyncio
from database.database import get_supabase_client

# Cliente Supabase centralizado
supabase = get_supabase_client()

def reset_password_view(page: ft.Page):
    # 1. ESTILIZAÇÃO DOS CAMPOS (Padronizado com o restante do app)
    new_password = ft.TextField(
        label="Nova Senha", 
        password=True, 
        can_reveal_password=True,
        border_radius=10,
        width=320,
        prefix_icon=ft.icons.LOCK_OUTLINE,
        bgcolor=ft.colors.with_opacity(0.1, ft.colors.WHITE)
    )
    
    confirm_password = ft.TextField(
        label="Confirmar Nova Senha", 
        password=True, 
        can_reveal_password=True,
        border_radius=10,
        width=320,
        prefix_icon=ft.icons.LOCK_RESET,
        bgcolor=ft.colors.with_opacity(0.1, ft.colors.WHITE)
    )
    
    status_msg = ft.Text(weight="bold", text_align=ft.TextAlign.CENTER)

    # 2. LÓGICA DE ATUALIZAÇÃO
    async def btn_update_click(e):
        # Validação básica de campos vazios
        if not new_password.value or not confirm_password.value:
            status_msg.value = "⚠️ Preencha todos os campos."
            status_msg.color = "orange"
            page.update()
            return

        # Validação de igualdade
        if new_password.value != confirm_password.value:
            status_msg.value = "❌ As senhas não coincidem!"
            status_msg.color = "red"
            page.update()
            return

        try:
            # Mostra estado de carregamento
            status_msg.value = "Processando..."
            status_msg.color = "blue"
            e.control.disabled = True
            page.update()

            # O Supabase identifica o utilizador pelo token presente no link do e-mail
            # que disparou a abertura desta view
            supabase.auth.update_user({"password": new_password.value})
            
            status_msg.value = "✅ Senha atualizada com sucesso!\nRedirecionando..."
            status_msg.color = "green"
            page.update()
            
            # Delay para o usuário ler a mensagem antes de voltar ao login
            await asyncio.sleep(2)
            page.go("/")
            
        except Exception as ex:
            status_msg.value = f"Erro ao atualizar: {str(ex)}"
            status_msg.color = "red"
            e.control.disabled = False
            page.update()

    # 3. CONSTRUÇÃO DA INTERFACE (Layout Dark Modern)
    return ft.View(
        "/reset-password",
        bgcolor="#121417", # Cor de fundo padrão do AguaFlow
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        controls=[
            ft.AppBar(
                title=ft.Text("Redefinir Senha", weight="bold"),
                bgcolor=ft.colors.SURFACE_VARIANT,
                center_title=True
            ),
            ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(ft.icons.LOCK_PERSON_ROUNDED, size=80, color=ft.colors.BLUE_400),
                        ft.Text(
                            "Segurança da Conta", 
                            size=22, 
                            weight="bold", 
                            color=ft.colors.WHITE
                        ),
                        ft.Text(
                            "Digite sua nova senha abaixo para retomar o acesso.",
                            color="grey",
                            text_align=ft.TextAlign.CENTER,
                            size=14
                        ),
                        ft.Container(height=10),
                        new_password,
                        confirm_password,
                        status_msg,
                        ft.Container(height=10),
                        ft.ElevatedButton(
                            "ATUALIZAR SENHA", 
                            on_click=btn_update_click, 
                            width=320,
                            height=50,
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=10),
                                bgcolor=ft.colors.BLUE_700,
                                color=ft.colors.WHITE
                            )
                        ),
                        ft.TextButton(
                            "Cancelar e Voltar", 
                            on_click=lambda _: page.go("/")
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=15,
                ),
                padding=20,
                bgcolor="#1e1e1e",
                border_radius=20,
                width=350,
            )
        ]
    )