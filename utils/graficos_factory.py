import flet as ft

def criar_grafico_evolucao(dados_historicos, titulo="Consumo"):
    """
    dados_historicos: Lista de dicionários [{'mes': 'Jan', 'valor': 10.5}, ...]
    """
    pontos = []
    for i, dado in enumerate(dados_historicos):
        # Criação dos pontos para o gráfico de linhas
        pontos.append(ft.LineChartDataPoint(i, dado['valor']))

    return ft.LineChart(
        data_series=[
            ft.LineChartData(
                # CORREÇÃO: No Flet atual, usa-se 'data_points' em vez de 'points'
                data_points=pontos,
                color=ft.colors.BLUE,
                stroke_width=4,
                curved=True,
                below_line_bgcolor=ft.colors.with_opacity(0.1, ft.colors.BLUE),
                # Garante que os pontos individuais fiquem visíveis no gráfico
                point=True 
            )
        ],
        border=ft.border.all(1, ft.colors.with_opacity(0.2, ft.colors.GREY)),
        horizontal_grid_lines=ft.ChartGridLines(
            interval=1, 
            color=ft.colors.with_opacity(0.1, ft.colors.GREY)
        ),
        # Configurações de interatividade para quando o utilizador toca no gráfico
        interactive=True,
        expand=True
    )