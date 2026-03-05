import flet as ft
import database as db

def montar_tela(page, voltar_menu):
    # O bloco de medição pede o próximo apto ao bloco de dados
    unidade = db.buscar_proximo_pendente()
    
    if not unidade:
        return ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.CHECK_CIRCLE, color="green", size=60),
                ft.Text("Medição do Vivere Concluída!", size=20, weight="bold"),
                ft.ElevatedButton("Voltar ao Menu", on_click=lambda _: voltar_menu())
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=50
        )

    id_db, nome_unidade = unidade[0], unidade[1]
    input_valor = ft.TextField(label="Leitura Atual (m³)", keyboard_type="number", autofocus=True)

    def salvar_leitura(e):
        if not input_valor.value:
            abrir_alerta_pular()
        else:
            try:
                # Substitui vírgula por ponto para o banco não dar erro
                valor = float(input_valor.value.replace(",", "."))
                db.registrar_leitura(id_db, valor)
                page.controls.clear()
                page.add(montar_tela(page, voltar_menu))
                page.update()
            except ValueError:
                input_valor.error_text = "Digite um número válido"
                page.update()

    def abrir_alerta_pular():
        def confirmar_pulo(e):
            db.registrar_leitura(id_db, 0.0, status="pulado")
            dlg.open = False
            page.controls.clear()
            page.add(montar_tela(page, voltar_menu))
            page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("Unidade sem leitura"),
            content=ft.Text(f"Deseja pular o apto {nome_unidade} e registrar como 'Não Lido'?"),
            actions=[
                ft.TextButton("Sim, Pular", on_click=confirmar_pulo),
                ft.TextButton("Cancelar", on_click=lambda _: setattr(dlg, "open", False))
            ]
        )
        page.dialog = dlg
        dlg.open = True
        page.update()

    return ft.Container(
        padding=30,
        content=ft.Column([
            ft.Text("Lendo agora:", size=16),
            ft.Text(nome_unidade, size=50, weight="bold", color="blue"),
            input_valor,
            ft.Row([
                ft.ElevatedButton("SALVAR", on_click=salvar_leitura, bgcolor="green", color="white", expand=True),
                # AJUSTADO: Icons com I maiúsculo para evitar erro de atributo
                ft.IconButton(ft.Icons.SKIP_NEXT, on_click=lambda _: abrir_alerta_pular(), icon_color="red"),
            ]),
            ft.TextButton("Interromper e Sair", on_click=lambda _: voltar_menu())
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )