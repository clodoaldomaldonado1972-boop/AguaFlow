import flet as ft
from database.database import Database

def montar_tela_relatorios(page, voltar, sync_nuvem, gerar_e_enviar_pdf, gerar_qr):
    # --- DADOS REAIS DO BANCO ---
    total_unidades = 96
    historico = Database.buscar_ultimas_leituras(limite=96)
    lidas = len(historico)
    progresso = lidas / total_unidades if total_unidades > 0 else 0

    # --- COMPONENTE DASHBOARD ---
    dashboard = ft.Container(
        content=ft.Column([
            ft.Text("Progresso Vivere Prudente", size=18, weight="bold"),
            ft.ProgressBar(value=progresso, width=320, color="blue", bgcolor="grey300"),
            ft.Row([
                ft.Text(f"Lidas: {lidas}", color="blue", weight="bold"),
                ft.Text(f"Pendentes: {total_unidades - lidas}", color="orange", weight="bold"),
            ], alignment="spaceBetween", width=320),
        ], horizontal_alignment="center"),
        padding=20, border=ft.border.all(1, "grey300"), border_radius=10, bgcolor="white"
    )

    return ft.Container(
        padding=20,
        content=ft.Column([
            ft.Text("Gestão e Relatórios", size=24, weight="bold"),
            dashboard,
            ft.Divider(height=20),
            
            # Botão Consolidado: Gera o PDF e já prepara para o e-mail
            ft.ElevatedButton(
                "GERAR PDF E ENVIAR E-MAIL", 
                icon=ft.icons.EMAIL_OUTLINED, 
                on_click=gerar_e_enviar_pdf, 
                width=320, height=55, bgcolor="blue", color="white"
            ),
            
            ft.ElevatedButton(
                "SINCRONIZAR NUVEM", 
                icon=ft.icons.CLOUD_SYNC, 
                on_click=sync_nuvem, 
                width=320, height=50, bgcolor="green700", color="white"
            ),

            ft.OutlinedButton(
                "REIMPRIMIR ETIQUETAS QR", 
                icon=ft.icons.QR_CODE, 
                on_click=gerar_qr, 
                width=320, height=50
            ),

            ft.TextButton("Voltar ao Menu Principal", on_click=voltar)
        ], horizontal_alignment="center", spacing=15)
    )