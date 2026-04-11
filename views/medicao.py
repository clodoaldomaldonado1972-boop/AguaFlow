import flet as ft
from database.database import Database

def montar_tela_medicao(page: ft.Page):
    # Campos de entrada
    txt_unidade = ft.TextField(label="Unidade (Apto/Casa)", width=300)
    txt_leitura = ft.TextField(
        label="Leitura Atual", 
        width=300, 
        keyboard_type=ft.KeyboardType.NUMBER,
        hint_text="Ex: 123.45",
        max_length=10,  # Impede números infinitos
        # Filtro: permite apenas números e um ponto ou vírgula
        input_filter=ft.InputFilter(
            allow=True, 
            regex_string=r"^[0-9]*[.,]?[0-9]{0,2}$", 
            replacement_string=""
        )
    )
    
    lbl_resultado = ft.Text("", size=16, color="blue", weight="bold")

    def processar_valor(valor_str):
        """Função auxiliar para tratar as casas decimais"""
        try:
            # Substitui vírgula por ponto para o Python não quebrar
            valor_float = float(valor_str.replace(',', '.'))
            
            # REGRA: Queremos 2 casas para exibição padrão, 
            # mas limitamos a 7 para evitar estouro de ponto flutuante.
            valor_limitado = round(valor_float, 7)
            
            # Retorna formatado com 2 casas para o usuário, mas guarda até 7 se necessário
            return valor_limitado
        except ValueError:
            return None

    def validar_e_formatar(e):
        valor = processar_valor(txt_leitura.value)
        if valor is not None:
            # Exibimos com 2 casas no campo para ficar limpo (: .2f)
            txt_leitura.value = f"{valor:.2f}"
            lbl_resultado.value = f"Validado: {txt_leitura.value} m³"
            lbl_resultado.color = "green"
        else:
            lbl_resultado.value = "Erro: Digite um número válido."
            lbl_resultado.color = "red"
        page.update()

    def salvar_dados(e):
        if not txt_unidade.value or not txt_leitura.value:
            page.snack_bar = ft.SnackBar(ft.Text("Preencha todos os campos!"), open=True)
            page.update()
            return

        leitura_final = processar_valor(txt_leitura.value)
        
        if leitura_final is not None:
            try:
                # Aqui salvamos com a precisão de até 7 casas, mas sem passar disso
                # Database.salvar_medicao(txt_unidade.value, leitura_final)
                
                page.snack_bar = ft.SnackBar(
                    ft.Text(f"Sucesso! Leitura: {leitura_final:.2f}"), 
                    bgcolor="green", 
                    open=True
                )
                txt_leitura.value = ""
                txt_unidade.value = ""
                lbl_resultado.value = ""
            except Exception as ex:
                page.snack_bar = ft.SnackBar(ft.Text(f"Erro ao salvar: {ex}"), open=True)
        else:
            page.snack_bar = ft.SnackBar(ft.Text("Valor inválido para salvar."), open=True)
        
        page.update()

    return ft.View(
        route="/medicao",
        horizontal_alignment="center",
        vertical_alignment="center",
        controls=[
            ft.AppBar(
                title=ft.Text("Realizar Medição"),
                bgcolor="blue",
                leading=ft.IconButton("arrow_back", on_click=lambda _: page.go("/menu"))
            ),
            ft.Column(
                controls=[
                    ft.Icon("speed", size=50, color="blue"),
                    ft.Text("Registro de Consumo", size=20, weight="bold"),
                    txt_unidade,
                    txt_leitura,
                    ft.ElevatedButton("FORMATAR (2 CASAS)", on_click=validar_e_formatar),
                    lbl_resultado,
                    ft.Divider(),
                    ft.ElevatedButton(
                        "CONFIRMAR E SALVAR", 
                        icon="save", 
                        width=300, 
                        on_click=salvar_dados
                    ),
                    ft.TextButton("Voltar ao Menu", on_click=lambda _: page.go("/menu"))
                ],
                horizontal_alignment="center",
                spacing=15
            )
        ]
    )