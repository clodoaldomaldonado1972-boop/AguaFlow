import flet as ft
from datetime import datetime
from database.database import Database
from utils.alertas_engine import enviar_alerta_whatsapp

def montar_tela_dashboard(page: ft.Page, voltar):
    # --- BUSCA E PROCESSAMENTO DE DADOS ---
    try:
        leituras = Database.buscar_todas_leituras()
    except Exception:
        leituras = []

    # Cria dicionário de leituras por unidade para consulta rápida
    leituras_dict = {}
    for leitura in leituras:
        unidade = leitura.get("unidade", "N/A")
        leituras_dict[unidade] = leitura

    # Gera todas as 96 unidades (16 andares x 6 apartamentos)
    todas_unidades = []
    for andar in range(16, 0, -1):
        for apto in range(1, 7):
            todas_unidades.append(f"Apto {andar}{apto}")

    # Inicializa meses para o gráfico
    meses_nomes = {1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr"}
    consumo_por_mes = {nome: 0.0 for nome in meses_nomes.values()}

    for leitura in leituras:
        try:
            data = datetime.strptime(leitura["data_leitura"][:10], "%Y-%m-%d")
            if data.month in meses_nomes:
                consumo_por_mes[meses_nomes[data.month]] += float(leitura["valor"])
        except:
            continue

    meses_lista = list(consumo_por_mes.keys())
    valores_lista = list(consumo_por_mes.values())
    total_consumo = sum(valores_lista)
    media_consumo = total_consumo / len(valores_lista) if valores_lista else 0
    unidades_lidas = len(leituras_dict)
    unidades_pendentes = len(todas_unidades) - unidades_lidas

    # --- COMPONENTE DE GRÁFICO (BarChart) ---
    chart = ft.BarChart(
        bar_groups=[
            ft.BarChartGroup(x=i, bar_rods=[ft.BarChartRod(from_y=0, to_y=val, color="blue", width=30)])
            for i, val in enumerate(valores_lista)
        ],
        bottom_axis=ft.ChartAxis(
            labels=[ft.ChartAxisLabel(value=i, label=ft.Text(mes)) for i, mes in enumerate(meses_lista)]
        ),
        border=ft.border.all(1, "transparent"),
        left_axis=ft.ChartAxis(labels_size=40),
        horizontal_grid_lines=ft.ChartGridLines(color="white10"),
    )

    # --- LISTA DE TODAS UNIDADES (PRONTAS PARA RECEBER LEITURA) ---
    lista_unidades = ft.ListView(expand=True, spacing=5, padding=10)

    for unidade in todas_unidades:
        leitura = leituras_dict.get(unidade)

        if leitura:
            # Unidade já possui leitura
            valor_c = float(leitura.get("valor", 0))
            data_leitura = leitura.get("data_leitura", "")[:10]

            # Botão de WhatsApp para consumo alto
            btn_alerta = ft.IconButton(
                icon=ft.Icons.WHATSAPP,
                icon_color="green",
                tooltip="Alertar Suspeita de Vazamento",
                on_click=lambda e, u=unidade, v=valor_c: enviar_alerta_whatsapp(
                    page, f"🚨 *ÁguaFlow: Alerta de Consumo*\nUnidade: {u}\nConsumo atual: {v} m³\nVerificamos um valor acima da média. Por favor, cheque suas torneiras."
                )
            ) if valor_c > 15.0 else None

            lista_unidades.controls.append(
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.WATER_DROP, color="green" if valor_c <= 15 else "red"),
                    title=ft.Text(unidade, weight="bold"),
                    subtitle=ft.Text(f"Lido: {valor_c} m³ em {data_leitura}"),
                    trailing=btn_alerta,
                    bgcolor="#1b5e2033" if valor_c <= 15 else "#b71c1c33"
                )
            )
        else:
            # Unidade pendente - pronta para receber leitura
            lista_unidades.controls.append(
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.WATER_DROP_OUTLINED, color="grey"),
                    title=ft.Text(unidade, italic=True),
                    subtitle=ft.Text("Aguardando leitura", size=12, color="grey"),
                    trailing=ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE, color="amber", tooltip="Pronta para leitura")
                )
            )

    # --- CONSTRUÇÃO DA VIEW ---
    return ft.View(
        route="/dashboard",
        appbar=ft.AppBar(
            title=ft.Text("Dashboard de Consumo"),
            leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=voltar),
            bgcolor=ft.Colors.SURFACE_VARIANT
        ),
        controls=[
            ft.Column([
                # Cartões de Métricas (Melhoria Visual)
                ft.Row([
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Total Geral", size=12, color="blue"),
                            ft.Text(f"{total_consumo:.1f} m³", size=20, weight="bold")
                        ]),
                        bgcolor="#1e1e1e", padding=15, border_radius=10, expand=True
                    ),
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Média Mensal", size=12, color="green"),
                            ft.Text(f"{media_consumo:.1f} m³", size=20, weight="bold")
                        ]),
                        bgcolor="#1e1e1e", padding=15, border_radius=10, expand=True
                    ),
                ], spacing=10),

                # Progresso das leituras
                ft.Row([
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Unidades Lidas", size=12, color="green"),
                            ft.Text(f"{unidades_lidas}/{len(todas_unidades)}", size=20, weight="bold")
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

                ft.Text("Estatísticas Mensais", size=16, weight="bold"),
                ft.Container(content=chart, height=200, padding=15, bgcolor=ft.Colors.BLACK26, border_radius=10),

                ft.Divider(height=10, color="transparent"),
                ft.Text("Todas as Unidades (96)", size=16, weight="bold"),
                ft.Container(
                    content=lista_unidades,
                    height=400,
                    bgcolor="#1e1e1e",
                    border_radius=10,
                    border=ft.border.all(1, "#333333")
                ),

            ], scroll=ft.ScrollMode.ADAPTIVE, spacing=15, padding=20)
        ]
    )