import flet as ft
import database as db
import estilos as st  # Importando o módulo de estilos

def montar_tela(page, voltar_menu):
    """
    Constrói a interface de medição modularizada.
    """
    
    # 1. BUSCA DE DADOS
    unidade = db.buscar_proximo_pendente()
    
    # 2. TELA DE CONCLUSÃO
    if not unidade:
        return ft.Container(
            content=ft.Column([
                ft.Icon("check_circle", color=st.COR_SUCESSO, size=60),
                ft.Text("Medição Concluída!", size=20, weight="bold"),
                st.botao_salvar("Voltar ao Menu", lambda _: (page.controls.clear(), voltar_menu(), page.update()))
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=50
        )

    # 3. MAPEAMENTO DE DADOS DA UNIDADE
    id_db, nome_unidade, leitura_anterior = unidade[0], unidade[1], unidade[2]
    texto_consumo = ft.Text("Consumo: 0.00 m³", size=18, color=st.COR_PRIMARIA, weight="bold")
    
    def calcular_ao_digitar(e):
        """Lógica de cálculo de consumo em tempo real"""
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
        max_length=7,
        input_filter=ft.InputFilter(allow=True, regex_string=r"^[0-9,.]*$", replacement_string=""),
        on_change=calcular_ao_digitar,
        on_submit=lambda _: salvar_leitura(None)
    )

    # 5. LÓGICA DE SALVAMENTO E PULO
    def salvar_leitura(e):
        if not input_valor.value:
            abrir_alerta_pular()
        else:
            try:
                valor = float(input_valor.value.replace(",", "."))
                db.registrar_leitura(id_db, valor)
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
            actions=[
                ft.TextButton("Sim, Pular", on_click=confirmar_pulo),
                ft.TextButton("Cancelar", on_click=lambda _: (setattr(dlg, "open", False), page.update()))
            ]
        )
        page.dialog = dlg
        dlg.open = True
        page.update()

    # 6. MONTAGEM DA LINHA DE BOTÕES (Ação Principal)
    linha_botoes = ft.Row(
        controls=[
            st.botao_salvar("SALVAR", salvar_leitura),
            ft.IconButton(
                icon="skip_next", 
                icon_color=st.COR_ALERTA, 
                on_click=lambda _: abrir_alerta_pular(),
                tooltip="Pular Unidade"
            ),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
    )
    
    # 7. RETORNO DO LAYOUT
    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Text(f"Unidade: {nome_unidade}", size=st.FONTE_TITULO, weight="bold", color=st.COR_PRIMARIA),
                ft.Text(f"Anterior: {leitura_anterior:.2f} m³", size=st.FONTE_LABEL, color=st.COR_TEXTO_SEC),
                ft.Divider(),
                input_valor,
                texto_consumo,
                ft.Container(height=20), 
                linha_botoes,            
                ft.Container(height=20), 
                st.botao_texto("Interromper e Sair", lambda _: (page.controls.clear(), voltar_menu(), page.update()))
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=15,
            tight=True,
        ),
        # ESTAS LINHAS ABAIXO SÃO AS QUE RESOLVEM A MANCHA BRANCA:
        expand=True,
        bgcolor=ft.colors.BACKGROUND, # Força o fundo a ser o do sistema (escuro)
        padding=30,
        alignment=ft.alignment.top_center,
    )