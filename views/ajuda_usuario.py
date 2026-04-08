import flet as ft


def montar_tela_ajuda(page, voltar):
    return ft.View(
        route="/ajuda",
        bgcolor="#121417",
        appbar=ft.AppBar(
            title=ft.Text("Central de Ajuda"),
            bgcolor="#1e1e1e",
            leading=ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=voltar)
        ),
        controls=[
            ft.Container(
                padding=20,
                content=ft.Column([
                    ft.Text("Guia Rápido AguaFlow", size=22,
                            weight="bold", color="blue"),
                    ft.Divider(height=20),

                    # Seção 1
                    ft.ExpansionTile(
                        title=ft.Text("Como realizar uma medição?"),
                        leading=ft.Icon(ft.Icons.CAMERA_ALT, color="green"),
                        controls=[
                            ft.ListTile(title=ft.Text(
                                "1. Clique em 'Realizar Leituras' no menu.")),
                            ft.ListTile(title=ft.Text(
                                "2. Aponte a câmera para o hidrômetro.")),
                            ft.ListTile(title=ft.Text(
                                "3. Confirme os números e clique em Salvar.")),
                        ]
                    ),

                    # Seção 2
                    ft.ExpansionTile(
                        title=ft.Text("Problemas com o Scanner (OCR)?"),
                        leading=ft.Icon(ft.Icons.BUG_REPORT, color="orange"),
                        controls=[
                            ft.ListTile(title=ft.Text(
                                "• Limpe o visor do hidrômetro.")),
                            ft.ListTile(title=ft.Text(
                                "• Evite reflexos de luz direta.")),
                            ft.ListTile(title=ft.Text(
                                "• Se falhar, use o ícone de 'Lápis' para digitar manual.")),
                        ]
                    ),

                    # Seção 3
                    ft.ExpansionTile(
                        title=ft.Text("Sincronização de Dados"),
                        leading=ft.Icon(ft.Icons.SYNC, color="blue"),
                        controls=[
                            ft.ListTile(title=ft.Text(
                                "Os dados são salvos localmente e podem ser enviados para a nuvem na aba 'Relatórios'.")),
                        ]
                    ),

                    ft.Divider(height=40),
                    ft.ElevatedButton(
                        "VOLTAR",
                        icon=ft.Icons.CHECK,
                        on_click=voltar,
                        width=400
                    )
                ], spacing=10, scroll=ft.ScrollMode.ADAPTIVE)
            )
        ]
    )
