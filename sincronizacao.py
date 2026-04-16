import flet as ft
from sync_engine import SyncEngine
from database.database import Database

class SincronizadorUI:
    """
    Classe responsável por gerenciar a interface do botão de nuvem.
    """
    def __init__(self, page: ft.Page):
        self.page = page
        self.btn_sync = ft.IconButton(
            icon=ft.icons.CLOUD_SYNC_ROUNDED,
            icon_color=ft.colors.GREY_400,
            tooltip="Sincronizar com Supabase",
            on_click=self.executar_sincronismo
        )
        self.txt_status = ft.Text("", size=12, color=ft.colors.BLUE_GREY_400)

    def executar_sincronismo(self, e):
        # 1. Feedback visual de início
        self.btn_sync.icon_color = ft.colors.BLUE_600
        self.btn_sync.disabled = True
        self.txt_status.value = "Sincronizando..."
        self.page.update()

        # 2. Chama o motor de sincronismo que você já possui
        # O SyncEngine vai ler o SQLite e enviar para o Supabase
        resultado = SyncEngine.sincronizar_agora()

        # 3. Feedback visual de conclusão
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(resultado),
            action="OK"
        )
        self.page.snack_bar.open = True
        
        self.btn_sync.icon_color = ft.colors.GREY_400
        self.btn_sync.disabled = False
        self.txt_status.value = ""
        self.page.update()

    def get_button(self):
        """Retorna o botão para ser inserido na AppBar."""
        return self.btn_sync