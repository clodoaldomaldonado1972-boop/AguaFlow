import flet as ft
import database


def main(page: ft.Page):
    page.title = "AguaFlow - Gestão Condominial"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20

    # --- LISTA DE UNIDADES ---
    unidades = ["Hidrômetro Geral", "Área de Lazer",
                "Apto 166", "Apto 165", "Apto 164"]
    indice = [0]

    # --- ELEMENTOS DA INTERFACE ---
    txt_unidade_atual = ft.Text(
        f"Unidade Atual: {unidades[0]}", size=24, weight="bold", color="blue900")
    input_agua = ft.TextField(label="Hidrômetro de Água (m³)",
                              icon=ft.icons.WATER, keyboard_type=ft.KeyboardType.NUMBER)
    input_gas = ft.TextField(label="Medidor de Gás (m³)",
                             icon=ft.icons.OPACITY, keyboard_type=ft.KeyboardType.NUMBER)

    tabela_historico = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Unidade")),
            ft.DataColumn(ft.Text("Leitura (m³)")),
            ft.DataColumn(ft.Text("Consumo (m³)")),
            ft.DataColumn(ft.Text("Gás")),
        ],
        rows=[]
    )

    # --- FUNÇÃO DO BOTÃO SALVAR ---
    def btn_proximo_click(e):
        if not input_agua.value:
            input_agua.error_text = "Campo obrigatório"
            page.update()
            return

        # 1. Busca leitura anterior e calcula consumo
        leitura_anterior = database.buscar_ultima_leitura(unidades[indice[0]])
        leitura_atual = float(input_agua.value)
        consumo = leitura_atual - leitura_anterior

        # 2. Salva no Banco de Dados Real
        database.salvar_leitura(
            unidades[indice[0]], leitura_atual, input_gas.value)

        # 3. Adiciona na Tabela de Histórico (Visual)
        tabela_historico.rows.append(
            ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(unidades[indice[0]])),
                    ft.DataCell(ft.Text(str(leitura_atual))),
                    # Se o consumo for maior que 20m3, fica vermelho (alerta de vazamento)
                    ft.DataCell(
                        ft.Text(f"{consumo:.2f}", color="red" if consumo > 20 else "blue")),
                    ft.DataCell(
                        ft.Text(input_gas.value if input_gas.value else "-")),
                ]
            )
        )

        # 4. Lógica de avançar para a próxima unidade
        if indice[0] < len(unidades) - 1:
            indice[0] += 1
            txt_unidade_atual.value = f"Unidade Atual: {unidades[indice[0]]}"
            input_agua.value = ""
            input_gas.value = ""
            input_agua.error_text = None
        else:
            txt_unidade_atual.value = "✅ Todas as leituras concluídas!"
            btn_salvar.disabled = True

        page.update()

    # --- LAYOUT DAS ABAS ---
    btn_salvar = ft.ElevatedButton("Salvar e Próximo", icon=ft.icons.SAVE,
                                   on_click=btn_proximo_click, bgcolor="blue900", color="white")

    aba_leitura = ft.Column([
        ft.Text("Medição de Água e Gás", size=25,
                weight="bold", color="blue900"),
        ft.Divider(),
        txt_unidade_atual,
        input_agua,
        input_gas,
        btn_salvar
    ])

    aba_historico = ft.Column([
        ft.Text("Histórico de Leituras", size=25, weight="bold"),
        ft.Container(content=tabela_historico, height=400, on_scroll=True)
    ])

    # Montagem Final
    t = ft.Tabs(
        selected_index=0,
        tabs=[
            ft.Tab(text="Leitura", icon=ft.icons.EDIT, content=aba_leitura),
            ft.Tab(text="Histórico", icon=ft.icons.LIST_ALT,
                   content=aba_historico),
        ],
        expand=1
    )

    page.add(t)


ft.app(target=main)
