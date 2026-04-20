import flet as ft
import asyncio
import datetime
from utils.diagnostico import DiagnosticoSistema

def montar_tela_saude(page: ft.Page, voltar):
    # Componentes de status visual
    icon_db = ft.Icon(ft.icons.STORAGE_ROUNDED, color="grey", size=30)
    lbl_db_status = ft.Text("Aguardando...", color="grey", size=16, weight="bold")
    lst_logs = ft.ListView(expand=1, spacing=5, padding=10)

    def adicionar_log(mensagem, cor="white54"):
        hora = datetime.datetime.now().strftime("%H:%M:%S")
        lst_logs.controls.insert(0, ft.Text(f"[{hora}] {mensagem}", color=cor, size=12))
        page.update()

    async def executar_diagnostico(e=None):
        adicionar_log("Iniciando varredura de integridade...", "blue")
        icon_db.color = "orange"
        page.update()
        
        # Chama o motor de diagnóstico que analisamos anteriormente
        sucesso, resumo = await DiagnosticoSistema.executar_checkup_completo()
        
        await asyncio.sleep(1) # Simulação para feedback visual
        
        if sucesso:
            icon_db.color = "green"
            lbl_db_status.value = "Sistema Saudável"
            lbl_db_status.color = "green"
            adicionar_log("Checkup concluído: Sem erros detectados.", "green")
        else:
            icon_db.color = "red"
            lbl_db_status.value = "Falha Detectada"
            lbl_db_status.color = "red"
            adicionar_log(f"Alerta: {resumo}", "red")
        
        page.update()

    # Inicia o diagnóstico automaticamente ao abrir a tela
    page.run_task(executar_diagnostico)

    return ft.View(
        route="/dashboard_saude",
        bgcolor="#121417",
        controls=[
            ft.Container(
                padding=20,
                content=ft.Column([
                    ft.Text("Saúde do AguaFlow", size=24, weight="bold", color="white"),
                    
                    # Card de Status do Banco
                    ft.Container(
                        padding=20,
                        bgcolor="#1e1e1e",
                        border_radius=10,
                        content=ft.Row([
                            icon_db,
                            ft.Column([
                                lbl_db_status,
                                ft.Text("Integridade do SQLite e Sincronismo", size=12, color="grey")
                            ])
                        ])
                    ),

                    ft.Text("Logs de Eventos", size=16, weight="bold"),
                    ft.Container(
                        content=lst_logs,
                        bgcolor=ft.colors.BLACK45,
                        border_radius=10, 
                        height=250,
                        border=ft.border.all(1, "white10")
                    ),

                    ft.ElevatedButton(
                        "REESCANEAR AGORA",
                        icon=ft.icons.REFRESH_ROUNDED,
                        on_click=executar_diagnostico,
                        width=400, height=50
                    ),
                    
                    ft.ElevatedButton(
                        "MÉTRICAS EM NUVEM (GRAFANA)",
                        icon=ft.icons.INSERT_CHART_OUTLINED_ROUNDED,
                        on_click=lambda _: page.launch_url("https://grafana.com"),
                        width=400, height=50,
                        style=ft.ButtonStyle(bgcolor=ft.colors.ORANGE_900, color="white")
                    ),

                    ft.TextButton("Voltar ao Menu", on_click=voltar)
                ], spacing=15)
            )
        ]
    )