import flet as ft
import asyncio
from utils.sync_engine import SyncEngine

class BotaoSincronismo(ft.IconButton):
    def __init__(self):
        super().__init__()
        self.icon = ft.icons.CLOUD_SYNC_ROUNDED
        self.icon_color = "#42A5F5"
        self.tooltip = "Sincronizar Dados"
        self.on_click = self.disparar_animacao

    async def disparar_animacao(self, e):
        """Executa a animação visual e a sincronização real."""
        page = e.page # Captura a página do evento para evitar erros de NoneType
        
        # 1. ESTADO: SUBINDO (Seta para cima)
        self.icon = ft.icons.UPGRADE_ROUNDED
        self.icon_color = ft.colors.AMBER_400
        self.tooltip = "A enviar para a nuvem..."
        self.disabled = True
        page.update()

        # Chama a sincronização real
        resultado = SyncEngine.sincronizar_agora()
        
        await asyncio.sleep(1) # Tempo para o utilizador ver a animação

        # 2. ESTADO: RESULTADO (Sucesso ou Erro)
        if "🚀" in resultado or "✅" in resultado:
            self.icon = ft.icons.CLOUD_DONE_ROUNDED
            self.icon_color = ft.colors.GREEN_ACCENT
        else:
            self.icon = ft.icons.CLOUD_OFF_ROUNDED
            self.icon_color = ft.colors.RED_ACCENT

        # Mostra mensagem de feedback
        page.snack_bar = ft.SnackBar(
            content=ft.Text(resultado),
            bgcolor="#2E7D32" if "🚀" in resultado else "#C62828"
        )
        page.snack_bar.open = True
        page.update()

        # 3. RESET: Volta ao ícone normal após 3 segundos
        await asyncio.sleep(3)
        self.icon = ft.icons.CLOUD_SYNC_ROUNDED
        self.icon_color = "#42A5F5"
        self.disabled = False
        page.update()