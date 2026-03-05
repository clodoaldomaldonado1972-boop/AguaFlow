import flet as ft
import database as db

def montar_tela(page, voltar_menu):
    # Puxa a próxima unidade que ainda não tem leitura_atual
    unidade = db.buscar_proximo_pendente()
    
    # Se não houver unidade pendente, mostra a tela de conclusão
    if not unidade:
        return ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.CHECK_CIRCLE, color="green", size=60),
                ft.Text("Medição Concluída!", size=20, weight="bold"),
                ft.Text("Todas as unidades foram lidas.", color="grey"),
                # AJUSTE 1: Limpar antes de voltar
                ft.ElevatedButton("Voltar ao Menu", on_click=lambda _: (page.controls.clear(), voltar_menu(), page.update()))
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=50
        )

    # Dados vindos do banco
    id_db, nome_unidade, leitura_anterior = unidade[0], unidade[1], unidade[2]
    
    texto_consumo = ft.Text("Consumo: 0.00 m³", size=18, color="blue", weight="bold")
    
    def calcular_ao_digitar(e):
        try:
            if input_valor.value:
                atual = float(input_valor.value.replace(",", "."))
                consumo = atual - leitura_anterior
                texto_consumo.value = f"Consumo: {consumo:.2f} m³"
                texto_consumo.color = "red" if consumo > 20 else "blue"
            else:
                texto_consumo.value = "Consumo: 0.00 m³"
        except ValueError:
            texto_consumo.value = "Consumo: ---"
        page.update()

    input_valor = ft.TextField(
        label="Leitura Atual (m³)", 
        keyboard_type=ft.KeyboardType.NUMBER, 
        autofocus=True,
        on_change=calcular_ao_digitar
    )

    def salvar_leitura(e):
        if not input_valor.value:
            abrir_alerta_pular()
        else:
            try:
                valor = float(input_valor.value.replace(",", "."))
                db.registrar_leitura(id_db, valor)
                page.controls.clear()
                # AJUSTE 2: Recarregar a tela passando a função de volta original
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

    return ft.Container(
        padding=30,
        content=ft.Column([
            ft.Text(f"Unidade: {nome_unidade}", size=30, weight="bold"),
            ft.Text(f"Leitura Anterior: {leitura_anterior:.2f} m³", size=16, color="grey"),
            ft.Divider(),
            input_valor,
            texto_consumo,
            ft.Row([
                ft.ElevatedButton("SALVAR", on_click=salvar_leitura, bgcolor="green", color="white", expand=True),
                ft.IconButton(ft.Icons.SKIP_NEXT, on_click=lambda _: abrir_alerta_pular(), icon_color="red"),
            ]),
            # AJUSTE 3: Limpar antes de interromper
            ft.TextButton("Interromper e Sair", on_click=lambda _: (page.controls.clear(), voltar_menu(), page.update()))
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )