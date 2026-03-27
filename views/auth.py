import flet as ft

def validar_login(usuario, senha):
    u = usuario.strip().lower()
    s = senha.strip()
    if u == "admin" and s.upper() == "ADMIN123": return "admin"
    if u == "leitor" and s == "1234": return "leitor"
    return None

def criar_tela_login(page, ao_logar_sucesso):
    user_f = ft.TextField(label="Usuário", prefix_icon=ft.icons.PERSON, width=300, border_color="blue")
    pass_f = ft.TextField(label="Senha", prefix_icon=ft.icons.LOCK, password=True, width=300, border_color="blue")

    async def entrar_clique(e):
        perfil = validar_login(user_f.value, pass_f.value)
        if perfil:
            await ao_logar_sucesso(perfil) # CAMINHO: Vai para ir_para_home no main.py
        else:
            page.snack_bar = ft.SnackBar(ft.Text("Dados incorretos!"), bgcolor="red")
            page.snack_bar.open = True
            page.update()

    return ft.Column([
        ft.Icon(ft.icons.WATER_DROP, size=80, color="blue"),
        ft.Text("AGUA FLOW", size=30, weight="bold"),
        user_f, pass_f,
        ft.ElevatedButton("ENTRAR", on_click=entrar_clique, width=300, bgcolor="blue", color="white")
    ], horizontal_alignment="center", alignment="center")