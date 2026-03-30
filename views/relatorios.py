import flet as ft
from database.database import Database
from views import styles as st # Usando seus estilos centralizados

def montar_tela_relatorios(page, voltar, sync_nuvem, gerar_e_enviar_pdf, gerar_qr):
    # --- BUSCA DE DADOS REAIS ---
    total_unidades = 96
    # Garante que a busca no SQLite funcione antes de renderizar
    try:
        historico = Database.buscar_ultimas_leituras(limite=96)
        lidas = len(historico)
    except:
        lidas = 0
    
    progresso = lidas / total_unidades if total_unidades > 0 else 0

    # --- COMPONENTE DASHBOARD (ESTILO DARK) ---
    dashboard = ft.Container(
        content=ft.Column([
            ft.Text("Progresso Vivere Prudente", size=18, weight="bold", color=st.WHITE),
            ft.ProgressBar(
                value=progresso, 
                width=350, 
                color=st.PRIMARY_BLUE, 
                bgcolor=ft.colors.with_opacity(0.1, st.WHITE)
            ),
            ft.Row([
                ft.Text(f"Lidas: {lidas}", color=st.PRIMARY_BLUE, weight="bold"),
                ft.Text(f"Pendentes: {total_unidades - lidas}", color=ft.colors.ORANGE_700, weight="bold"),
            ], alignment="spaceBetween", width=350),
        ], horizontal_alignment="center"),
        padding=25,
        border=ft.border.all(1, ft.colors.with_opacity(0.1, st.WHITE)),
        border_radius=15,
        bgcolor=ft.colors.with_opacity(0.05, st.WHITE) # Fundo levemente visível no modo dark
    )

    return ft.Container(
        expand=True,
        padding=20,
        content=ft.Column([
            # Cabeçalho
            ft.Row([
                ft.Icon(ft.icons.ASSESSMENT_ROUNDED, color=st.PRIMARY_BLUE, size=30),
                ft.Text("Gestão e Relatórios", size=26, weight="bold", color=st.WHITE),
            ], alignment="center"),
            
            ft.Divider(height=10, color=ft.colors.TRANSPARENT),
            
            dashboard,
            
            ft.Divider(height=20, color=ft.colors.with_opacity(0.1, st.WHITE)),
            
            # Botões de Ação
            ft.Column([
                ft.ElevatedButton(
                    "GERAR PDF E ENVIAR E-MAIL", 
                    icon=ft.icons.SEND_ROUNDED, 
                    on_click=gerar_e_enviar_pdf, 
                    style=st.BTN_MAIN, # Usando seu estilo de botão azul
                    width=350, height=55
                ),
                
                ft.ElevatedButton(
                    "SINCRONIZAR COM NUVEM", 
                    icon=ft.icons.CLOUD_SYNC_ROUNDED, 
                    on_click=sync_nuvem, 
                    width=350, height=50,
                    style=ft.ButtonStyle(
                        color=st.WHITE,
                        bgcolor=ft.colors.GREEN_800,
                        shape=ft.RoundedRectangleBorder(radius=8)
                    )
                ),

                ft.OutlinedButton(
                    "REIMPRIMIR ETIQUETAS QR", 
                    icon=ft.icons.QR_CODE_2_ROUNDED, 
                    on_click=gerar_qr, 
                    width=350, height=50,
                    style=ft.ButtonStyle(color=st.GREY)
                ),
            ], horizontal_alignment="center", spacing=12),

            ft.TextButton(
                "Voltar ao Menu Principal", 
                icon=ft.icons.ARROW_BACK,
                on_click=voltar,
                style=ft.ButtonStyle(color=st.GREY)
            )
        ], horizontal_alignment="center", spacing=20, scroll="auto")
    )