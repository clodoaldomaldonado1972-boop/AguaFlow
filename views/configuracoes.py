import flet as ft
import asyncio
import urllib.parse
from views import styles as st
from database.database import Database

# Tenta importar funções de backup se existirem no projeto
try:
    from database.backup import executar_backup_seguranca, limpar_backups_antigos
except ImportError:
    executar_backup_seguranca = None
    limpar_backups_antigos = None

async def montar_tela_configs(page: ft.Page, ao_voltar):
    """
    Monta a tela de configurações de forma assíncrona para evitar Timeouts 
    na leitura do client_storage.
    """
    
    def salvar_preferencia(chave, valor):
        page.client_storage.set(chave, valor)

    def abrir_ajuda_interna(e):
        page.go("/ajuda")

    def abrir_manual_externo(e):
        page.launch_url("https://docs.google.com/document/d/16K78tdhAwYScNKrxz4Qnw0g-AXXT-b3gv10UHFzX1SM/edit?tab=t.0#heading=h.9ijnxaq7oekf")

    def abrir_grafana(e):
        # Substituir pela URL real do Grafana do condomínio Vivere
        page.launch_url("https://clodoaldomaldonado1972boop.grafana.net/a/grafana-setupguide-app/getting-started")

    def abrir_suporte_whatsapp(e):
        telefone = "5518981337316"
        mensagem = "Olá Clodoaldo, preciso de suporte no app AguaFlow."
        url = f"https://wa.me/{telefone}?text={urllib.parse.quote(mensagem)}"
        page.launch_url(url)

    async def acao_backup(e):
        if not executar_backup_seguranca: return
        progresso_backup.visible = True
        page.update()
        # Executa o backup numa thread separada para não travar a UI
        resultado = await asyncio.to_thread(executar_backup_seguranca)
        progresso_backup.visible = False
        page.update()

    # LEITURA ASSÍNCRONA: Evita o erro "Timeout waiting for invokeMethod clientStorage:get"
    ocr_val = await page.client_storage.get_async("ocr_ativo")
    voz_val = await page.client_storage.get_async("voz_ativa")
    sync_val = await page.client_storage.get_async("sync_auto")

    # Define valores padrão caso seja a primeira execução
    ocr_val = ocr_val if ocr_val is not None else False
    voz_val = voz_val if voz_val is not None else False
    sync_val = sync_val if sync_val is not None else True

    # Componentes de Interface
    sw_ocr = ft.Switch(
        label="Leitura automática (OCR)", 
        value=ocr_val, 
        active_color=st.PRIMARY_BLUE, 
        on_change=lambda e: salvar_preferencia("ocr_ativo", e.control.value)
    )
    
    sw_voz = ft.Switch(
        label="Confirmar por voz", 
        value=voz_val, 
        active_color=st.PRIMARY_BLUE, 
        on_change=lambda e: salvar_preferencia("voz_ativa", e.control.value)
    )
    
    sw_sync = ft.Switch(
        label="Sincronismo automático", 
        value=sync_val, 
        active_color=st.PRIMARY_BLUE, 
        on_change=lambda e: salvar_preferencia("sync_auto", e.control.value)
    )
    
    progresso_backup = ft.ProgressBar(width=300, color=st.ACCENT_ORANGE, visible=False)

    return ft.View(
        route="/configuracoes",
        bgcolor=st.BG_DARK,
        padding=20,
        controls=[
            # Cabeçalho com botão voltar
            ft.Row([
                ft.IconButton(ft.icons.ARROW_BACK_IOS_NEW, on_click=ao_voltar), 
                ft.Column([
                    ft.Text("Configurações", style=st.TEXT_TITLE), 
                    ft.Text("Vivere Residencial", style=st.TEXT_SUB)
                ], spacing=0)
            ]),
            
            ft.Column([
                ft.Container(height=10),
                ft.Text("PREFERÊNCIAS", color=st.PRIMARY_BLUE, weight="bold", size=12),
                ft.Container(
                    content=ft.Column([sw_ocr, sw_voz, sw_sync], spacing=10), 
                    padding=15, bgcolor="#1E2126", border_radius=15
                ),
                
                ft.Container(height=15),
                ft.Text("MANUTENÇÃO", color=st.PRIMARY_BLUE, weight="bold", size=12),
                ft.Container(
                    content=ft.Column([
                        ft.ElevatedButton("Realizar Backup Agora", icon=ft.icons.BACKUP, on_click=acao_backup, style=st.BTN_MAIN),
                        progresso_backup
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER), 
                    padding=15, bgcolor="#1E2126", border_radius=15
                ),
                
                ft.Container(height=15),
                ft.Text("APOIO AO USUÁRIO", color=st.PRIMARY_BLUE, weight="bold", size=12),
                ft.Container(
                    content=ft.Column([
                        ft.ListTile(
                            leading=ft.Icon(ft.icons.DESCRIPTION, color=st.ACCENT_ORANGE), 
                            title=ft.Text("Manual do Usuário (Docs)", color=st.WHITE), 
                            on_click=abrir_manual_externo
                        ),
                        ft.ListTile(
                            leading=ft.Icon(ft.icons.HELP_CENTER, color=st.PRIMARY_BLUE), 
                            title=ft.Text("Central de Ajuda", color=st.WHITE), 
                            on_click=abrir_ajuda_interna
                        ),
                        ft.ListTile(
                            leading=ft.Icon(ft.icons.INSERT_CHART, color=ft.colors.ORANGE_700), 
                            title=ft.Text("Painel Grafana", color=st.WHITE), 
                            on_click=abrir_grafana
                        ),
                        ft.ListTile(
                            leading=ft.Icon(ft.icons.CHAT_ROUNDED, color=ft.colors.GREEN_ACCENT_700), 
                            title=ft.Text("Suporte via WhatsApp", color=st.WHITE), 
                            on_click=abrir_suporte_whatsapp
                        ),
                    ], spacing=5), 
                    padding=10, bgcolor="#1E2126", border_radius=15
                ),
            ], scroll=ft.ScrollMode.ADAPTIVE, expand=True),
            
            # Rodapé atualizado para a versão do build atual
            ft.Text("AguaFlow v1.1.1 - Residencial Vivere Prudente", size=10, color=st.GREY)
        ]
    )