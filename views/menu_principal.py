import flet as ft
from views import styles as st

def montar_menu(page, ir_para_medicao, ir_para_relatorios, ir_para_configs):
    perfil = page.session.get("perfil") 

    # O Container agora está DENTRO da função
    return ft.Container(
        expand=True,
        bgcolor=st.BG_DARK,
        padding=20,
        content=ft.Column([
            ft.Icon(ft.icons.WATER_DROP, size=60, color=st.PRIMARY_BLUE),
            ft.Text("Menu Principal", style=st.TEXT_TITLE),
            ft.Text(f"Bem-vindo, {perfil if perfil else 'Operador'}", color=st.GREY),
            
            ft.Divider(height=20, color=ft.colors.TRANSPARENT),

            ft.ElevatedButton(
                "REALIZAR LEITURAS", 
                icon=ft.icons.PLAY_ARROW, 
                on_click=ir_para_medicao, 
                style=st.BTN_SPECIAL, # Laranja
                width=320, height=60
            ),
            
            ft.ElevatedButton(
                "RELATÓRIOS E SYNC", 
                icon=ft.icons.INSERT_CHART, 
                on_click=ir_para_relatorios, 
                style=st.BTN_MAIN, # Azul
                width=320, height=60
            ),
            
            ft.ElevatedButton(
                "CONFIGURAÇÕES", 
                icon=ft.icons.SETTINGS, 
                on_click=ir_para_configs, 
                style=st.BTN_MAIN, 
                width=320, height=60
            ),
        ], horizontal_alignment="center", spacing=20)
    )