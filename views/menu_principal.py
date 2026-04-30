import flet as ft
import views.styles as st  # Importar estilos para cores


def montar_menu(page: ft.Page):
    """
    Monta a tela do menu principal, atuando como hub central para a navegação.
    """
    return ft.View(
        "/menu",
        [
            ft.AppBar(title=ft.Text("Menu Principal"),
                      bgcolor=st.PRIMARY_BLUE),
            ft.Column(
                [
                    ft.ElevatedButton(
                        "Medição",
                        icon="speed",
                        on_click=lambda _: page.go("/medicao"),
                        width=250,
                        height=50
                    ),
                    ft.ElevatedButton(
                        "Scanner",
                        icon="qr_code_scanner",
                        on_click=lambda _: page.go("/scanner"),
                        width=250,
                        height=50
                    ),
                    ft.ElevatedButton(
                        "Sincronizar Dados",
                        icon="cloud_upload",
                        on_click=lambda _: page.go("/sincronizar"),
                        width=250,
                        height=50
                    ),
                    ft.ElevatedButton(
                        "Dashboard de Saúde",
                        icon="health_and_safety",
                        on_click=lambda _: page.go("/dashboard_saude"),
                        width=250,
                        height=50
                    ),
                    ft.ElevatedButton(
                        "Configurações",
                        icon="settings",
                        on_click=lambda _: page.go("/configuracoes"),
                        width=250,
                        height=50
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True
            ),
            ft.ElevatedButton("Sair", on_click=lambda _: page.go("/")),
        ],
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )
