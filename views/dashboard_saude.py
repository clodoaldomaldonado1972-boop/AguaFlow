import flet as ft
import os
import shutil
import platform
from views import styles as st
from views.sincronizacao import SincronizadorUI
from database.database import Database, get_supabase_client

def montar_tela_saude(page: ft.Page, ao_voltar):
    sincronizador = SincronizadorUI(page)

    # --- FUNÇÕES DE DIAGNÓSTICO EM TEMPO REAL ---
    def checar_db_local():
        try:
            with Database.get_db() as conn:
                conn.execute("SELECT 1")
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
        # Verifica espaço no disco/celular
        total, usado, livre = shutil.disk_usage("/")
        pct_livre = (livre / total) * 100
        if pct_livre > 15:
            return (f"{pct_livre:.1f}% LIVRE", "green")
        return ("ESPAÇO BAIXO", "orange")

    # --- COMPONENTE DE CARD DINÂMICO ---
    def criar_card_status(icone, titulo, func_check):
        status_texto, cor = func_check()
        return ft.Container(
            content=ft.ListTile(
                leading=ft.Icon(icone, color=cor, size=30),
                title=ft.Text(titulo, weight="bold", size=14, color="white"),
                trailing=ft.Text(status_texto, color=cor, weight="bold"),
            ),
            bgcolor="#1E2126",
            border_radius=10,
            padding=5,
            border=ft.border.all(1, "#33373E")
        )

    # Conteúdo da View
    status_db = criar_card_status(ft.icons.STORAGE, "Banco de Dados Local", checar_db_local)
    status_cloud = criar_card_status(ft.icons.CLOUD_DONE, "Conexão Supabase", checar_supabase)
    status_disk = criar_card_status(ft.icons.SD_CARD, "Armazenamento", checar_armazenamento)

    return ft.View(
        route="/dashboard_saude",
        bgcolor=st.BG_DARK,
        controls=[
            ft.AppBar(
                title=ft.Text("Saúde do Sistema"),
                bgcolor=st.PRIMARY_BLUE,
                leading=ft.IconButton(ft.icons.ARROW_BACK, on_click=ao_voltar),
                actions=[sincronizador.btn_sync] # Usa o botão de sync que já analisámos
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
                    ft.Text(f"AguaFlow Build: v1.1.2", size=11, color="grey70"),
                ], alignment=ft.MainAxisAlignment.CENTER)
            ], scroll=ft.ScrollMode.ADAPTIVE, expand=True)
        ]
    )