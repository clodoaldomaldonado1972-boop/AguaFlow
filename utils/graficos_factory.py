import flet as ft


def criar_grafico_evolucao(dados_historicos, titulo="Consumo"):
    """
    dados_historicos: Lista de dicts com chaves 'data_hora_coleta', 'leitura_agua', 'leitura_gas'
    Constrói um gráfico de barras duplas (água=azul, gás=laranja) usando controles padrão do Flet.
    """
    if not dados_historicos:
        return ft.Container(
            content=ft.Text("Sem histórico disponível", color="grey", size=12),
            alignment=ft.Alignment(0, 0),
            height=160,
        )

    valores_agua = []
    valores_gas = []
    labels = []
    for dado in dados_historicos:
        agua = float(dado.get('leitura_agua') or 0)
        gas = float(dado.get('leitura_gas') or 0)
        valores_agua.append(agua)
        valores_gas.append(gas)
        data = dado.get('data_hora_coleta') or dado.get('mes', '?')
        if isinstance(data, str) and len(data) >= 7:
            labels.append(data[5:7] + "/" + data[2:4])
        else:
            labels.append(str(data)[:5])

    tem_agua = any(v > 0 for v in valores_agua)
    tem_gas = any(v > 0 for v in valores_gas)

    todos_valores = [v for v in valores_agua + valores_gas if v > 0]
    max_val = max(todos_valores) if todos_valores else 1
    max_bar_height = 110

    bars = []
    for i, label in enumerate(labels):
        agua = valores_agua[i]
        gas = valores_gas[i]

        barras_periodo = []

        if tem_agua:
            h = max(4, int((agua / max_val) * max_bar_height)) if agua > 0 else 4
            barras_periodo.append(
                ft.Column(
                    [
                        ft.Text(f"{agua:.1f}", size=7, color="#90CAF9"),
                        ft.Container(
                            width=14,
                            height=h,
                            bgcolor="#2196F3",
                            border_radius=ft.BorderRadius.only(top_left=3, top_right=3),
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=1,
                )
            )

        if tem_gas:
            h = max(4, int((gas / max_val) * max_bar_height)) if gas > 0 else 4
            barras_periodo.append(
                ft.Column(
                    [
                        ft.Text(f"{gas:.1f}", size=7, color="#FFCC80"),
                        ft.Container(
                            width=14,
                            height=h,
                            bgcolor="#FF9800",
                            border_radius=ft.BorderRadius.only(top_left=3, top_right=3),
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=1,
                )
            )

        bars.append(
            ft.Column(
                [
                    ft.Row(
                        barras_periodo,
                        vertical_alignment=ft.CrossAxisAlignment.END,
                        spacing=2,
                    ),
                    ft.Text(label, size=8, color="grey"),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=2,
            )
        )

    legenda = []
    if tem_agua:
        legenda.append(ft.Row([
            ft.Container(width=10, height=10, bgcolor="#2196F3", border_radius=2),
            ft.Text("Água", size=9, color="#90CAF9"),
        ], spacing=4))
    if tem_gas:
        legenda.append(ft.Row([
            ft.Container(width=10, height=10, bgcolor="#FF9800", border_radius=2),
            ft.Text("Gás", size=9, color="#FFCC80"),
        ], spacing=4))

    return ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    bars,
                    alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                    vertical_alignment=ft.CrossAxisAlignment.END,
                ),
                ft.Divider(height=1, color="white10"),
                ft.Row(
                    legenda + [ft.Text("m³ por coleta", size=9, color="grey", italic=True)],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=12,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=4,
        ),
        padding=ft.Padding.symmetric(horizontal=10, vertical=8),
        bgcolor="#1a1a2e",
        border_radius=10,
    )
