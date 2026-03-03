import flet as ft
import database  # Importa todas as funções que criamos acima

def main(page: ft.Page):
    # Configurações básicas da página
    page.title = "AguaFlow - Gestão Condominial"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    
    # Ordem das unidades para medição (Sequenciamento)
    unidades = ["Hidrometro Geral", "Area de Lazer", "Apto 166", "Apto 165", "Apto 164"]
    indice_atual = [0] # Usamos lista para poder alterar o valor dentro da função

    # Elementos Visuais
    lbl_unidade = ft.Text(f"Unidade Atual: {unidades[0]}", size=24, weight="bold", color="blue900")
    txt_agua = ft.TextField(label="Leitura Agua (m³)", icon=ft.icons.WATER, keyboard_type=ft.KeyboardType.NUMBER)
    txt_gas = ft.TextField(label="Leitura Gas (m³)", icon=ft.icons.OPACITY, keyboard_type=ft.KeyboardType.NUMBER)

    # Tabela de Histórico (vazia inicialmente)
    tabela_resumo = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Unidade")),
            ft.DataColumn(ft.Text("Consumo (m³)")),
            ft.DataColumn(ft.Text("Gas")),
        ],
        rows=[]
    )

    # FUNÇÃO: Salvar e Calcular
    def salvar_clique(e):
        if not txt_agua.value:
            txt_agua.error_text = "Por favor, insira a leitura da água"
            page.update()
            return

        # 1. Lógica de Consumo: Atual - Anterior
        valor_anterior = database.buscar_ultima_leitura(unidades[indice_atual[0]])
        valor_atual = float(txt_agua.value)
        consumo = valor_atual - valor_anterior

        # 2. Salva no Banco de Dados
        database.salvar_leitura(unidades[indice_atual[0]], valor_atual, txt_gas.value)

        # 3. Atualiza a Tabela de Histórico na Aba 2
        tabela_resumo.rows.append(
            ft.DataRow(cells=[
                ft.DataCell(ft.Text(unidades[indice_atual[0]])),
                # Alerta: Se consumo for maior que 20, fica vermelho
                ft.DataCell(ft.Text(f"{consumo:.2f}", color="red" if consumo > 20 else "blue")),
                ft.DataCell(ft.Text(txt_gas.value)),
            ])
        )

        # 4. Avança para a próxima unidade da lista
        if indice_atual[0] < len(unidades) - 1:
            indice_atual[0] += 1
            lbl_unidade.value = f"Unidade Atual: {unidades[indice_atual[0]]}"
            txt_agua.value = ""
            txt_gas.value = ""
        else:
            lbl_unidade.value = "✅ Todas as unidades foram medidas!"
            btn_salvar.disabled = True
        
        page.update()

    # FUNÇÃO: Gerar PDF
    def gerar_pdf_clique(e):
        nome_pdf = database.gerar_pdf_relatorio()
        page.snack_bar = ft.SnackBar(ft.Text(f"Arquivo {nome_pdf} criado!"), bgcolor="green")
        page.snack_bar.open = True
        page.update()

    # MONTAGEM DAS ABAS
    btn_salvar = ft.ElevatedButton("Salvar Leitura", on_click=salvar_clique, bgcolor="blue900", color="white")
    
    aba_leitura = ft.Column([
        ft.Text("Medicao em Tempo Real", size=20, weight="bold"),
        ft.Divider(),
        lbl_unidade,
        txt_agua,
        txt_gas,
        btn_salvar
    ])

    aba_historico = ft.Column([
        ft.Text("Resumo da Sessao", size=20, weight="bold"),
        tabela_resumo,
        ft.ElevatedButton("Exportar Relatorio PDF", icon=ft.icons.PICTURE_AS_PDF, on_click=gerar_pdf_clique, color="white", bgcolor="red700")
    ])

    # Barra de Navegação Superior
    tabs = ft.Tabs(
        selected_index=0,
        tabs=[
            ft.Tab(text="Leitura", content=aba_leitura),
            ft.Tab(text="Historico", content=aba_historico),
        ],
        expand=1
    )

    page.add(tabs)

ft.app(target=main)