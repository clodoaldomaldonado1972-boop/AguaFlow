import flet as ft
from datetime import datetime
from database.database import Database
import views.styles as st  # Importa seus estilos personalizados
from flet import colors  # Importar colors para uso direto
# Importa a fábrica de gráficos (Certifique-se que o arquivo existe em utils/)
from utils.graficos_factory import criar_grafico_evolucao


def montar_tela_dashboard(page: ft.Page, ao_voltar):
    # --- 1. BUSCA DE DADOS ---
    leituras_feitas = Database.get_leituras_mes_atual()  # Busca dados do mês no SQLite
    todas_unidades = Database._gerar_lista_unidades()  # Lista das 98 unidades

    # Cálculos Analíticos
    lidas = len({l['unidade_id'] for l in leituras_feitas})
    unidades_pendentes = len(todas_unidades) - lidas
    unidades_lidas_nomes = [l['unidade_id'] for l in leituras_feitas]

    total_agua = sum(item.get('leitura_agua', 0)
                     or 0 for item in leituras_feitas)
    total_gas = sum(item.get('leitura_gas', 0)
                    or 0 for item in leituras_feitas)
    media_agua = total_agua / lidas if lidas > 0 else 0

    # --- 2. FUNÇÃO PARA EXIBIR DETALHES (Interatividade) ---
    def abrir_detalhes_unidade(e, unidade):
        # Busca o histórico real no banco local
        historico = Database.buscar_historico(unidade)

        # Gera o gráfico usando a factory externa
        grafico_comp = criar_grafico_evolucao(historico, f"Unidade {unidade}")

        def fechar_bs(e):
            bs.open = False
            page.update()

        bs = ft.BottomSheet(
            ft.Container(
                padding=20,
                bgcolor="#1e1e1e",  # Cor direta para evitar erro de modulo 'styles'
                border_radius=ft.border_radius.only(top_left=20, top_right=20),
                content=ft.Column([
                    ft.Row([
                        ft.Text(
                            f"Evolução: Unidade {unidade}", size=20, weight="bold"),
                        ft.IconButton("close",
                                      on_click=fechar_bs, icon_color="red")
                        # Corrigido alinhamento, padronizado ícone
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, icon="close"),
                    ft.Divider(),
                    ft.Container(content=grafico_comp, height=250, padding=10),
                    ft.Text(f"Acumulado no mês: {total_agua:.2f} m³",
                            size=12, color="grey", italic=True),
                    # Corrigido alinhamento
                ], tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            ),
            open=True,
        )
        page.overlay.append(bs)
        page.update()

    # --- 3. CONSTRUÇÃO DO MAPA DE COLETA ---
    lista_unidades_controles = []
    for u in todas_unidades:
        esta_lida = u in unidades_lidas_nomes
        # CORREÇÃO 1: Usando strings para cores ("green", "red") para evitar NameError
        cor_fundo = "green" if esta_lida else "red"

        lista_unidades_controles.append(
            ft.Container(
                content=ft.Text(u, size=10, weight="bold", color="white"),
                # CORREÇÃO 2: Ajustado para ft.alignment.Center (PascalCase)
                alignment="center",
                bgcolor=cor_fundo,
                border_radius=5,
                on_click=lambda e, unidade=u: abrir_detalhes_unidade(
                    e, unidade),
                tooltip=f"Clique para ver evolução da Unidade {u}",
                ink=True,
            )
        )

    # --- 4. INTERFACE PRINCIPAL ---
    return ft.View(
        route="/dashboard",
        bgcolor=st.BG_DARK,
        controls=[
            ft.AppBar(
                title=ft.Text("Análise Vivere Prudente"),
                bgcolor=st.PRIMARY_BLUE,
                leading=ft.IconButton("arrow_back", on_click=ao_voltar)
            ),
            ft.Column(
                scroll=ft.ScrollMode.ADAPTIVE,
                controls=[
                    ft.Container(height=10),
                    # Cards de Resumo
                    ft.ResponsiveRow([
                        st.criar_card_metrica("Lidas", str(
                            lidas), "check_circle", "green", 3),
                        st.criar_card_metrica("Pendentes", str(
                            unidades_pendentes), "pending", st.ACCENT_ORANGE, 3),
                        st.criar_card_metrica(
                            "Total Água", f"{total_agua:.1f}m³", "water_drop", st.PRIMARY_BLUE, 3),
                        st.criar_card_metrica(
                            "Total Gás", f"{total_gas:.1f}m³", "local_fire_department", st.ACCENT_ORANGE, 3),
                    ]),

                    ft.Text("Mapa de Coleta (Clique na unidade)",
                            size=16, weight="bold"),
                    ft.Container(
                        content=ft.GridView(
                            controls=lista_unidades_controles,
                            runs_count=6,
                            max_extent=60,
                            spacing=5,
                            run_spacing=5,
                        ),
                        height=400,
                        bgcolor="#1e1e1e",
                        padding=10,
                        border_radius=10
                    ),

                    ft.ElevatedButton(
                        "VOLTAR AO MENU",
                        on_click=ao_voltar,
                        width=400,
                        # st.BTN_MAIN deve estar definido em views/styles.py
                        style=st.BTN_MAIN if hasattr(st, 'BTN_MAIN') else None
                    )
                ]
            )
        ]
    )
