import flet as ft
from views import styles as st


def montar_menu(page, ir_para_medicao, ir_para_relatorios, ir_para_configs):
    # Recupera o que foi salvo no login via page.data
    perfil = page.data if page.data else "Operador"

    return ft.View(
        route="/menu",
        bgcolor=st.BG_DARK,
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Container(
                content=ft.Column([
                    # Ícone e Título
                    ft.Icon(ft.Icons.WATER_DROP, size=60,
                            color=st.PRIMARY_BLUE),
                    ft.Text("Menu Principal", style=st.TEXT_TITLE),

                    # Texto de Boas-vindas corrigido
                    ft.Text(f"Bem-vindo, {perfil}", color=st.GREY, size=16),

                    # Espaçador transparente
                    ft.Divider(height=20, color=ft.Colors.TRANSPARENT),

                    # Botão Principal: Medição
                    ft.ElevatedButton(
                        "REALIZAR LEITURAS",
                        icon=ft.Icons.PLAY_ARROW,
                        on_click=ir_para_medicao,
                        style=st.BTN_SPECIAL,  # Laranja
                        width=320, height=60
                    ),

                    # Botão: Relatórios e Sincronização
                    ft.ElevatedButton(
                        "RELATÓRIOS E SYNC",
                        icon=ft.Icons.INSERT_CHART,
                        on_click=ir_para_relatorios,
                        style=st.BTN_MAIN,  # Azul
                        width=320, height=60
                    ),

                    # Botão: Configurações
                    ft.ElevatedButton(
                        "CONFIGURAÇÕES",
                        icon=ft.Icons.SETTINGS,
                        on_click=ir_para_configs,
                        style=st.BTN_MAIN,
                        width=320, height=60
                    ),
                ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=20
                )
            )
        ]
    )
