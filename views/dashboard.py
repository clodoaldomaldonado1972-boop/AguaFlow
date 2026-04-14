import flet as ft
from datetime import datetime
from database.database import Database
from utils.alertas_engine import enviar_alerta_MESSAGE

def montar_tela_dashboard(page: ft.Page, voltar):
    # --- 1. BUSCA DE DADOS (Compatibilidade com novo Schema) ---
    try:
        leituras = Database.buscar_todas_leituras()
    except Exception:
        leituras = []

    leituras_dict = {}
    for leitura in leituras:
        u = leitura.get("unidade", "N/A")
        leituras_dict[u] = leitura

    # 2. Geração da Lista Estática (96 Unidades)
    todas_unidades = []
    for andar in range(16, 0, -1):
        for apto in range(1, 7):
            todas_unidades.append(f"Apto {andar}{apto}")

    # 3. Lógica de Consumo Mensal (Fix: leitura_agua)
    meses_nomes = {1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr"}
    consumo_por_mes = {nome: 0.0 for nome in meses_nomes.values()}

    for leitura in leituras:
        try:
            # Pegamos o valor da nova coluna 'leitura_agua'
            valor_lido = float(leitura.get("leitura_agua", 0))
            data_str = leitura.get("data_leitura", "")[:10]
            data = datetime.strptime(data_str, "%Y-%m-%d")
            if data.month in meses_nomes:
                consumo_por_mes[meses_nomes[data.month]] += valor_lido
        except:
            continue

    meses_lista = list(consumo_por_mes.keys())
    valores_lista = list(consumo_por_mes.values())
    total_consumo = sum(valores_lista)
    media_consumo = total_consumo / len(valores_lista) if valores_lista else 0
    unidades_lidas = len(leituras_dict)
    unidades_pendentes = len(todas_unidades) - unidades_lidas

    # --- 4. UI: COMPONENTE DE GRÁFICO ---
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

    # --- 5. UI: LISTA DE UNIDADES ---
    lista_unidades = ft.ListView(expand=True, spacing=5)

    for unidade in todas_unidades:
        leitura = leituras_dict.get(unidade)
        if leitura:
            valor_c = float(leitura.get("leitura_agua", 0))
            data_l = leitura.get("data_leitura", "")[:10]
            
            # Botão de Alerta condicional
            btn_alerta = ft.IconButton(
                icon=ft.icons.MESSAGE,
                icon_color="green",
                on_click=lambda e, u=unidade, v=valor_c: enviar_alerta_MESSAGE(
                    page, f"🚨 *ÁguaFlow*\nUnidade: {u}\nConsumo: {v} m³"
                )
            ) if valor_c > 15.0 else None

            lista_unidades.controls.append(
                ft.ListTile(
                    leading=ft.Icon(ft.icons.WATER_DROP, color="green" if valor_c <= 15 else "red"),
                    title=ft.Text(unidade, weight="bold"),
                    subtitle=ft.Text(f"Lido: {valor_c} m³ em {data_l}"),
                    trailing=btn_alerta,
                    bgcolor="#1b5e2033" if valor_c <= 15 else "#b71c1c33"
                )
            )
        else:
            lista_unidades.controls.append(
                ft.ListTile(
                    leading=ft.Icon(ft.icons.WATER_DROP_OUTLINED, color="grey"),
                    title=ft.Text(unidade, italic=True),
                    subtitle=ft.Text("Pendente", size=12, color="grey"),
                    trailing=ft.Icon(ft.icons.ADD_CIRCLE_OUTLINE, color="amber")
                )
            )

    # --- 6. CONSTRUÇÃO FINAL (FIX: TypeError Padding) ---
    return ft.View(
        route="/dashboard",
        appbar=ft.AppBar(
            title=ft.Text("Dashboard de Consumo"),
            leading=ft.IconButton(ft.icons.ARROW_BACK, on_click=voltar),
            bgcolor=ft.colors.SURFACE_VARIANT
        ),
        controls=[
            ft.Container(
                padding=20, # Padding aplicado no Container, não na Column!
                content=ft.Column([
                    # Cartões de Métricas
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
                    
                    # Progresso
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

                    ft.Text("Estatísticas Mensais", size=16, weight="bold"),
                    ft.Container(content=chart, height=200, padding=15, bgcolor=ft.colors.BLACK26, border_radius=10),
                    
                    ft.Divider(height=10, color="transparent"),
                    ft.Text("Unidades (96)", size=16, weight="bold"),
                    ft.Container(content=lista_unidades, height=400, bgcolor="#1e1e1e", border_radius=10),
                ], scroll=ft.ScrollMode.ADAPTIVE, spacing=15)
            )
        ]
    )