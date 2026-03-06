import flet as ft


def validar_login(usuario, senha):
    u = usuario.strip().lower()
    s = senha.strip()
    if u == "admin" and s == "ADMIN123":
        return "admin"
    if u == "leitor" and s == "1234":
        return "leitor"
    return None


def criar_tela_login(page, ao_logar_sucesso):
    # 1. Primeiro definimos os campos de texto
    user_f = ft.TextField(
        label="Usuário", prefix_icon=ft.Icons.PERSON, color="white")
    pass_f = ft.TextField(label="Senha", password=True,
                          can_reveal_password=True, color="white")

    # 2. SEGUNDO: Definimos a função de clique (ela PRECISA vir antes do botão)
    def entrar_clique(e):
        perfil = validar_login(user_f.value, pass_f.value)
        if perfil:
            ao_logar_sucesso(perfil)
        else:
            page.snack_bar = ft.SnackBar(
                ft.Text("Usuário ou Senha Inválidos!"), bgcolor="red")
            page.snack_bar.open = True
            page.update()

    # 3. TERCEIRO: Agora sim criamos o retorno com o botão que chama a função
    return ft.Container(
        expand=True,
        bgcolor="#1A1C1E",
        alignment=ft.Alignment(0, 0),
        padding=40,
        content=ft.Column([
            ft.Icon(ft.Icons.WATER_DROP, size=50, color="blue"),
            ft.Text("Login ÁguaFlow", size=24, weight="bold", color="white"),
            user_f,
            pass_f,
            ft.Container(height=10),
            ft.FilledButton(
                "ENTRAR",
                on_click=entrar_clique,  # Agora ele já sabe quem é o 'entrar_clique'
                width=300
            )
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )
