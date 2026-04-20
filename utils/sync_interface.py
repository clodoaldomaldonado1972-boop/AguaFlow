import flet as ft
import asyncio
from database.sync_service import SyncService # Importa o motor que ajustamos antes

class BotaoSincronismo(ft.IconButton):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.icon = ft.icons.CLOUD_SYNC_ROUNDED
        self.icon_color = "#42A5F5" # Azul inicial (AguaFlow)
        self.tooltip = "Sincronizar dados com a Nuvem"
        self.on_click = self.disparar_sincronismo

    async def disparar_sincronismo(self, e):
        """
        Executa a animação visual e aciona o envio real dos dados.
        IHC: O feedback visual informa ao zelador que o app está trabalhando.
        """
        # 1. ESTADO: PROCESSANDO (Feedback visual de carregamento)
        self.icon = ft.icons.SYNC_ROUNDED
        self.icon_color = ft.colors.AMBER_400
        self.tooltip = "Enviando dados para o Supabase..."
        self.disabled = True # Bloqueia cliques repetidos
        self.page.update()

        # 2. AÇÃO REAL: Chama o motor de sincronismo
        # O processar_fila retorna a quantidade de registros sincronizados
        try:
            qtd_sincronizada = await SyncService.processar_fila()
            
            await asyncio.sleep(1.5) # Tempo técnico para o usuário perceber a mudança

            if qtd_sincronizada > 0:
                # 3. ESTADO: SUCESSO (Nuvem verde)
                self.icon = ft.icons.CLOUD_DONE_ROUNDED
                self.icon_color = ft.colors.GREEN_ACCENT_400
                msg = f"🚀 Sucesso! {qtd_sincronizada} leituras enviadas."
                cor_fundo = ft.colors.GREEN_800
            else:
                # Caso não houvesse nada para enviar, volta ao estado normal
                self.icon = ft.icons.CLOUD_QUEUE_ROUNDED
                self.icon_color = "#42A5F5"
                msg = "✅ O sistema já está atualizado."
                cor_fundo = ft.colors.BLUE_GREY_800

        except Exception as err:
            # 4. ESTADO: ERRO (Nuvem cortada)
            self.icon = ft.icons.CLOUD_OFF_ROUNDED
            self.icon_color = ft.colors.RED_ACCENT_400
            msg = f"❌ Falha na conexão: Verifique seu sinal."
            cor_fundo = ft.colors.RED_900

        # Mostra o resultado em uma barra de aviso (SnackBar)
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(msg, weight="bold"),
            bgcolor=cor_fundo,
            duration=3000
        )
        self.page.snack_bar.open = True
        
        # Restaura o botão para uso futuro
        self.disabled = False
        self.page.update()

    def set_page(self, page: ft.Page):
        """Método auxiliar para garantir a referência da página."""
        self.page = page