import flet as ft

def criar_grafico_evolucao(dados_historicos, titulo="Consumo"):
    """
    dados_historicos: Lista de dicionários [{'mes': 'Jan', 'valor': 10.5}, ...]
    """
    pontos = []
    
    # Se não houver dados, retorna um aviso visual para evitar crash no Dashboard
    if not dados_historicos:
        return ft.Container(
            content=ft.Text("Sem histórico disponível", color="grey"),
            alignment="center" # Corrigido para PascalCase
        )

    for i, dado in enumerate(dados_historicos):
        # O campo 'valor' deve bater com o nome da coluna no seu banco (ex: 'consumo')
        valor = dado.get('consumo') or dado.get('valor') or 0
        pontos.append(ft.LineChartDataPoint(i, valor))[cite: 4]

    return ft.LineChart(
        data_series=[
            ft.LineChartData(
                # CORREÇÃO: data_points é o padrão para versões atuais do Flet[cite: 4]
                data_points=pontos,
                color="blue", # Corrigido: Usando string para evitar erro de definição
                stroke_width=4,
                curved=True,
                # Abaixo da linha usamos uma cor suave[cite: 4]
                below_line_bgcolor="blue100", 
                point=True 
            )
        ],
        border=ft.border.all(1, "grey200"), # Corrigido: String para evitar NameError
        horizontal_grid_lines=ft.ChartGridLines(
            interval=1, 
            color="grey100"
        ),
        # Configurações de interatividade para o toque do usuário[cite: 4]
        interactive=True,
        expand=True
    )