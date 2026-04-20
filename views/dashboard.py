import flet as ft
from datetime import datetime
from database.database import Database
# Mantém a integração com seu motor de alertas para notificar anomalias
try:
    from utils.alertas_engine import enviar_alerta_MESSAGE
except ImportError:
    enviar_alerta_MESSAGE = lambda x: print(f"Alerta: {x}")

def montar_tela_dashboard(page: ft.Page, voltar):
    # --- 1. BUSCA DE DADOS ---
    try:
        # Busca leituras sincronizadas e locais para compor o gráfico
        leituras = Database.buscar_historico_cloud()
    except Exception:
        leituras = []

    # --- 2. GERAÇÃO DA GRADE DE UNIDADES (96 APARTAMENTOS) ---
    # IHC: Representação visual clara do progresso da leitura no condomínio
    unidades_lidas = 0
    lista_unidades_controles = []
    
    # Simulação de leitura para preencher a grade (ou busca real do banco)
    for andar in range(16, 0, -1):
        for apto in range(1, 7):
            id_unidade = f"{andar}{apto}"
            ja_lida = any(str(l.get("unidade_id")).startswith(id_unidade) for l in leituras)
            
            if ja_lida: unidades_lidas += 1
            
            lista_unidades_controles.append(
                ft.Container(
                    content=ft.Text(id_unidade, size=10, weight="bold"),
                    alignment=ft.alignment.center,
                    width=40, height=40,
                    bgcolor=ft.colors.GREEN_800 if ja_lida else ft.colors.RED_900,
                    border_radius=5,
                    tooltip=f"Unidade {id_unidade}: {'Concluída' if ja_lida else 'Pendente'}"
                )
            )

    unidades_pendentes = 96 - unidades_lidas

    # --- 3. GRÁFICO DE CONSUMO (Flet Chart) ---
    chart_data = []
    if leituras:
        # Agrupa os últimos 5 registros para o gráfico de barras
        for i, leitura in enumerate(leituras[:5]):
            chart_data.append(
                ft.BarChartGroup(
                    x=i,
                    bar_rods=[
                        ft.BarChartRod(
                            from_y=0,
                            to_y=float(leitura.get("consumo_mes", 0)),
                            width=20,
                            color=ft.colors.BLUE_400,
                            border_radius=5,
                        )
                    ],
                )
            )

    chart = ft.BarChart(
        bar_groups=chart_data,
        border=ft.border.all(1, "white10"),
        left_axis=ft.ChartAxis(labels_size=40, title=ft.Text("m³"), title_size=40),
        bottom_axis=ft.ChartAxis(labels=[ft.ChartAxisLabel(value=i, label=ft.Text(f"L{i+1}")) for i in range(len(chart_data))]),
        expand=True,
    )

    # --- 4. CONSTRUÇÃO DA INTERFACE ---
    return ft.View(
        route="/dashboard",
        bgcolor="#121417",
        controls=[
            ft.ListView(
                padding=20,
                spacing=15,
                controls=[
                    ft.Text("Consumo Vivere Prudente", size=24, weight="bold", color=ft.colors.BLUE_400),
                    
                    # Painel de Resumo
                    ft.Row([
                        ft.Container(
                            content=ft.Column([
                                ft.Text("Lidas", size=12, color="green"),
                                ft.Text(f"{unidades_lidas}/96", size=20, weight="bold")
                            ]),
                            bgcolor="#1e1e1e", padding=15, border_radius=10, expand=True
                        ),
                        ft.Container(
                            content=ft.Column([
                                ft.Text("Pendentes", size=12, color="amber"),
                                ft.Text(f"{unidades_pendentes}", size=20, weight="bold")
                            ]),
                            bgcolor="#1e1e1e", padding=15, border_radius=10, expand=True
                        ),
                    ], spacing=10),

                    ft.Text("Histórico de Consumo (m³)", size=16, weight="bold"),
                    ft.Container(content=chart, height=200, padding=15, bgcolor=ft.colors.BLACK26, border_radius=10),
                    
                    ft.Text("Mapa do Condomínio", size=16, weight="bold"),
                    ft.Container(
                        content=ft.GridView(
                            controls=lista_unidades_controles,
                            runs_count=6,
                            max_extent=60,
                            spacing=5,
                            run_spacing=5,
                        ),
                        height=300,
                        bgcolor="#1e1e1e",
                        padding=10,
                        border_radius=10
                    ),
                    
                    ft.ElevatedButton("VOLTAR AO MENU", on_click=voltar, width=400)
                ]
            )
        ]
    )