import flet as ft
import database as db
import estilos as st


def montar_tela(page, voltar_menu):
    """
    Constrói a interface de medição modularizada.
    """

    # 1. BUSCA DE DADOS
    unidade = db.buscar_proximo_pendente()

    # 2. TELA DE CONCLUSÃO (VERSÃO ANTI-BRANCO)
    if not unidade:
        return ft.Container(
            expand=True,           # Força ocupar a largura toda
            height=1000,           # Força uma altura bem grande para garantir o fundo
            bgcolor="#1A1C1E",     # Cor escura total
            alignment=ft.Alignment(0, 0),  # Centraliza o conteúdo
            content=ft.Column([
                ft.Icon(ft.Icons.CHECK_CIRCLE, color="green", size=80),
                ft.Text("Medição Concluída!", size=24,
                        weight="bold", color="white"),
                ft.Text("Todas as unidades foram lidas.", color="white70"),
                ft.Container(height=20),
                # Chama a função de voltar que vem do main.py
                ft.FilledButton("Voltar ao Menu",
                                on_click=lambda _: voltar_menu())
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, tight=True)
        )

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

    # 4. CAMPO DE ENTRADA (Reforço de Cor)
    input_valor = ft.TextField(
        label="Leitura Atual (m³)",
        keyboard_type=ft.KeyboardType.NUMBER,
        autofocus=True,
        max_length=7,
        color="white",  # Garante visibilidade no fundo escuro
        input_filter=ft.InputFilter(
            allow=True, regex_string=r"^[0-9,.]*$", replacement_string=""),
        on_change=calcular_ao_digitar,
        on_submit=lambda _: salvar_leitura(None)
    )

    # 5. LÓGICA DE SALVAMENTO E PULO
    def carregar_proxima():
        """Função auxiliar para trocar o conteúdo do palco sem 'limpar' a página"""
        # Em vez de page.add, usamos a lógica de atualizar o conteúdo do palco
        # Se você estiver usando o 'palco' do main.py, o ideal é chamar a função de navegação
        # Aqui, como é recursivo, apenas limpamos e adicionamos o novo Container
        page.controls.clear()
        page.add(montar_tela(page, voltar_menu))
        page.update()

    def salvar_leitura(e):
        if not input_valor.value:
            abrir_alerta_pular()
        else:
            try:
                valor = float(input_valor.value.replace(",", "."))
                db.registrar_leitura(id_db, valor)
                carregar_proxima()
            except ValueError:
                input_valor.error_text = "Número inválido"
                page.update()

    def abrir_alerta_pular():
        def confirmar_pulo(e):
            db.registrar_leitura(id_db, 0.0, status="pulado")
            dlg.open = False
            carregar_proxima()

        dlg = ft.AlertDialog(
            title=ft.Text("Pular Unidade?"),
            content=ft.Text("Deseja marcar esta unidade como pendente?"),
            actions=[
                ft.TextButton("Sim, Pular", on_click=confirmar_pulo),
                ft.TextButton("Cancelar", on_click=lambda _: (
                    setattr(dlg, "open", False), page.update()))
            ]
        )
        page.dialog = dlg
        dlg.open = True
        page.update()

    # 6. MONTAGEM DA LINHA DE BOTÕES
    linha_botoes = ft.Row(
        controls=[
            st.botao_salvar("SALVAR", salvar_leitura),
            ft.IconButton(
                icon=ft.Icons.SKIP_NEXT,
                icon_color=st.COR_ALERTA,
                on_click=lambda _: abrir_alerta_pular(),
                tooltip="Pular Unidade"
            ),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
    )

    # 7. RETORNO DO LAYOUT (VERSÃO FINAL BLINDADA)
    return ft.Container(
        expand=True,
        alignment=ft.Alignment(0, -1),
        bgcolor="#1A1C1E",
        padding=30,
        content=ft.Column(
            controls=[
                ft.Text(
                    f"Unidade: {nome_unidade}", size=st.FONTE_TITULO, weight="bold", color="blue"),
                ft.Text(f"Anterior: {leitura_anterior:.2f} m³",
                        size=st.FONTE_LABEL, color="white"),
                ft.Container(height=1, bgcolor="white10"),
                input_valor,
                texto_consumo,
                ft.Container(height=20),
                linha_botoes,
                ft.Container(height=20),
                # AJUSTE: Simplificado o voltar para não causar conflito de controles
                st.botao_texto("Interromper e Sair", lambda _: voltar_menu())
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=15
        )
    )
