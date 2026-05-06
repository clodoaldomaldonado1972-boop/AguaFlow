import flet as ft


def validar_sessao(page: ft.Page, rota: str, required_role: str = None):
    """
    Valida se existe um usuário autenticado na sessão (page.user_data).
    Caso não exista, redireciona o usuário para a tela de login (/).
    Se required_role for definido, verifica se o usuário possui permissão.
    Retorna uma View vazia para sinalizar a interrupção da montagem da tela original.
    """
    if not page.user_data:
        print(
            f"🔒 Acesso negado: Tentativa de entrada na rota {rota} sem login.")
        # Redireciona para a raiz (login)
        page.go("/")
        # Retornamos uma View técnica para evitar que o Flet tente renderizar controles nulos
        return ft.View(route=rota)

    # Verificação de cargo (Role)
    if required_role:
        user_role = page.user_data.get("role", "user")
        if user_role != required_role and user_role != "admin":
            print(f"🚫 Acesso negado: Rota {rota} exige cargo '{required_role}'.")
            page.snack_bar = ft.SnackBar(
                ft.Text("Acesso restrito a administradores."), bgcolor="red")
            page.snack_bar.open = True
            page.go("/menu")
            return ft.View(route=rota)

    return None
