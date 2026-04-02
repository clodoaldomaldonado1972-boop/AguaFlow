import flet as ft
from views import styles as st


def montar_menu(page, ir_para_medicao, ir_para_relatorios, ir_para_configs):
    # Recupera o perfil salvo na sessão após o login
    perfil = page.session.get("perfil")

    return ft.View(
        route="/menu",
        bgcolor=st.BG_DARK,
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Container(
                content=ft.Column([
                    # Correção: Icons e Colors com Inicial Maiúscula
                    ft.Icon(ft.Icons.WATER_DROP, size=60,
                            color=st.PRIMARY_BLUE),
                    ft.Text("Menu Principal", style=st.TEXT_TITLE),
                    ft.Text(
                        f"Bem-vindo, {perfil if perfil else 'Operador'}", color=st.GREY),

                    ft.Divider(height=20, color=ft.Colors.TRANSPARENT),

                    ft.ElevatedButton(
                        "REALIZAR LEITURAS",
                        icon=ft.Icons.PLAY_ARROW,
                        on_click=ir_para_medicao,
                        # Laranja (Destaque para a ação principal)
                        style=st.BTN_SPECIAL,
                        width=320, height=60
                    ),

                    ft.ElevatedButton(
                        "RELATÓRIOS E SYNC",
                        icon=ft.Icons.INSERT_CHART,
                        on_click=ir_para_relatorios,
                        style=st.BTN_MAIN,  # Azul
                        width=320, height=60
                    ),

                    ft.ElevatedButton(
                        "CONFIGURAÇÕES",
                        icon=ft.Icons.SETTINGS,
                        on_click=ir_para_configs,
                        style=st.BTN_MAIN,
                        width=320, height=60
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20)
            )
        ]
    )
