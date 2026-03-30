import flet as ft
from views import styles as st

def montar_tela_dashboard(page, voltar):
    # --- DADOS SIMULADOS (Substituir por Database.buscar_resumo()) ---
    consumo_total = "450 m³"
    media_apto = "4.6 m³"
    
    # Gráfico Simples de Barras (Consumo por Bloco ou Mês)
    chart = ft.BarChart(
        bar_groups=[
            ft.BarChartGroup(x=0, bar_rods=[ft.BarChartRod(from_y=0, to_y=15, color=st.PRIMARY_BLUE)]),
            ft.BarChartGroup(x=1, bar_rods=[ft.BarChartRod(from_y=0, to_y=12, color=st.PRIMARY_BLUE)]),
            ft.BarChartGroup(x=2, bar_rods=[ft.BarChartRod(from_y=0, to_y=18, color=st.PRIMARY_BLUE)]),
            ft.BarChartGroup(x=3, bar_rods=[ft.BarChartRod(from_y=0, to_y=10, color=st.PRIMARY_BLUE)]),
        ],
        border=ft.border.all(1, ft.colors.with_opacity(0.2, st.GREY)),
        left_axis=ft.ChartAxis(labels=[ft.ChartAxisLabel(value=0, label=ft.Text("0")), ft.ChartAxisLabel(value=20, label=ft.Text("20"))]),
        expand=True,
    )

    return ft.Column([
        # Cabeçalho
        ft.Row([
            ft.IconButton(ft.icons.ARROW_BACK, on_click=voltar),
            ft.Text("Dashboard de Consumo", size=24, weight="bold"),
        ]),
        
        # Cards de Resumo (KPIs)
        ft.Row([
            ft.Container(
                content=ft.Column([ft.Text("Consumo Total"), ft.Text(consumo_total, size=20, weight="bold", color=st.PRIMARY_BLUE)]),
                bgcolor=ft.colors.SURFACE_VARIANT, padding=15, border_radius=10, expand=True
            ),
            ft.Container(
                content=ft.Column([ft.Text("Média/Apto"), ft.Text(media_apto, size=20, weight="bold", color=ft.colors.GREEN)]),
                bgcolor=ft.colors.SURFACE_VARIANT, padding=15, border_radius=10, expand=True
            ),
        ], spacing=15),
        
        # Área do Gráfico
        ft.Text("Histórico de Consumo Mensal", size=18, weight="w500"),
        ft.Container(
            content=chart,
            height=200,
            padding=20,
            bgcolor=ft.colors.BLACK26,
            border_radius=10
        ),
        
        # Lista de Alertas/Destaques
        ft.ListTile(
            leading=ft.Icon(ft.icons.WARNING, color=ft.colors.AMBER),
            title=ft.Text("Apto 42B - Consumo 30% acima da média"),
            subtitle=ft.Text("Verificar possível vazamento ou erro de leitura."),
        ),
        
    ], scroll="auto", spacing=20)