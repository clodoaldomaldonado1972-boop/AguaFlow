import flet as ft
import asyncio
from sync_engine import SyncEngine
from database.database import Database

class SincronizadorUI:
    """
    Classe responsável por gerenciar a interface do botão de nuvem.
    Ajustada para suportar execução assíncrona e evitar travamentos no Python 3.14.
    """
    def __init__(self, page: ft.Page):
        self.page = page
        # O botão inicia com a cor padrão (cinza)
        self.btn_sync = ft.IconButton(
            icon=ft.icons.CLOUD_SYNC_ROUNDED,
            icon_color=ft.colors.GREY_400,
            tooltip="Sincronizar com Supabase",
            on_click=self.executar_sincronismo
        )
        self.txt_status = ft.Text("", size=12, color=ft.colors.BLUE_GREY_400)

    async def executar_sincronismo(self, e):
        try:
            # 1. Feedback visual de início (Mudança para Azul)
            self.btn_sync.icon_color = ft.colors.BLUE_600
            self.btn_sync.disabled = True
            self.txt_status.value = "Sincronizando..."
            self.page.update()

            # 2. Chamada assíncrona para não travar a UI
            # O to_thread é vital para que a rede não bloqueie o loop de eventos
            resultado = await asyncio.to_thread(SyncEngine.sincronizar_agora)

            # 3. Feedback visual de conclusão (Sucesso - Verde)
            self.btn_sync.icon_color = ft.colors.GREEN_600
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Sucesso: {resultado}"),
                bgcolor=ft.colors.GREEN_700
            )
            
        except Exception as ex:
            # 4. Feedback em caso de erro (Vermelho)
            # Agora o erro real aparecerá na SnackBar para sabermos o que falhou
            self.btn_sync.icon_color = ft.colors.RED_600
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Erro na sincronia: {str(ex)}"),
                bgcolor=ft.colors.RED_700
            )
        
        finally:
            # 5. Restaura o estado do botão e exibe a mensagem
            self.btn_sync.disabled = False
            self.txt_status.value = ""
            self.page.snack_bar.open = True
            self.page.update()
            
            # Aguarda 3 segundos para o utilizador ver o estado e volta ao cinza
            await asyncio.sleep(3)
            self.btn_sync.icon_color = ft.colors.GREY_400
            self.page.update()