import flet as ft

def main(page: ft.Page):
    page.title = "AguaFlow - Gestão Condominial"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    
    # --- ABA DE LEITURA ---
    def btn_proximo_click(e):
        # Aqui entrará a lógica de pular do 16º para o 15º andar
        print("Avançando unidade...")

    aba_leitura = ft.Column([
        ft.Text("Medição de Água e Gás", size=25, weight="bold", color="blue900"),
        ft.Divider(),
        ft.Text("Unidade Atual: Apto 166", size=18),
        ft.TextField(label="Hidrômetro de Água", icon=ft.icons.WATER_DROP),
        ft.TextField(label="Medidor de Gás", icon=ft.icons.FIRE_EXTINGUISHER),
        ft.ElevatedButton("Salvar Leitura", icon=ft.icons.SAVE, on_click=btn_proximo_click, bgcolor="blue900", color="white")
    ])

    # --- ABA DE HISTÓRICO ---
    aba_historico = ft.Column([
        ft.Text("Histórico de Leituras", size=25, weight="bold"),
        ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Unidade")),
                ft.DataColumn(ft.Text("Água")),
                ft.DataColumn(ft.Text("Gás")),
            ],
            rows=[] # Aqui o banco de dados vai preencher as linhas
        )
    ])

    # --- NAVEGAÇÃO POR ABAS ---
    t = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        tabs=[
            ft.Tab(text="Leitura", content=aba_leitura),
            ft.Tab(text="Histórico", content=aba_historico),
        ],
        expand=1
    )

    page.add(t)

ft.app(target=main)