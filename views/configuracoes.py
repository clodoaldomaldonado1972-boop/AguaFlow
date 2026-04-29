import flet as ft
import asyncio
from views import styles as st
from utils.suporte_helper import SuporteHelper
from utils.backup import executar_backup_seguranca

async def montar_tela_configs(page: ft.Page, voltar_callback):
    user_email = page.session.get("user_email") or "Utilizador"

    async def obter_sync_auto():
        if hasattr(page, "client_storage") and page.client_storage:
            return await asyncio.wait_for(page.client_storage.get_async("sync_auto"), timeout=2.0)
        return page.session.get("sync_auto")

    def salvar_sync_auto(valor: bool):
        if hasattr(page, "client_storage") and page.client_storage:
            page.client_storage.set("sync_auto", valor)
        else:
            page.session.set("sync_auto", valor)

    try:
        sync_auto = await obter_sync_auto()
    except Exception:
        sync_auto = False

    return ft.View(
        route="/configuracoes",
        bgcolor=st.BG_DARK,
        appbar=ft.AppBar(
            title=ft.Text("Configurações Técnicas"),
            bgcolor=st.PRIMARY_BLUE,
            leading=ft.IconButton(ft.icons.ARROW_BACK, on_click=voltar_callback)
        ),
        controls=[
            ft.Column([
                ft.Container(height=10),
                
                # CARD: SISTEMA
                ft.Container(
                    content=ft.Column([
                        ft.Text(" SISTEMA E NUVEM", size=12, color="grey", weight="bold"),
                        ft.Switch(
                            label="Sincronização Automática",
                            value=sync_auto or False,
                            on_change=lambda e: salvar_sync_auto(e.control.value)
                        ),
                        ft.ListTile(
                            leading=ft.Icon(ft.icons.BACKUP, color=st.PRIMARY_BLUE),
                            title=ft.Text("Backup de Segurança", color=st.WHITE),
                            on_click=lambda _: executar_backup_seguranca()
                        ),
                    ]),
                    padding=15, bgcolor="#1E2126", border_radius=15
                ),

                # CARD: AUDITORIA E SUPORTE (Manual e Suporte Preservados)
                ft.Container(
                    content=ft.Column([
                        ft.Text(" AUDITORIA E SUPORTE", size=12, color="grey", weight="bold"),
                        ft.ListTile(
                            leading=ft.Icon(ft.icons.INSERT_CHART, color=ft.colors.ORANGE_700),
                            title=ft.Text("Painel Grafana (Cloud)", color=st.WHITE),
                            on_click=lambda _: page.launch_url("Sua_URL_do_Grafana")
                        ),
                        ft.ListTile(
                            leading=ft.Icon(ft.icons.DESCRIPTION, color=st.ACCENT_ORANGE),
                            title=ft.Text("Manual do Usuário", color=st.WHITE),
                            on_click=lambda _: SuporteHelper.abrir_manual(page)
                        ),
                        ft.ListTile(
                            leading=ft.Icon(ft.icons.CHAT_ROUNDED, color=ft.colors.GREEN_ACCENT_700),
                            title=ft.Text("Suporte WhatsApp", color=st.WHITE),
                            on_click=lambda _: SuporteHelper.abrir_whatsapp_suporte(page, user_email)
                        ),
                    ]),
                    padding=15, bgcolor="#1E2126", border_radius=15
                ),

                ft.Container(height=20),
                
                # CORREÇÃO DO ERRO ft.Center:
                ft.Container(
                    content=ft.Text("AguaFlow v1.1.2 - Residencial Vivere", size=11, color="grey600"),
                    alignment=ft.alignment.center # Alinhamento centralizado correto
                )
            ], scroll=ft.ScrollMode.ADAPTIVE, expand=True)
        ]
    )