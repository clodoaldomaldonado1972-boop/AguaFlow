import flet as ft
from datetime import datetime
from database.database import Database
from views import styles as st
# Importa a fábrica de gráficos que vamos criar no ficheiro à parte
from utils.graficos_factory import criar_grafico_evolucao

def montar_tela_dashboard(page: ft.Page, ao_voltar):
    # --- 1. BUSCA DE DADOS ---
    leituras_feitas = Database.get_leituras_mes_atual()
    lidas = len(leituras_feitas)
    todas_unidades = Database._gerar_lista_unidades()
    unidades_pendentes = len(todas_unidades) - lidas
    unidades_lidas_nomes = [l['unidade'] for l in leituras_feitas]

    # --- 2. FUNÇÃO PARA EXIBIR DETALHES (Interatividade) ---
    def abrir_detalhes_unidade(e, unidade):
        # Busca o histórico real no banco (precisa existir o método no database.py)
        historico = Database.get_historico_unidade(unidade)
        
        # Gera o gráfico usando a nossa factory externa
        grafico_comp = criar_grafico_evolucao(historico, f"Unidade {unidade}")

        def fechar_bs(e):
            bs.open = False
            page.update()

        bs = ft.BottomSheet(
            ft.Container(
                padding=20,
                bgcolor="#1e1e1e",
                border_radius=ft.border_radius.only(top_left=20, top_right=20),
                content=ft.Column([
                    ft.Row([
                        ft.Text(f"Evolução: Unidade {unidade}", size=20, weight="bold"),
                        ft.IconButton(ft.icons.CLOSE, on_click=fechar_bs)
                    ], alignment="spaceBetween"),
                    ft.Divider(),
                    ft.Container(content=grafico_comp, height=250, padding=10),
                    ft.Text("Média mensal calculada com base nos últimos 6 meses.", 
                            size=12, color="grey", italic=True),
                ], tight=True, horizontal_alignment="center"),
            ),
            open=True,
        )
        page.overlay.append(bs)
        page.update()

    # --- 3. CONSTRUÇÃO DO MAPA DE COLETA ---
    lista_unidades_controles = []
    for u in todas_unidades:
        esta_lida = u in unidades_lidas_nomes
        lista_unidades_controles.append(
            ft.Container(
                content=ft.Text(u, size=10, weight="bold", color="white"),
                alignment=ft.alignment.center,
                bgcolor=ft.colors.GREEN_800 if esta_lida else ft.colors.RED_900,
                border_radius=5,
                # IHC: Feedback visual ao passar o rato e clique para ver detalhes
                on_click=lambda e, unidade=u: abrir_detalhes_unidade(e, unidade),
                tooltip=f"Clique para ver evolução da Unidade {u}",
                ink=True, # Efeito de clique material design
            )
        )

    # --- 4. INTERFACE PRINCIPAL ---
    return ft.View(
        route="/dashboard",
        bgcolor=st.BG_DARK,
        controls=[
            ft.AppBar(
                title=ft.Text("Dashboard de Consumo"),
                bgcolor=st.PRIMARY_BLUE,
                leading=ft.IconButton(ft.icons.ARROW_BACK, on_click=ao_voltar)
            ),
            ft.Column(
                scroll=ft.ScrollMode.ADAPTIVE,
                controls=[
                    ft.Container(height=10),
                    # Cards de Resumo
                    ft.Row([
                        ft.Container(
                            content=ft.Column([
                                ft.Icon(ft.icons.CHECK_CIRCLE, color="green"),
                                ft.Text("Lidas"),
                                ft.Text(str(lidas), size=24, weight="bold")
                            ], horizontal_alignment="center"),
                            bgcolor="#1e1e1e", padding=15, border_radius=10, expand=True
                        ),
                        ft.Container(
                            content=ft.Column([
                                ft.Icon(ft.icons.PENDING, color="orange"),
                                ft.Text("Pendentes"),
                                ft.Text(str(unidades_pendentes), size=24, weight="bold")
                            ], horizontal_alignment="center"),
                            bgcolor="#1e1e1e", padding=15, border_radius=10, expand=True
                        ),
                    ], spacing=10),

                    ft.Text("Mapa de Coleta (Clique na unidade para detalhes)", size=16, weight="bold"),
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
                        style=st.BTN_MAIN
                    )
                ]
            )
        ]
    )