import flet as ft

def montar_menu(page, ir_para_medicao, ir_para_relatorios, ir_para_configs):
    perfil = page.session.get("perfil") # Recupera quem logou

    return ft.Column([
        ft.Text("Menu Principal", size=24, weight="bold"),
        # CAMINHO 1: Vai para a tela de medição (Campo)
        ft.ElevatedButton("REALIZAR LEITURAS", icon=ft.icons.PLAY_ARROW, 
                          on_click=ir_para_medicao, width=320, height=60, bgcolor="orange", color="white"),
        
        # CAMINHO 2: Vai para Relatórios (Sincronização e Documentos)
        ft.ElevatedButton("RELATÓRIOS E SYNC", icon=ft.icons.INSERT_CHART, 
                          on_click=ir_para_relatorios, width=320, height=60),
        
        # CAMINHO 3: Vai para Configurações (Cadastros)
        ft.ElevatedButton("CONFIGURAÇÕES", icon=ft.icons.SETTINGS, 
                          on_click=ir_para_configs, width=320, height=60),
    ], horizontal_alignment="center", spacing=20)