import flet as ft


def validar_sessao(page: ft.Page, rota: str, required_role: str = None):
    """
    Valida se existe um usuário autenticado na sessão (page.user_data).
    Retorna None se a sessão é válida; retorna uma View de redirecionamento caso contrário.
    """
    if not page.user_data or not page.user_data.get("email"):
        print(f"🔒 Acesso negado: rota {rota} sem login.")
        page.go("/")
        return ft.View(
            route=rota,
            bgcolor="#121417",
            vertical_alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Icon("lock_outline", size=64, color="#2196F3"),
                ft.Text("Sessão expirada", size=18, color="white"),
                ft.Text("Redirecionando para o login...", size=12, color="grey"),
            ]
        )

    if required_role:
        user_role = page.user_data.get("role", "user")
        if user_role != required_role and user_role != "admin":
            print(f"🚫 Acesso negado: rota {rota} exige cargo '{required_role}'.")
            page.go("/menu")
            return ft.View(
                route=rota,
                bgcolor="#121417",
                vertical_alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Icon("block", size=64, color="red"),
                    ft.Text("Acesso restrito a administradores.", size=14, color="white"),
                    ft.ElevatedButton("Voltar ao Menu", on_click=lambda _: page.go("/menu")),
                ]
            )

    return None
