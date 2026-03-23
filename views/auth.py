import flet as ft


def validar_login(usuario, senha):
    u = usuario.strip().lower()
    s = senha.strip()
    if u == "admin" and s.upper() == "ADMIN123":
        return "admin"
    if u == "leitor" and s == "1234":
        return "leitor"
    return None


def criar_tela_login(page, ao_logar_sucesso):
    user_f = ft.TextField(
        label="Usuário",
        prefix_icon=ft.Icons.PERSON,  # <-- ADICIONADA A VÍRGULA AQUI
        color="white",
        border_color="blue",
        focused_border_color="white",
        width=300
    )

    pass_f = ft.TextField(
        label="Senha",
        password=True,
        can_reveal_password=True,
        color="white",
        border_color="blue",
        focused_border_color="white",
        width=300
    )

    async def entrar_clique(e):
        # Desativa o botão temporariamente para evitar cliques duplos que travam a sessão
        e.control.disabled = True
        page.update()

        perfil = validar_login(user_f.value, pass_f.value)
        if perfil:
            await ao_logar_sucesso(perfil)
        else:
            e.control.disabled = False  # Reativa o botão se errar
            page.snack_bar = ft.SnackBar(
                ft.Text("Dados incorretos!"), bgcolor="red")
            page.snack_bar.open = True
            page.update()

    return ft.Container(
        expand=True,
        content=ft.Column(
            controls=[
                # CORREÇÃO: Adicionado ft.Icons. e aspas no texto
                ft.Icon(ft.Icons.WATER_DROP, size=80, color="blue"),
                ft.Text("AGUA FLOW", size=30, weight="bold", color="white"),
                ft.Text("Vivere Prudente", size=16, color="white54"),
                ft.Container(height=20),
                user_f,
                pass_f,
                ft.Container(height=10),
                ft.FilledButton(
                    content=ft.Text("ENTRAR NO SISTEMA"),
                    on_click=entrar_clique,
                    width=300,
                    height=50
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
        )
    )
