import flet as ft
import os
import shutil
import platform
from views import styles as st
from views.sincronizacao import SincronizadorUI
from database.database import Database, get_supabase_client
from utils.auth_utils import validar_sessao
# IMPORTAÇÃO DA AUTOMAÇÃO DE VERSÃO e Path para o log
from utils.updater import AppUpdater
from pathlib import Path


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
        total, usado, livre = shutil.disk_usage("/")
        pct_livre = (livre / total) * 100
        if pct_livre > 15:
            return (f"{pct_livre:.1f}% LIVRE", "green")
        return ("ESPAÇO BAIXO", "orange")

    def criar_card_status(icone, titulo, func_check):
        status_texto, cor = func_check()
        return ft.Container(
            content=ft.ListTile(  # icone is already a string here
                leading=ft.Icon(icone, color=cor, size=30),
                title=ft.Text(titulo, weight="bold", size=14, color="white"),
                trailing=ft.Text(status_texto, color=cor, weight="bold"),
            ),
            bgcolor="#1E2126",
            border_radius=10,
            padding=5,
            border=ft.border.all(1, "#33373E")
        )

    # Componentes de interface atualizados
    status_db = criar_card_status(
        "storage", "Banco de Dados Local", checar_db_local)
    status_cloud = criar_card_status(
        "cloud_done", "Conexão Supabase", checar_supabase)
    status_disk = criar_card_status(
        "sd_card", "Armazenamento", checar_armazenamento)

    # --- LOG VIEWER ---
    # Define o caminho do arquivo de log de forma robusta
    log_file_path = Path(__file__).parent.parent / "logs" / "aguaflow.log"
    txt_log_content = ft.TextField(
        label="Conteúdo do Log",
        multiline=True,
        read_only=True,
        min_lines=10,
        max_lines=20,
        expand=True,
        bgcolor="#1E2126",
        border_color="#33373E",
        color="white",
        text_size=10,
        text_style=ft.TextStyle(font_family="monospace")
    )

    def carregar_log_file(e):
        try:
            if log_file_path.exists():
                with open(log_file_path, "r", encoding="utf-8") as f:
                    txt_log_content.value = f.read()
            else:
                txt_log_content.value = "Arquivo de log não encontrado."
        except Exception as ex:
            txt_log_content.value = f"Erro ao ler log: {ex}"
        page.update()

    carregar_log_file(None)

    return ft.View(
        route="/dashboard_saude",
        # Cor direta para evitar erro de modulo 'styles'[cite: 3]
        bgcolor="#121417",
        controls=[
            ft.AppBar(
                title=ft.Text("Saúde do Sistema"),
                # String literal para evitar NameError[cite: 1, 3]
                bgcolor="blue",
                leading=ft.IconButton("arrow_back", on_click=ao_voltar),
                actions=[sincronizador.btn_sync]
            ),
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
                txt_log_content,
                ft.Row([
                    ft.ElevatedButton(
                        "Atualizar Log",
                        icon="refresh",
                        on_click=carregar_log_file,
                        style=st.BTN_MAIN
                    ),
                    ft.ElevatedButton(
                        "Limpar Log",
                        icon="delete_sweep",
                        on_click=lambda e: (log_file_path.unlink(missing_ok=True), carregar_log_file(
                            None)),  # Limpa o arquivo e atualiza a exibição
                        style=ft.ButtonStyle(color="white", bgcolor="red")
                    )
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
