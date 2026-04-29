import flet as ft
import asyncio
from database.sync_service import SyncService
from utils.backup import executar_backup_seguranca
from database.database import Database
from views import styles as st

def montar_tela_sincronizacao(page: ft.Page):
    """
    Tela de sincronização com a nuvem Supabase.
    Mostra status, histórico e permite sincronização manual.
    """
    sincronizador = SincronizadorUI(page)

    lbl_status_geral = ft.Text("Verificando conexão...", size=14, color="grey")
    lbl_ultimasinc = ft.Text("Última sincronização: --", size=12, color="grey")
    lista_logs = ft.ListView(expand=True, spacing=10, padding=10, height=200)

    async def verificar_status(e):
        """Verifica o status da sincronização e exibe logs recentes."""
        lbl_status_geral.value = "Verificando..."
        page.update()

        try:
            # Verifica se há leituras pendentes
            with Database.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM leituras WHERE sincronizado = 0")
                pendentes = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM leituras WHERE sincronizado = 1")
                sincronizadas = cursor.fetchone()[0]

                lbl_status_geral.value = f"Pendentes: {pendentes} | Sincronizadas: {sincronizadas}"
                lbl_status_geral.color = "green" if pendentes == 0 else "orange"

            lbl_ultimasinc.value = "Status atualizado em tempo real"

        except Exception as ex:
            lbl_status_geral.value = f"Erro: {str(ex)}"
            lbl_status_geral.color = "red"

        page.update()

    async def sincronizar_agora(e):
        """Executa sincronização manual."""
        await sincronizador.executar_sincronismo(e)
        await verificar_status(None)

    return ft.View(
        route="/sincronizar",
        bgcolor=st.BG_DARK,
        controls=[
            ft.AppBar(
                title=ft.Text("Sincronização com Nuvem"),
                bgcolor=st.PRIMARY_BLUE,
                leading=ft.IconButton(ft.icons.ARROW_BACK, on_click=lambda _: page.go("/menu"))
            ),
            ft.Column([
                ft.Container(height=20),

                # Card de Status
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.icons.CLOUD_SYNC, size=50, color=st.PRIMARY_BLUE),
                        ft.Text("STATUS DA SINCRONIZAÇÃO", size=16, weight="bold"),
                        lbl_status_geral,
                        lbl_ultimasinc,
                    ], horizontal_alignment="center"),
                    padding=20,
                    bgcolor="#1E2126",
                    border_radius=15,
                    width=400
                ),

                ft.Container(height=20),

                # Botões de Ação
                ft.Row([
                    ft.ElevatedButton(
                        "SINCRONIZAR AGORA",
                        icon=ft.icons.CLOUD_UPLOAD,
                        on_click=sincronizar_agora,
                        style=st.BTN_MAIN,
                        width=200,
                        height=55
                    ),
                    ft.ElevatedButton(
                        "ATUALIZAR STATUS",
                        icon=ft.icons.REFRESH,
                        on_click=verificar_status,
                        width=200,
                        height=55
                    ),
                ], alignment=ft.MainAxisAlignment.CENTER),

                ft.Container(height=20),

                # Informações
                ft.Text("Informações", size=14, weight="bold"),
                ft.Container(
                    content=ft.Column([
                        ft.Text("• As leituras são enviadas automaticamente quando há internet", size=12),
                        ft.Text("• Backup local é gerado após cada sincronização", size=12),
                        ft.Text("• Erros são registrados em logs para auditoria", size=12),
                    ], spacing=5),
                    padding=15,
                    bgcolor="#1E2126",
                    border_radius=10,
                    width=400
                ),

                ft.Container(expand=True),
                ft.TextButton("Voltar ao Menu", on_click=lambda _: page.go("/menu"))

            ], horizontal_alignment="center", scroll=ft.ScrollMode.ADAPTIVE)
        ]
    )


class SincronizadorUI:
    def __init__(self, page: ft.Page):
        self.page = page
        self.btn_sync = ft.IconButton(
            icon=ft.icons.CLOUD_UPLOAD,
            tooltip="Sincronizar com Nuvem",
            on_click=lambda e: page.run_task(SyncService.processar_fila)
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