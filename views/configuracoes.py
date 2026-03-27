import flet as ft

def montar_tela_configs(page, voltar):
    def exibir_ajuda(e):
        # Janela popup com instruções de uso do Scanner
        dialogo = ft.AlertDialog(
            title=ft.Text("Como Escanear"),
            content=ft.Column([
                ft.Text("1. Aponte para os números pretos e vermelhos."),
                ft.Text("2. Mantenha o telemóvel firme (sem tremer)."),
                ft.Text("3. Evite reflexos de luz no vidro do hidrómetro."),
                ft.Image(src="https://flet.dev/img/docs/controls/image/flower.jpg", width=200), # Substitua pela sua imagem de exemplo
            ], tight=True),
            actions=[ft.TextButton("Entendi", on_click=lambda _: page.close(dialogo))]
        )
        page.overlay.append(dialogo)
        dialogo.open = True
        page.update()

    return ft.Container(
        padding=20,
        content=ft.Column([
            ft.Text("Configurações", size=24, weight="bold"),
            ft.ListTile(leading=ft.Icon(ft.icons.EMAIL), title=ft.Text("E-mail de Notificações")),
            ft.ListTile(leading=ft.Icon(ft.icons.PERSON_ADD), title=ft.Text("Cadastrar Novo Leitor")),
            ft.ListTile(
                leading=ft.Icon(ft.icons.HELP_CENTER, color="orange"), 
                title=ft.Text("Ajuda: Como usar o Scanner"),
                on_click=exibir_ajuda
            ),
            ft.Divider(),
            ft.ElevatedButton("VOLTAR AO MENU", on_click=voltar, width=320, bgcolor="blue", color="white")
        ], horizontal_alignment="center")
    )