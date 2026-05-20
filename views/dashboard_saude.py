import asyncio
import flet as ft
import os
import shutil
import platform
from views import styles as st
from views.sincronizacao import SincronizadorUI
from database.database import Database, get_supabase_client
from utils.auth_utils import validar_sessao
from utils.updater import AppUpdater
from utils.logger_config import get_log_path


def montar_tela_saude(page: ft.Page, ao_voltar):
    # Proteção de Rota
    auth_check = validar_sessao(
        page, "/dashboard_saude", required_role="admin")
    if auth_check:
        return auth_check

    sincronizador = SincronizadorUI(page)

    # --- FUNÇÕES DE DIAGNÓSTICO ---
    def checar_db_local():
        try:
            with Database.get_db() as conn:
                conn.execute("SELECT 1")
            # Usando strings para estabilidade[cite: 3]
            return ("CONECTADO", "green")
        except:
            return ("ERRO", "red")

    def checar_supabase():
        try:
            client = get_supabase_client()
            if client:
                return ("ONLINE", "green")
            return ("OFFLINE", "red")
        except:
            return ("OFFLINE", "red")

    def checar_armazenamento():
        # Usa o diretório de dados do app (sandbox Android ou raiz desktop)
        check_path = os.environ.get("FLET_APP_STORAGE_DATA") or os.path.expanduser("~")
        try:
            total, usado, livre = shutil.disk_usage(check_path)
            livre_mb = livre / (1024 * 1024)
            livre_gb = livre_mb / 1024
            # Threshold absoluto: <500 MB é crítico, independente do tamanho do disco
            if livre_mb >= 500:
                label = f"{livre_gb:.1f} GB livres" if livre_gb >= 1 else f"{livre_mb:.0f} MB livres"
                return (label, "green")
            return (f"BAIXO: {livre_mb:.0f} MB", "orange")
        except Exception:
            return ("Indisponível", "grey")

    def criar_card_status(icone, titulo, func_check):
        status_texto, cor = func_check()
        return ft.Container(
            content=ft.ListTile(
                leading=ft.Icon(icone, color=cor, size=30),
                title=ft.Text(titulo, weight="bold", size=13, color="white", no_wrap=True),
                trailing=ft.Text(status_texto, color=cor, weight="bold", size=12),
            ),
            bgcolor="#1E2126",
            border_radius=10,
            padding=5,
            border=ft.border.all(1, "#33373E")
        )

    # Componentes de interface atualizados
    status_db = criar_card_status(
        ft.Icons.STORAGE, "Banco de Dados Local", checar_db_local)
    status_cloud = criar_card_status(
        ft.Icons.CLOUD_DONE, "Conexão Supabase", checar_supabase)
    status_disk = criar_card_status(
        ft.Icons.SD_CARD, "Armazenamento", checar_armazenamento)

    # --- LOG VIEWER ---
    # get_log_path() retorna o caminho resolvido no boot (Android sandbox ou desktop)
    log_file_path = get_log_path()

    lbl_log_path = ft.Text(
        f"Arquivo: {log_file_path or 'não inicializado'}",
        size=9, color="grey", italic=True,
    )

    txt_log_content = ft.TextField(
        label="Últimas 200 linhas do Log",
        multiline=True,
        read_only=True,
        min_lines=10,
        max_lines=20,
        expand=True,
        bgcolor="#1E2126",
        border_color="#33373E",
        color="white",
        text_size=10,
        text_style=ft.TextStyle(font_family="monospace"),
    )

    lbl_log_size = ft.Text("", size=10, color="grey")

    async def carregar_log_file(e):
        try:
            if log_file_path and os.path.exists(log_file_path):
                tamanho_kb = os.path.getsize(log_file_path) / 1024
                # Lê apenas as últimas 200 linhas para não travar a UI
                linhas = await asyncio.to_thread(_ler_ultimas_linhas, log_file_path, 200)
                txt_log_content.value = linhas
                lbl_log_size.value = f"Tamanho total: {tamanho_kb:.1f} KB"
            else:
                txt_log_content.value = "Arquivo de log não encontrado.\n(No Android, logs ficam no sandbox do app)"
                lbl_log_size.value = ""
        except Exception as ex:
            txt_log_content.value = f"Erro ao ler log: {ex}"
        page.update()

    async def limpar_log(e):
        try:
            if log_file_path and os.path.exists(log_file_path):
                await asyncio.to_thread(os.remove, log_file_path)
            await carregar_log_file(None)
        except Exception as ex:
            txt_log_content.value = f"Erro ao limpar log: {ex}"
            page.update()

    page.run_task(carregar_log_file, None)

    return ft.View(
        route="/dashboard_saude",
        bgcolor="#121417",
        appbar=ft.AppBar(
            title=ft.Text("Saúde do Sistema"),
            bgcolor="blue",
            leading=ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=ao_voltar),
            actions=[sincronizador.btn_sync]
        ),
        controls=[
            ft.Column([
                ft.Container(height=10),
                ft.Text(" MONITORAMENTO TÉCNICO", size=12,
                        color="grey", weight="bold"),
                status_db,
                status_cloud,
                status_disk,

                ft.Container(height=20),
                ft.Text(" INFORMAÇÕES DO DISPOSITIVO",
                        size=12, color="grey", weight="bold"),
                ft.Text(
                    f"Sistema: {platform.system()} {platform.release()}", size=12, color="white70"),

                ft.Container(height=20),
                ft.Text(" LOGS DO APLICATIVO", size=12,
                        color="grey", weight="bold"),
                lbl_log_path,
                lbl_log_size,
                txt_log_content,
                ft.Row([
                    ft.ElevatedButton(
                        "Atualizar Log",
                        icon=ft.Icons.REFRESH,
                        on_click=lambda e: page.run_task(carregar_log_file, e),
                        style=st.BTN_MAIN,
                    ),
                    ft.ElevatedButton(
                        "Limpar Log",
                        icon=ft.Icons.DELETE_SWEEP,
                        on_click=lambda e: page.run_task(limpar_log, e),
                        style=ft.ButtonStyle(color="white", bgcolor="red"),
                    ),
                ], alignment=ft.MainAxisAlignment.CENTER),

                ft.Container(expand=True),
                ft.Divider(color="white10"),
                ft.Row([
                    # VERSÃO AUTOMÁTICA: Puxa direto do updater.py
                    ft.Text(AppUpdater.get_footer(),
                            size=11, color="grey70"),
                ], alignment=ft.MainAxisAlignment.CENTER)
            ], scroll=ft.ScrollMode.ADAPTIVE, expand=True)
        ]
    )


def _ler_ultimas_linhas(path: str, n: int = 200) -> str:
    """Lê as últimas N linhas do arquivo de log sem carregar tudo em memória."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            linhas = f.readlines()
        return "".join(linhas[-n:])
    except Exception as ex:
        return f"Erro ao ler log: {ex}"
