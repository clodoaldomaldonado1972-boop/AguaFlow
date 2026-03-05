import flet as ft
import database as db

def montar_tela(page, voltar_menu):
    # Puxa a próxima unidade que ainda não tem leitura_atual
    unidade = db.buscar_proximo_pendente()
    
    # Se não houver unidade pendente, mostra a tela de conclusão
    if not unidade:
        return ft.Container(
            content=ft.Column([
                ft.Icon(ft.icons.CHECK_CIRCLE, color="green", size=60),
                ft.Text("Medição Concluída!", size=20, weight="bold"),
                ft.Text("Todas as unidades foram lidas.", color="grey"),
                ft.FilledButton("Voltar ao Menu", 
                    on_click=lambda _: (page.controls.clear(), voltar_menu(None), page.update()))
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=50
        )

    # Dados vindos do banco
    id_db, nome_unidade, leitura_anterior = unidade[0], unidade[1], unidade[2]
    
    texto_consumo = ft.Text("Consumo: 0.00 m³", size=18, color="blue", weight="bold")
    
    def calcular_ao_digitar(e):
        try:
            if input_valor.value:
                # Remove espaços e troca vírgula por ponto
                val_limpo = input_valor.value.strip().replace(",", ".")
                atual = float(val_limpo)
                consumo = atual - leitura_anterior
                texto_consumo.value = f"Consumo: {consumo:.2f} m³"
                texto_consumo.color = "red" if consumo > 20 else "blue"
            else:
                texto_consumo.value = "Consumo: 0.00 m³"
        except ValueError:
            texto_consumo.value = "Consumo: ---"
        page.update()

    # --- INPUT COM LIMITE DE CARACTERES E FILTRO ---
    # --- INPUT COM LIMITE DE CARACTERES E FILTRO ---
    input_valor = ft.TextField(
        label="Leitura Atual (m³)", 
        keyboard_type=ft.KeyboardType.NUMBER, 
        autofocus=True,
        max_length=7,           # LIMITE DE CARACTERES (Ajuste conforme necessário)
        # Removido counter_text para evitar o erro de __init__
        input_filter=ft.InputFilter(allow=True, regex_string=r"^[0-9,.]*$", replacement_string=""),
        on_change=calcular_ao_digitar,
        on_submit=lambda _: salvar_leitura(None)
    )

    def salvar_leitura(e):
        if not input_valor.value:
            abrir_alerta_pular()
        else:
            try:
                valor = float(input_valor.value.replace(",", "."))
                db.registrar_leitura(id_db, valor)
                
                # RESET DA TELA: Remove tudo e recarrega a função para a próxima unidade
                page.controls.clear()
                page.add(montar_tela(page, voltar_menu))
                page.update()
            except ValueError:
                input_valor.error_text = "Número inválido"
                page.update()

    def abrir_alerta_pular():
        def confirmar_pulo(e):
            db.registrar_leitura(id_db, 0.0, status="pulado")
            dlg.open = False
            page.controls.clear()
            page.add(montar_tela(page, voltar_menu))
            page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("Pular Unidade?"),
            content=ft.Text(f"Deseja pular o apto {nome_unidade}?"),
            actions=[
                ft.TextButton("Sim, Pular", on_click=confirmar_pulo),
                ft.TextButton("Cancelar", on_click=lambda _: (setattr(dlg, "open", False), page.update()))
            ]
        )
        page.dialog = dlg
        dlg.open = True
        page.update()

    # Retorna o layout estruturado
    return ft.Container(
        padding=30,
        content=ft.Column([
            ft.Text(f"Unidade: {nome_unidade}", size=30, weight="bold"),
            ft.Text(f"Leitura Anterior: {leitura_anterior:.2f} m³", size=16, color="grey"),
            ft.Divider(),
            input_valor,
            texto_consumo,
            ft.Row([
                ft.FilledButton("SALVAR", 
                    on_click=salvar_leitura, 
                    style=ft.ButtonStyle(bgcolor="green", color="white"), 
                    expand=True),
                ft.IconButton(ft.icons.SKIP_NEXT, on_click=lambda _: abrir_alerta_pular(), icon_color="red"),
            ]),
            ft.TextButton("Interromper e Sair", 
                on_click=lambda _: (page.controls.clear(), voltar_menu(None), page.update()))
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )