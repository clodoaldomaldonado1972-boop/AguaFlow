import flet as ft
import asyncio
from database.sync_service import SyncService # Integração com o motor de busca
from utils.backup import executar_backup_seguranca # Integração com o Backup
from database.database import Database

class SincronizadorUI:
    def __init__(self, page: ft.Page):
        # Dentro da classe SincronizadorUI ou na função que cria o botão
        self.btn_sync = ft.IconButton(
            icon=ft.icons.CLOUD_UPLOAD,
            tooltip="Sincronizar com Nuvem",
            # CORREÇÃO AQUI: Use page.run_task para não travar a interface
            on_click=lambda e: self.page.run_task(SyncService.processar_fila)
        )
        self.txt_status = ft.Text("", size=12, color=ft.colors.BLUE_GREY_400)

    async def executar_sincronismo(self, e):
        """
        Orquestra o processo de envio para nuvem e geração de backup local.
        """
        try:
            # 1. ESTADO: INICIANDO
            self.btn_sync.icon_color = ft.colors.BLUE_600
            self.btn_sync.disabled = True
            self.txt_status.value = "Conectando ao servidor..."
            self.page.update()

            # 2. AÇÃO: Processamento do Sincronismo
            # Usamos to_thread para que o upload pesado não trave a interface (UI)
            qtd_sincronizada = await asyncio.to_thread(SyncService.processar_fila)

            # 3. AÇÃO COMPLEMENTAR: Backup Automático
            # IHC: Segurança de dados - se subiu para a nuvem, garantimos uma cópia local atualizada
            if qtd_sincronizada > 0:
                await asyncio.to_thread(executar_backup_seguranca)
                feedback_msg = f"Sucesso: {qtd_sincronizada} leituras enviadas e backup gerado!"
                self.btn_sync.icon_color = ft.colors.GREEN_600
            else:
                feedback_msg = "O sistema já está atualizado."
                self.btn_sync.icon_color = ft.colors.BLUE_GREY_200

            # 4. FEEDBACK AO USUÁRIO
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(feedback_msg),
                bgcolor=ft.colors.GREEN_700 if qtd_sincronizada > 0 else ft.colors.BLUE_GREY_800,
                open=True
            )
            
            self.txt_status.value = "Sincronizado"
            
        except Exception as ex:
            # 5. TRATAMENTO DE ERRO (Ex: Falta de internet no condomínio)
            self.btn_sync.icon_color = ft.colors.RED_600
            self.btn_sync.disabled = False
            self.txt_status.value = "Erro na sincronia"
            
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Erro: Verifique sua conexão. {str(ex)}"),
                bgcolor=ft.colors.RED_700,
                open=True
            )
        
        finally:
            self.btn_sync.disabled = False
            self.page.update()

    def obter_componente(self):
        """Retorna o botão para ser inserido em qualquer AppBar ou Menu."""
        return self.btn_sync