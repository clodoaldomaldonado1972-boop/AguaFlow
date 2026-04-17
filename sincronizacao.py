import flet as ft
import asyncio
from sync_engine import SyncEngine
from database.database import Database

class SincronizadorUI:
    def __init__(self, page: ft.Page):
        self.page = page
        self.btn_sync = ft.IconButton(
            icon=ft.icons.CLOUD_SYNC_ROUNDED,
            icon_color=ft.colors.GREY_400,
            tooltip="Sincronizar com Supabase",
            on_click=self.executar_sincronismo
        )
        self.txt_status = ft.Text("", size=12, color=ft.colors.BLUE_GREY_400)

    async def executar_sincronismo(self, e):
        try:
            self.btn_sync.icon_color = ft.colors.BLUE_600
            self.btn_sync.disabled = True
            self.page.update()

            # Roda o processamento pesado em thread para não matar o loop de eventos
            resultado = await asyncio.to_thread(SyncEngine.sincronizar_agora)

            self.btn_sync.icon_color = ft.colors.GREEN_600
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Sucesso: {resultado}"),
                bgcolor=ft.colors.GREEN_700
            )
            
        except Exception as ex:
            self.btn_sync.icon_color = ft.colors.RED_600
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Erro na sincronia: {str(ex)}"),
                bgcolor=ft.colors.RED_700
            )
        
        finally:
            self.btn_sync.disabled = False
            self.page.snack_bar.open = True
            self.page.update()
            
            await asyncio.sleep(3)
            self.btn_sync.icon_color = ft.colors.GREY_400
            self.page.update()