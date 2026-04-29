import flet as ft

def criar_grafico_evolucao(historico, titulo_unidade):
    """Transforma os dados do banco em um gráfico de linhas do Flet."""
    pontos = []
    
    # Se não houver dados, retorna uma mensagem simples
    if not historico:
        return ft.Text("Sem histórico para esta unidade", color="grey")

    for i, dado in enumerate(historico):
        # CORREÇÃO: Usamos 'leitura_atual' que é o nome real da coluna no SQLite
        pontos.append(ft.LineChartDataPoint(i, dado['leitura_atual']))

    return ft.LineChart(
        data_series=[
            ft.LineChartData(
                data_points=pontos,
                stroke_width=4,
                color=ft.colors.BLUE,
                curved=True,
                below_line_bgcolor=ft.colors.with_opacity(0.1, ft.colors.BLUE),
                below_line_gradient=ft.LinearGradient(
                    begin=ft.alignment.top_center,
                    end=ft.alignment.bottom_center,
                    colors=[ft.colors.with_opacity(0.3, ft.colors.BLUE), ft.colors.TRANSPARENT],
                ),
            )
        ],
        border=ft.border.all(1, ft.colors.with_opacity(0.1, ft.colors.WHITE)),
        horizontal_grid_lines=ft.ChartGridLines(interval=1, color=ft.colors.with_opacity(0.1, ft.colors.WHITE)),
        expand=True
    )