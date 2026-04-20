import flet as ft
import asyncio
import urllib.parse
from views import styles as st
from database.database import Database

# Bloco de importação resiliente
try:
    from database.backup import executar_backup_seguranca, limpar_backups_antigos
except ImportError:
    executar_backup_seguranca = None
    limpar_backups_antigos = None

def montar_tela_configs(page: ft.Page, ao_voltar):
    # --- FUNÇÕES DE LÓGICA ---
    def salvar_preferencia(chave, valor):
        page.client_storage.set(chave, valor)
        print(f"DEBUG [Storage]: {chave} -> {valor}")

    def abrir_ajuda(e):
        page.launch_url("https://vivere.com.br/manual")

    def abrir_suporte_whatsapp(e):
        """Lógica corrigida: removemos o ícone problemático e validamos a URL."""
        telefone = "5518981337316" # Substitua pelo seu número
        mensagem = "Olá Clodoaldo, preciso de suporte no app AguaFlow."
        msg_encoded = urllib.parse.quote(mensagem)
        url = f"https://wa.me/{telefone}?text={msg_encoded}"
        try:
            page.launch_url(url)
        except Exception as err:
            print(f"Erro ao abrir link: {err}")

    async def acao_backup(e):
        if not executar_backup_seguranca:
            page.snack_bar = ft.SnackBar(ft.Text("❌ Função de backup não disponível."), bgcolor=st.ERROR_COLOR)
            page.snack_bar.open = True
            page.update()
            return
        
        progresso_backup.visible = True
        page.update()
        resultado = await asyncio.to_thread(executar_backup_seguranca)
        progresso_backup.visible = False
        
        page.snack_bar = ft.SnackBar(
            ft.Text("✅ Backup concluído!" if resultado else "❌ Falha no backup"), 
            bgcolor=st.SUCCESS_GREEN if resultado else st.ERROR_COLOR
        )
        page.snack_bar.open = True
        page.update()

    # --- COMPONENTES ---
    sw_ocr = ft.Switch(label="Leitura automática (OCR)", label_style=ft.TextStyle(color=st.WHITE), value=page.client_storage.get("ocr_ativo") or False, active_color=st.PRIMARY_BLUE, on_change=lambda e: salvar_preferencia("ocr_ativo", e.control.value))
    sw_voz = ft.Switch(label="Confirmar por voz", label_style=ft.TextStyle(color=st.WHITE), value=page.client_storage.get("voz_ativa") or False, active_color=st.PRIMARY_BLUE, on_change=lambda e: salvar_preferencia("voz_ativa", e.control.value))
    sw_sync = ft.Switch(label="Sincronismo automático", label_style=ft.TextStyle(color=st.WHITE), value=page.client_storage.get("sync_auto") or True, active_color=st.PRIMARY_BLUE, on_change=lambda e: salvar_preferencia("sync_auto", e.control.value))

    progresso_backup = ft.ProgressBar(width=300, color=st.ACCENT_ORANGE, visible=False)

    # --- MONTAGEM DA VIEW ---
    return ft.View(
        route="/configuracoes",
        bgcolor=st.BG_DARK,
        padding=20,
        controls=[
            ft.Row([
                ft.IconButton(ft.icons.ARROW_BACK_IOS_NEW, icon_color=st.WHITE, on_click=ao_voltar),
                ft.Column([
                    ft.Text("Configurações", style=st.TEXT_TITLE),
                    ft.Text("Vivere Residencial", style=st.TEXT_SUB)
                ], spacing=0)
            ]),
            
            ft.Column([
                ft.Container(height=10),
                ft.Text("PREFERÊNCIAS", color=st.PRIMARY_BLUE, weight="bold", size=12),
                ft.Container(content=ft.Column([sw_ocr, sw_voz, sw_sync], spacing=10), padding=15, bgcolor="#1E2126", border_radius=15),
                
                ft.Container(height=15),
                ft.Text("MANUTENÇÃO", color=st.PRIMARY_BLUE, weight="bold", size=12),
                ft.Container(content=ft.Column([
                    ft.ElevatedButton("Realizar Backup Agora", icon=ft.icons.BACKUP, on_click=acao_backup, style=st.BTN_MAIN),
                    progresso_backup
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER), padding=15, bgcolor="#1E2126", border_radius=15),

                ft.Container(height=15),
                ft.Text("APOIO AO USUÁRIO", color=st.PRIMARY_BLUE, weight="bold", size=12),
                ft.Container(content=ft.Column([
                    ft.ListTile(
                        leading=ft.Icon(ft.icons.HELP_CENTER, color=st.ACCENT_ORANGE), 
                        title=ft.Text("Manual do Usuário", color=st.WHITE), 
                        on_click=abrir_ajuda
                    ),
                    ft.ListTile(
                        # CORREÇÃO: Ícone alterado para evitar erro de atributo
                        leading=ft.Icon(ft.icons.CHAT_ROUNDED, color=ft.colors.GREEN_ACCENT_700), 
                        title=ft.Text("Suporte via WhatsApp", color=st.WHITE), 
                        on_click=abrir_suporte_whatsapp
                    ),
                ], spacing=5), padding=10, bgcolor="#1E2126", border_radius=15),

            ], scroll=ft.ScrollMode.ADAPTIVE, expand=True),
            
            ft.Container(expand=True), 
            ft.Text("AguaFlow v1.0.2 - Residencial Vivere Prudente", size=10, color=st.GREY)
        ]
    )