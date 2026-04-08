import flet as ft
# --- IMPORT CORRIGIDO PARA O NOVO ARQUIVO DE ESTILOS ---
from views import styles as st


def montar_menu(page, ir_para_leitura, ir_para_relatorios, ir_para_configs):
    # Recupera o perfil do usuário ou define como Operador por padrão
    perfil = getattr(page, "user_email", "Operador")

    return ft.Container(
        content=ft.Column([
            # Ícone principal com a cor vinda do styles.py
            ft.Icon(ft.Icons.WATER_DROP, size=60, color=st.PRIMARY_BLUE),

            ft.Text("Menu Principal", style=st.TEXT_TITLE),
            ft.Text(f"Bem-vindo, {perfil}", color=st.GREY, size=16),

            ft.Divider(height=20, color=ft.Colors.TRANSPARENT),

            # Botão de Leitura usando o estilo especial (Laranja)[cite: 4, 9]
            ft.ElevatedButton(
                "REALIZAR LEITURAS",
                icon=ft.Icons.PLAY_ARROW,
                on_click=ir_para_leitura,
                width=320,
                height=60,
                style=st.BTN_SPECIAL
            ),

            # Botão de Relatórios usando o estilo principal (Azul)[cite: 4, 9]
            ft.ElevatedButton(
                "RELATÓRIOS E SYNC",
                icon=ft.Icons.INSERT_CHART,
                on_click=ir_para_relatorios,
                width=320,
                height=60,
                style=st.BTN_MAIN
            ),

            # Botão de Configurações
            ft.ElevatedButton(
                "CONFIGURAÇÕES",
                icon=ft.Icons.SETTINGS,
                on_click=ir_para_configs,
                width=320,
                height=60,
                style=st.BTN_MAIN
            ),

        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20),
        alignment=ft.Alignment(0, 0),
        padding=20,
        expand=True,
        bgcolor="#121417"  # Garante o fundo escuro consistente com o main.py
    )
