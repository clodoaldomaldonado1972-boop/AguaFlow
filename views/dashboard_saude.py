import flet as ft
from views import styles as st
from views.sincronizacao import SincronizadorUI

try:
    from utils.updater import VERSION
except ImportError:
    VERSION = "1.1.0"

def montar_tela_saude(page: ft.Page, ao_voltar):
    sincronizador = SincronizadorUI(page)

    def criar_card_status(icone, titulo, status, cor):
        return ft.Container(
            content=ft.ListTile(
                leading=ft.Icon(icone, color=cor, size=30),
                title=ft.Text(titulo, weight="bold", size=14),
                trailing=ft.Text(status, color=cor, weight="bold"),
            ),
            bgcolor="#1E2126",
            border_radius=10,
            padding=5,
            border=ft.border.all(1, "#33373E")
        )

    return ft.View(
        route="/dashboard_saude",
        bgcolor=st.BG_DARK,
        controls=[
            ft.AppBar(
                title=ft.Text("Saúde do Sistema"),
                bgcolor=st.PRIMARY_BLUE,
                leading=ft.IconButton(ft.icons.ARROW_BACK, on_click=ao_voltar),
                actions=[sincronizador.obter_componente()]
            ),
            ft.Column([
                ft.Text("MONITORAMENTO TÉCNICO", size=12, color="grey", weight="bold"),
                criar_card_status(ft.icons.STORAGE, "Banco de Dados Local", "CONECTADO", "blue"),
                criar_card_status(ft.icons.MEMORY, "Memória RAM (OCR)", "OTIMIZADO", "green"),
                criar_card_status(ft.icons.SD_CARD, "Armazenamento", "SAUDÁVEL", "green"),
                criar_card_status(ft.icons.CLOUD_DONE, "Conexão Supabase", "ONLINE", "green"),
                
                # Espaçador para empurrar a versão para o final
                ft.Container(expand=True),
                
                # --- RODAPÉ COM VERSÃO ---
                ft.Divider(color="white10"),
                ft.Row([
                    ft.Text(f"AguaFlow Build: v{VERSION}", size=11, color="grey700", italic=True),
                    ft.Text("Edifício Vivere Prudente", size=11, color="grey700"),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                
            ], expand=True, spacing=15)
        ]
    )