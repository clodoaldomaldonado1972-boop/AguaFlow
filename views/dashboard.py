import flet as ft
from datetime import datetime
from database.database import Database
from views import styles as st


def montar_tela_dashboard(page, voltar):
    # Dados de consumo por mês (Janeiro a Abril)
    leituras = Database.buscar_todas_leituras()
    consumo_por_mes = {
        "Janeiro": 0.0,
        "Fevereiro": 0.0,
        "Março": 0.0,
        "Abril": 0.0,
    }

    for leitura in leituras:
        try:
            data = datetime.strptime(leitura["data_leitura"][:10], "%Y-%m-%d")
            if data.month == 1:
                consumo_por_mes["Janeiro"] += float(leitura["valor"])
            elif data.month == 2:
                consumo_por_mes["Fevereiro"] += float(leitura["valor"])
            elif data.month == 3:
                consumo_por_mes["Março"] += float(leitura["valor"])
            elif data.month == 4:
                consumo_por_mes["Abril"] += float(leitura["valor"])
        except Exception:
            continue

    meses = ["Janeiro", "Fevereiro", "Março", "Abril"]
    valores = [consumo_por_mes[mes] for mes in meses]

    chart = ft.BarChart(
        bar_groups=[
            ft.BarChartGroup(
                x=index,
                bar_rods=[ft.BarChartRod(
                    from_y=0, to_y=value, color=st.PRIMARY_BLUE)]
            ) for index, value in enumerate(valores)
        ],
        left_axis=ft.ChartAxis(
            labels=[
                ft.ChartAxisLabel(value=0, label=ft.Text("0")),
                ft.ChartAxisLabel(value=max(valores) or 10,
                                  label=ft.Text(str(int(max(valores) or 10))))
            ]
        ),
        bottom_axis=ft.ChartAxis(
            labels=[
                ft.ChartAxisLabel(value=i, label=ft.Text(mes[:3]))
                for i, mes in enumerate(meses)
            ]
        ),
        border=ft.border.all(1, ft.Colors.with_opacity(0.2, st.GREY)),
        expand=True,
    )

    # Dropdown de apartamentos
    unidades = []
    with Database.get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM unidades ORDER BY id")
        unidades = [row[0] for row in cursor.fetchall()]

    unidade_selecionada = unidades[0] if unidades else None
    historico_lista = ft.ListView(expand=True, spacing=5, padding=10)

    def atualizar_historico(e=None):
        selecionado = unidade_dropdown.value
        historico_lista.controls.clear()
        if selecionado:
            registros = [l for l in leituras if l["unidade"] == selecionado]
            registros.sort(key=lambda item: item["data_leitura"], reverse=True)
            for registro in registros:
                historico_lista.controls.append(
                    ft.ListTile(
                        title=ft.Text(f"{registro['data_leitura'][:10]}"),
                        subtitle=ft.Text(
                            f"{registro['valor']} m³ - {registro['tipo_leitura']}"),
                        leading=ft.Icon(ft.icons.WATER_DROP,
                                        color=st.PRIMARY_BLUE)
                    )
                )
        if not historico_lista.controls:
            historico_lista.controls.append(
                ft.Text(
                    "Nenhum histórico encontrado para este apartamento.", color="grey")
            )
        page.update()

    unidade_dropdown = ft.Dropdown(
        label="Apartamento",
        width=320,
        value=unidade_selecionada,
        options=[ft.dropdown.Option(u) for u in unidades],
        on_change=atualizar_historico,
    )

    atualizar_historico()

    return ft.View(
        route="/dashboard",
        bgcolor="#121417",
        controls=[
            ft.AppBar(
                title=ft.Text("Dashboard de Consumo", weight="bold"),
                bgcolor="#1e1e1e",
                leading=ft.IconButton(icon="arrow_back", on_click=voltar)
            ),
            ft.Container(
                padding=20,
                expand=True,
                content=ft.Column([
                    ft.Row([
                        ft.Container(
                            content=ft.Column([
                                ft.Text("Consumo Total"),
                                ft.Text(f"{sum(valores):.1f} m³", size=20,
                                        weight="bold", color=st.PRIMARY_BLUE)
                            ]),
                            bgcolor=ft.Colors.SURFACE_VARIANT,
                            padding=15,
                            border_radius=10,
                            expand=True
                        ),
                        ft.Container(
                            content=ft.Column([
                                ft.Text("Média Mensal"),
                                ft.Text(f"{(sum(valores)/len(meses)):.1f} m³",
                                        size=20, weight="bold", color=ft.Colors.GREEN)
                            ]),
                            bgcolor=ft.Colors.SURFACE_VARIANT,
                            padding=15,
                            border_radius=10,
                            expand=True
                        ),
                    ], spacing=15),
                    ft.Text("Consumo por Mês", size=18, weight="w500"),
                    ft.Container(
                        content=chart,
                        height=260,
                        padding=20,
                        bgcolor=ft.Colors.BLACK26,
                        border_radius=10,
                    ),
                    ft.Row([
                        unidade_dropdown,
                    ], alignment=ft.MainAxisAlignment.START),
                    ft.Text("Histórico do Apartamento",
                            size=16, weight="w500"),
                    historico_lista,
                ], spacing=20),
            )
        ]
    )
