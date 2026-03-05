import flet as ft

def validar_login(usuario, senha):
    """Lógica de conferência de credenciais"""
    u = usuario.strip().lower()
    s = senha.strip()
    # Admin (Local Secreto) | Usuário (Celular/Leitor)
    if u == "admin" and s == "ADMIN123": return "admin"
    if u == "leitor" and s == "1234": return "leitor"
    return None

def criar_tela_login(page, ao_logar_sucesso):
    """Retorna o Container visual da tela de login"""
    def entrar_clique(e):
        perfil = validar_login(user_f.value, pass_f.value)
        if perfil:
            page.session.set("perfil", perfil)
            ao_logar_sucesso() # Chama a função de ir para o menu no main.py
        else:
            page.snack_bar = ft.SnackBar(ft.Text("Acesso Negado!"))
            page.snack_bar.open = True
            page.update()

    user_f = ft.TextField(label="Usuário", prefix_icon=ft.Icons.PERSON)
    pass_f = ft.TextField(label="Senha", password=True, can_reveal_password=True)

    return ft.Container(
        padding=40, alignment=ft.alignment.center,
        content=ft.Column([
            ft.Icon(ft.Icons.WATER_DROP, size=50, color="blue"),
            ft.Text("Login ÁguaFlow", size=24, weight="bold"),
            user_f, pass_f,
            ft.FilledButton("ENTRAR", on_click=entrar_clique, width=300)
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )
