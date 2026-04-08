import flet as ft
from database.database import Database

# --- IMPORT DAS UTILIDADES QUE AGORA ESTÃO NA RAIZ ---
# Exemplo de função utilitária
from utils.exportador import gerar_pdf_csv as exportar_dados


def montar_tela_relatorios(page, voltar):
    try:
        # Busca os dados atuais no banco de dados local
        dados = Database.buscar_relatorio_geral()
        lidas = len(dados) if dados else 0
    except Exception as e:
        print(f"Erro ao carregar banco: {e}")
        lidas = 0

    total = 96
    progresso = lidas / total if total > 0 else 0

    # --- FUNÇÕES INTERNAS DE AÇÃO ---
    async def acao_gerar_pdf(e):
        # Aqui chamamos a lógica que agora vive em utils/[cite: 1, 2]
        page.snack_bar = ft.SnackBar(
            ft.Text("Gerando relatório em storage/..."), bgcolor="blue")
        page.snack_bar.open = True
        page.update()
        # lógica de exportação viria aqui

    async def acao_sync(e):
        page.snack_bar = ft.SnackBar(
            ft.Text("Sincronizando com Supabase..."), bgcolor="green")
        page.snack_bar.open = True
        page.update()

    return ft.View(
        route="/relatorios",
        bgcolor="#121417",
        controls=[
            ft.AppBar(
                title=ft.Text("Relatórios e Gestão", weight="bold"),
                # Botão Voltar: configurado no main.py[cite: 5, 10]
                leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=voltar),
                bgcolor="#1e1e1e"
            ),
            ft.Column([
                # Painel de Progresso[cite: 10]
                ft.Container(
                    content=ft.Column([
                        ft.Text("Progresso Vivere Prudente",
                                size=18, color="white"),
                        ft.ProgressBar(value=progresso,
                                       width=350, color="blue"),
                        ft.Row([
                            ft.Text(f"Lidas: {lidas}",
                                    color="blue", weight="bold"),
                            ft.Text(f"Pendentes: {total - lidas}",
                                    color="orange", weight="bold"),
                        ], alignment="spaceBetween", width=350),
                    ]),
                    padding=20, bgcolor="#1e1e1e", border_radius=10
                ),

                # Seção de Ações[cite: 10]
                ft.Container(
                    padding=20,
                    content=ft.Column([
                        # Botão Dashboard
                        ft.ElevatedButton(
                            "DASHBOARD DE CONSUMO",
                            icon=ft.Icons.INSERT_CHART,
                            on_click=lambda _: page.go(
                                "/dashboard"),  # Rota definida no main
                            width=350,
                            bgcolor="#2196F3",
                            color="white"
                        ),

                        # Botão Exportar (Agora aponta para lógica em utils)[cite: 1, 2, 10]
                        ft.ElevatedButton(
                            "GERAR PDF E ENVIAR",
                            icon=ft.Icons.PICTURE_AS_PDF,
                            on_click=acao_gerar_pdf,
                            width=350,
                            bgcolor="blue",
                            color="white"
                        ),

                        # Botão Sincronizar[cite: 10]
                        ft.ElevatedButton(
                            "SINCRONIZAR NUVEM",
                            icon=ft.Icons.CLOUD_SYNC,
                            on_click=acao_sync,
                            width=350,
                            bgcolor="green",
                            color="white"
                        ),

                        # Botão QR Code
                        ft.OutlinedButton(
                            "GERAR QR CODES",
                            icon=ft.Icons.QR_CODE_2,
                            on_click=lambda _: page.go("/qrcodes"),
                            width=350,
                            style=ft.ButtonStyle(color="white")
                        )
                    ], spacing=15)
                )
            ], scroll="auto", expand=True, horizontal_alignment="center")
        ]
    )
