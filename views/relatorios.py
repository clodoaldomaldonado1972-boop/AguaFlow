import flet as ft
from database.database import Database


def montar_tela_relatorios(page, voltar, sync_nuvem=None, gerar_e_enviar_pdf=None, gerar_qr=None):
    # --- Lógica de Dados (Igual à anterior) ---
    try:
        dados = Database.buscar_relatorio_geral()
        lidas = len(dados) if dados else 0
    except:
        lidas = 0

    total = 96
    progresso = lidas / total if total > 0 else 0

    # --- RETORNO DA VIEW COM OPÇÃO DE VOLTAR ---
    return ft.View(
        route="/relatorios",
        bgcolor="#121417",
        controls=[
            # 1. BARRA SUPERIOR COM BOTÃO VOLTAR
            ft.AppBar(
                title=ft.Text("Relatórios e Gestão", weight="bold"),
                bgcolor="#1e1e1e",
                color="white",
                # O parâmetro 'leading' coloca o ícone de voltar à esquerda
                leading=ft.IconButton(
                    "arrow_back", icon_color="white", on_click=voltar),
            ),

            ft.Column([
                # Dashboard de Progresso (Visual)
                ft.Container(
                    content=ft.Column([
                        ft.Text("Progresso Vivere Prudente",
                                size=18, color="white"),
                        ft.ProgressBar(value=progresso, width=350,
                                       color="blue", bgcolor="#333333"),
                        ft.Row([
                            ft.Text(f"Lidas: {lidas}",
                                    color="blue", weight="bold"),
                            ft.Text(f"Pendentes: {total - lidas}",
                                    color="orange", weight="bold"),
                        ], alignment="spaceBetween", width=350),
                    ], horizontal_alignment="center"),
                    padding=20, bgcolor="#1e1e1e", border_radius=10, margin=10
                ),

                # Botões de Ação
                ft.Container(
                    padding=20,
                    content=ft.Column([
                        ft.ElevatedButton(
                            "GERAR PDF E ENVIAR",
                            icon="send",
                            on_click=gerar_e_enviar_pdf,
                            width=350, height=50, bgcolor="blue", color="white"
                        ),
                        ft.ElevatedButton(
                            "SINCRONIZAR NUVEM",
                            icon="cloud_sync",
                            on_click=sync_nuvem,
                            width=350, height=50, bgcolor="green", color="white"
                        ),
                        ft.OutlinedButton(
                            "REIMPRIMIR QR CODES",
                            icon="qr_code",
                            on_click=gerar_qr,
                            width=350, height=50, style=ft.ButtonStyle(color="grey")
                        ),

                        # 2. BOTÃO EXTRA DE VOLTAR NO FINAL DA LISTA
                        ft.TextButton(
                            "Voltar ao Menu Principal",
                            icon="arrow_back",
                            on_click=voltar,
                            style=ft.ButtonStyle(color="grey")
                        ),
                    ], spacing=15, horizontal_alignment="center")
                )
            ], scroll="auto", expand=True)
        ]
    )
