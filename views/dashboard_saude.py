import flet as ft
import os
import shutil
import platform
from views import styles as st
from flet import colors # Importar colors para uso direto
from views.sincronizacao import SincronizadorUI
from database.database import Database, get_supabase_client
# IMPORTAÇÃO DA AUTOMAÇÃO DE VERSÃO
from utils.updater import AppUpdater

def montar_tela_saude(page: ft.Page, ao_voltar):
    sincronizador = SincronizadorUI(page)

    # --- FUNÇÕES DE DIAGNÓSTICO ---
    def checar_db_local():
        try:
            with Database.get_db() as conn:
                conn.execute("SELECT 1")
            return ("CONECTADO", "green") # Usando strings para estabilidade[cite: 3]
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
            content=ft.ListTile( # icone is already a string here
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
    status_db = criar_card_status(ft.icons.STORAGE, "Banco de Dados Local", checar_db_local)
    status_cloud = criar_card_status(ft.icons.CLOUD_DONE, "Conexão Supabase", checar_supabase)
    status_disk = criar_card_status(ft.icons.SD_CARD, "Armazenamento", checar_armazenamento)

    return ft.View(
        route="/dashboard_saude",
        bgcolor="#121417", # Cor direta para evitar erro de modulo 'styles'[cite: 3]
        controls=[
            ft.AppBar(
                title=ft.Text("Saúde do Sistema"),
                bgcolor="blue", # String literal para evitar NameError[cite: 1, 3]
                leading=ft.IconButton(ft.icons.ARROW_BACK, on_click=ao_voltar),
                actions=[sincronizador.btn_sync]
            ),
            ft.Column([
                ft.Container(height=10),
                ft.Text(" MONITORAMENTO TÉCNICO", size=12, color="grey", weight="bold"),
                status_db,
                status_cloud,
                status_disk,
                
                ft.Container(height=20),
                ft.Text(" INFORMAÇÕES DO DISPOSITIVO", size=12, color="grey", weight="bold"),
                ft.Text(f"Sistema: {platform.system()} {platform.release()}", size=12, color="white70"),
                
                ft.Container(expand=True),
                ft.Divider(color="white10"),
                ft.Row([
                    # VERSÃO AUTOMÁTICA: Puxa direto do updater.py
                    ft.Text(AppUpdater.get_version_footer(), size=11, color="grey70"),
                ], alignment=ft.MainAxisAlignment.CENTER)
            ], scroll=ft.ScrollMode.ADAPTIVE, expand=True)
        ]
    )