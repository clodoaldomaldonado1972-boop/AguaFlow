import flet as ft
from datetime import datetime
from database.database import Database


def montar_tela_dashboard(page, voltar):
    # --- BUSCA DE DADOS ---
    try:
        leituras = Database.buscar_todas_leituras()
    except:
        leituras = []

    # Inicializa consumo por mês (Janeiro a Abril)
    consumo_por_mes = {
        "Janeiro": 0.0,
        "Fevereiro": 0.0,
        "Março": 0.0,
        "Abril": 0.0,
    }

    # Processa as leituras do banco de dados
    for leitura in leituras:
        try:
            # Extrai o mês da data da leitura
            data = datetime.strptime(leitura["data_leitura"][:10], "%Y-%m-%d")
            meses_nomes = {1: "Janeiro",
                           2: "Fevereiro", 3: "Março", 4: "Abril"}
            if data.month in meses_nomes:
                consumo_por_mes[meses_nomes[data.month]
                                ] += float(leitura["valor"])
        except Exception:
            continue

    meses = ["Janeiro", "Fevereiro", "Março", "Abril"]
    valores = [consumo_por_mes[mes] for mes in meses]
    max_consumo = max(valores) if valores and max(valores) > 0 else 10

    # --- GRÁFICO DE CONSUMO ---[cite: 4]
    chart = ft.BarChart(
        bar_groups=[
            ft.BarChartGroup(
                x=index,
                bar_rods=[ft.BarChartRod(
                    from_y=0, to_y=value, color=ft.Colors.BLUE_400, width=20, border_radius=5)]
            ) for index, value in enumerate(valores)
        ],
        left_axis=ft.ChartAxis(
            labels=[
                ft.ChartAxisLabel(value=0, label=ft.Text("0")),
                ft.ChartAxisLabel(value=max_consumo,
                                  label=ft.Text(f"{int(max_consumo)}"))
            ]
        ),
        bottom_axis=ft.ChartAxis(
            labels=[
                ft.ChartAxisLabel(value=i, label=ft.Text(mes[:3], size=12))
                for i, mes in enumerate(meses)
            ]
        ),
        border=ft.border.all(1, ft.Colors.with_opacity(0.1, "white")),
        expand=True,
    )

    # --- LÓGICA DE HISTÓRICO POR UNIDADE ---[cite: 4]
    historico_lista = ft.ListView(expand=True, spacing=5, padding=10)

    def atualizar_historico(e=None):
        selecionado = unidade_dropdown.value
        historico_lista.controls.clear()

        if selecionado:
            # Filtra registros pela unidade selecionada[cite: 4]
            registros = [l for l in leituras if str(
                l["unidade"]) == str(selecionado)]
            registros.sort(key=lambda item: item["data_leitura"], reverse=True)

            for registro in registros:
                historico_lista.controls.append(
                    ft.ListTile(
                        title=ft.Text(
                            f"Data: {registro['data_leitura'][:10]}", weight="bold"),
                        subtitle=ft.Text(
                            f"{registro['valor']} m³ • {registro['tipo_leitura']}"),
                        leading=ft.Icon(ft.Icons.WATER_DROP, color="blue")
                    )
                )

        if not historico_lista.controls:
            historico_lista.controls.append(
                ft.Text("Nenhum histórico encontrado.",
                        color="grey", italic=True)
            )
        page.update()

    # Busca unidades para o Dropdown[cite: 4]
    unidades_opcoes = []
    try:
        with Database.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM unidades ORDER BY id")
            unidades_opcoes = [ft.dropdown.Option(
                str(row[0])) for row in cursor.fetchall()]
    except:
        unidades_opcoes = []

    unidade_dropdown = ft.Dropdown(
        label="Filtrar por Apartamento",
        width=350,
        options=unidades_opcoes,
        on_change=atualizar_historico,
    )

    # Inicializa a lista[cite: 4]
    atualizar_historico()

    return ft.View(
        route="/dashboard",
        bgcolor="#121417",
        controls=[
            ft.AppBar(
                title=ft.Text("Dashboard de Consumo", weight="bold"),
                bgcolor="#1e1e1e",
                # Botão Voltar[cite: 4]
                leading=ft.IconButton(
                    icon=ft.Icons.ARROW_BACK, on_click=voltar)
            ),
            ft.Container(
                padding=15,
                expand=True,
                content=ft.Column([
                    # Cartões de Resumo[cite: 4]
                    ft.Row([
                        ft.Container(
                            content=ft.Column([
                                ft.Text("Consumo Total", size=12),
                                ft.Text(f"{sum(valores):.1f} m³",
                                        size=18, weight="bold", color="blue")
                            ]),
                            bgcolor="#1e1e1e", padding=15, border_radius=10, expand=True
                        ),
                        ft.Container(
                            content=ft.Column([
                                ft.Text("Média Mensal", size=12),
                                ft.Text(f"{(sum(valores)/len(meses)):.1f} m³",
                                        size=18, weight="bold", color="green")
                            ]),
                            bgcolor="#1e1e1e", padding=15, border_radius=10, expand=True
                        ),
                    ], spacing=10),

                    # Gráfico[cite: 4]
                    ft.Text("Consumo por Mês", size=16, weight="bold"),
                    ft.Container(
                        content=chart,
                        height=200,
                        padding=15,
                        bgcolor=ft.Colors.BLACK26,
                        border_radius=10,
                    ),

                    # Filtro e Histórico[cite: 4]
                    ft.Divider(height=10, color="transparent"),
                    unidade_dropdown,
                    ft.Text("Histórico Detalhado", size=16, weight="bold"),
                    ft.Container(
                        content=historico_lista,
                        expand=True,
                        bgcolor="#1e1e1e",
                        border_radius=10
                    ),
                ], spacing=10, scroll=ft.ScrollMode.ADAPTIVE)
            )
        ]
    )
