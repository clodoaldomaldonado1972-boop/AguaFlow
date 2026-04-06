import flet as ft


def montar_tela_configs(page, voltar):
    # Recupera o usuário logado usando o padrão get_data da v0.84.0
    user_email = page.session.get_data(
        "user_email") if page.session else "Visitante"

    def exibir_ajuda(e):
        # Limpa overlays antigos para evitar a faixa vermelha
        page.overlay.clear()

        dialogo = ft.AlertDialog(
            title=ft.Text("Central de Ajuda - AguaFlow"),
            content=ft.Column([
                ft.Text("📝 MEDIÇÃO MANUAL:", weight="bold", color="blue"),
                ft.Text("Use o ícone de lápis para liberar o teclado."),
                ft.Divider(),
                ft.Text("📸 SCANNER (OCR):", weight="bold", color="green"),
                ft.Text("1. Aponte para os números pretos e vermelhos."),
                ft.Text("2. Evite reflexos de luz no vidro."),
                ft.Text("3. Mantenha o celular firme."),
            ], tight=True),
            actions=[
                ft.TextButton(
                    "FECHAR", on_click=lambda _: fechar_dialogo(dialogo))
            ]
        )
        page.overlay.append(dialogo)
        # Na v0.84.0, usamos page.show_dialog para abrir com segurança
        page.show_dialog(dialogo)
        page.update()

    def fechar_dialogo(dlg):
        # Na v0.84.0, a forma mais segura de fechar é limpar o overlay ou remover o diálogo
        page.overlay.clear()
        page.update()

    return ft.Container(
        padding=20,
        content=ft.Column([
            ft.Text("Configurações e Suporte", size=24, weight="bold"),
            ft.Text(f"Logado como: {user_email}", color="grey", size=14),
            ft.Divider(),

            ft.ListTile(
                leading=ft.Icon(ft.Icons.HELP_CENTER, color="orange"),
                title=ft.Text("Tutorial: Como usar o Scanner"),
                subtitle=ft.Text("Dicas para leitura de hidrômetros"),
                on_click=exibir_ajuda
            ),

            ft.ListTile(
                leading=ft.Icon(ft.Icons.FOLDER_OPEN, color="blue"),
                title=ft.Text("Local dos Relatórios"),
                subtitle=ft.Text("PDFs salvos em: C:\\AguaFlow\\export")
            ),

            ft.ListTile(
                leading=ft.Icon(ft.Icons.CONTACT_SUPPORT, color="green"),
                title=ft.Text("Suporte Grupo 8"),
                subtitle=ft.Text("suporte@aguaflow.com"),
                on_click=lambda _: page.show_snack_bar(
                    ft.SnackBar(
                        ft.Text("E-mail copiado para a área de transferência!"))
                )
            ),

            ft.Divider(),
            ft.ElevatedButton(
                "VOLTAR AO MENU",
                on_click=voltar,
                width=320,
                bgcolor=ft.Colors.BLUE,  # Ajustado para Colors (C maiúsculo)
                color=ft.Colors.WHITE
            )
        ], horizontal_alignment="center")
    )
