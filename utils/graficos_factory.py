import flet as ft


def criar_grafico_evolucao(dados_historicos, titulo="Consumo"):
    """
    dados_historicos: Lista de dicts com chaves 'data_hora_coleta', 'leitura_agua', 'leitura_gas'
    Constrói um gráfico de barras usando controles padrão do Flet (sem LineChart).
    """
    if not dados_historicos:
        return ft.Container(
            content=ft.Text("Sem histórico disponível", color="grey", size=12),
            alignment=ft.Alignment(0, 0),
            height=160,
        )

    valores = []
    labels = []
    for dado in dados_historicos:
        val = dado.get('leitura_agua') or dado.get('consumo') or dado.get('valor') or 0
        valores.append(float(val) if val else 0)
        data = dado.get('data_hora_coleta') or dado.get('mes', '?')
        if isinstance(data, str) and len(data) >= 7:
            labels.append(data[5:7] + "/" + data[2:4])
        else:
            labels.append(str(data)[:5])

    max_val = max(valores) if valores and max(valores) > 0 else 1
    max_bar_height = 120

    bars = []
    for val, label in zip(valores, labels):
        bar_height = max(4, int((val / max_val) * max_bar_height))
        bars.append(
            ft.Column(
                [
                    ft.Text(f"{val:.1f}", size=8, color="white70"),
                    ft.Container(
                        width=28,
                        height=bar_height,
                        bgcolor="#2196F3",
                        border_radius=ft.BorderRadius.only(top_left=4, top_right=4),
                    ),
                    ft.Text(label, size=8, color="grey"),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=2,
            )
        )

    return ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    bars,
                    alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                    vertical_alignment=ft.CrossAxisAlignment.END,
                ),
                ft.Divider(height=1, color="white10"),
                ft.Text("m³ por coleta", size=9, color="grey", italic=True),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=4,
        ),
        padding=ft.Padding.symmetric(horizontal=10, vertical=8),
        bgcolor="#1a1a2e",
        border_radius=10,
    )
