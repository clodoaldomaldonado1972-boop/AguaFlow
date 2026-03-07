import flet as ft
import database as db
import estilos as st


def montar_tela(page, voltar_menu):
    # 1. BUSCA DE DADOS
    unidade = db.buscar_proximo_pendente()
    
    # LOG DE TESTE: Adicione isso para ver no terminal se ele achou alguém
    print(f"DEBUG: Unidade encontrada para ler: {unidade}")

    # 2. TELA DE CONCLUSÃO (Se não houver nada para ler)
    if not unidade:
        return ft.Container(
            expand=True,
            bgcolor="#1A1C1E",
            alignment=ft.Alignment(0, 0), # Usando a coordenada fixa que não dá erro
            content=ft.Column([
                ft.Icon(ft.Icons.CHECK_CIRCLE, color="green", size=80),
                ft.Text("Medição Concluída!", size=24, weight="bold", color="white"),
                ft.ElevatedButton("Voltar ao Menu", on_click=lambda _: voltar_menu())
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )
    
    # 3. SE HOUVER UNIDADE, MONTA O RESTO...
    id_db, nome_unidade, leitura_anterior = unidade[0], unidade[1], unidade[2]
    # ... resto do seu código de layout ...

    # 3. MAPEAMENTO DE DADOS
    id_db, nome_unidade, leitura_anterior = unidade[0], unidade[1], unidade[2]

    texto_consumo = ft.Text("Consumo: 0.00 m³", size=18,
                            color=st.COR_PRIMARIA, weight="bold")

    def calcular_ao_digitar(e):
        try:
            if input_valor.value:
                val_limpo = input_valor.value.strip().replace(",", ".")
                atual = float(val_limpo)
                consumo = atual - leitura_anterior
                texto_consumo.value = f"Consumo: {consumo:.2f} m³"
                texto_consumo.color = st.COR_ALERTA if consumo > 20 else st.COR_PRIMARIA
            else:
                texto_consumo.value = "Consumo: 0.00 m³"
        except ValueError:
            texto_consumo.value = "Consumo: ---"
        page.update()

    # 4. CAMPO DE ENTRADA
    input_valor = ft.TextField(
        label="Leitura Atual (m³)",
        keyboard_type=ft.KeyboardType.NUMBER,
        autofocus=True,
        color="white",
        on_change=calcular_ao_digitar,
        # Quando der Enter, ele salva e recarrega a tela
        on_submit=lambda _: salvar_leitura(None)
    )

    # 5. LÓGICA DE SALVAMENTO (SEM CLEAR PAGE)
    def recarregar_interface():
        """
        Em vez de limpar a página toda, nós apenas chamamos 
        a função de montagem novamente através do disparador do menu.
        """
        # Isso força o main.py a redesenhar o 'palco' com a próxima unidade
        page.go("/temp")  # Um truque simples para resetar o foco se necessário
        voltar_menu()
        # Chamamos o iniciar leitura de novo automaticamente
        page.controls[0].content.content.controls[2].on_click(None)

    def salvar_leitura(e):
        if not input_valor.value:
            abrir_alerta_pular()
        else:
            try:
                valor = float(input_valor.value.replace(",", "."))
                db.registrar_leitura(id_db, valor)
                # O segredo: Chamamos a função do main para recarregar o módulo
                page.controls[0].content.content.controls[2].on_click(None)
            except ValueError:
                input_valor.error_text = "Número inválido"
                page.update()

    def abrir_alerta_pular():
        def confirmar_pulo(e):
            db.registrar_leitura(id_db, 0.0, status="pulado")
            dlg.open = False
            page.update()
            # Recarrega para a próxima
            page.controls[0].content.content.controls[2].on_click(None)

        dlg = ft.AlertDialog(
            title=ft.Text("Pular Unidade?"),
            content=ft.Text("Deseja marcar como pendente?"),
            actions=[
                ft.TextButton("Sim, Pular", on_click=confirmar_pulo),
                ft.TextButton("Cancelar", on_click=lambda _: (
                    setattr(dlg, "open", False), page.update()))
            ]
        )
        page.dialog = dlg
        dlg.open = True
        page.update()

    # 6. LAYOUT FINAL
    return ft.Container(
        expand=True,
        bgcolor="#1A1C1E",
        padding=30,
        content=ft.Column(
            controls=[
                ft.Text(f"Unidade: {nome_unidade}",
                        size=28, weight="bold", color="blue"),
                ft.Text(f"Anterior: {leitura_anterior:.2f} m³",
                        size=18, color="white70"),
                ft.Divider(color="white10"),
                input_valor,
                texto_consumo,
                ft.Container(height=20),
                ft.Row([
                    ft.ElevatedButton(
                        "SALVAR", icon=ft.Icons.SAVE, on_click=salvar_leitura, bgcolor="blue", color="white"),
                    ft.IconButton(icon=ft.Icons.SKIP_NEXT, icon_color="orange",
                                  on_click=lambda _: abrir_alerta_pular())
                ], alignment=ft.MainAxisAlignment.CENTER),
                ft.TextButton("Sair da Medição",
                              on_click=lambda _: voltar_menu())
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20
        )
    )
