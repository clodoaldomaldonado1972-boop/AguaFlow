import flet as ft
import asyncio
from views.auth import supabase

def reset_password_view(page: ft.Page):
    # Campos de entrada com design limpo
    new_password = ft.TextField(
        label="Nova Senha", 
        password=True, 
        can_reveal_password=True,
        width=300,
        border_radius=10
    )
    confirm_password = ft.TextField(
        label="Confirmar Nova Senha", 
        password=True, 
        can_reveal_password=True,
        width=300,
        border_radius=10
    )
    
    status_msg = ft.Text(weight="bold")

    async def btn_update_click(e):
        if not new_password.value or not confirm_password.value:
            status_msg.value = "Preencha todos os campos."
            status_msg.color = "red"
            page.update()
            return

        if new_password.value != confirm_password.value:
            status_msg.value = "As senhas não coincidem!"
            status_msg.color = "red"
            page.update()
            return

        try:
            # O Supabase utiliza o token de acesso que vem no link do e-mail
            # para identificar qual utilizador está a tentar atualizar a senha
            response = supabase.auth.update_user({"password": new_password.value})
            
            status_msg.value = "Senha atualizada com sucesso!"
            status_msg.color = "green"
            page.update()
            
            # Delay assíncrono para não travar a UI (melhor que time.sleep)
            await asyncio.sleep(2)
            page.go("/login")
            
        except Exception as ex:
            status_msg.value = f"Erro ao atualizar: {str(ex)}"
            status_msg.color = "red"
            page.update()

    # Layout da Página
    return ft.View(
        "/reset-password",
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        controls=[
            ft.AppBar(title=ft.Text("AguaFlow - Redefinir Senha"), bgcolor="blue800"),
            ft.Column(
                [
                    ft.Icon(ft.icons.LOCK_RESET, size=80, color="blue"),
                    ft.Text("Crie uma nova senha segura", size=20, weight="bold"),
                    ft.Divider(height=10, color="transparent"),
                    new_password,
                    confirm_password,
                    status_msg,
                    ft.Divider(height=10, color="transparent"),
                    ft.ElevatedButton(
                        "Atualizar Senha", 
                        on_click=btn_update_click, 
                        width=300,
                        height=50
                    ),
                    ft.TextButton("Voltar ao Login", on_click=lambda _: page.go("/login"))
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        ]
    )