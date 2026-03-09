import flet as ft
import database as db
import leitor_ocr  # Importa o módulo da câmera

COR_PRIMARIA = "blue"
COR_ALERTA = "orange"


def montar_tela(page, voltar_menu):
    # 1. BUSCA A PRÓXIMA UNIDADE NO BANCO
    unidade = db.buscar_proximo_pendente()

    # 2. TELA DE CONCLUSÃO
    if not unidade:
        return ft.Container(
            expand=True, bgcolor="#1A1C1E", alignment=ft.Alignment(0, 0),
            content=ft.Column([
                ft.Icon(ft.Icons.CHECK_CIRCLE, color="green", size=80),
                ft.Text("Todas as medições concluídas!",
                        size=24, weight="bold", color="white"),
                ft.ElevatedButton("Voltar ao Menu",
                                  on_click=lambda _: voltar_menu())
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )

    # MAPEAMENTO DE DADOS
    id_db, nome_unidade, leitura_anterior = unidade[0], unidade[1], unidade[2]

    # --- FUNÇÕES DE LÓGICA (Dentro do montar_tela) ---

    def calcular_ao_digitar(e):
        try:
            input_valor.error_text = ""
            if input_valor.value:
                val_limpo = input_valor.value.replace(",", ".")
                atual = float(val_limpo)
                consumo = atual - leitura_anterior
                texto_consumo.value = f"Consumo: {consumo:.2f} m³"
                texto_consumo.color = COR_ALERTA if consumo > 20 or consumo < 0 else COR_PRIMARIA
            else:
                texto_consumo.value = "Consumo: 0.00 m³"
        except ValueError:
            texto_consumo.value = "Consumo: ---"
        page.update()

    def abrir_camera_ocr(e):
        leitura = leitor_ocr.capturar_e_ler_hidrometro()
        if leitura:
            input_valor.value = leitura
            calcular_ao_digitar(None)  # Atualiza o cálculo automaticamente
            page.update()

    # --- CRIAÇÃO DOS COMPONENTES ---

    texto_consumo = ft.Text("Consumo: 0.00 m³", size=18,
                            color=COR_PRIMARIA, weight="bold")

    input_valor = ft.TextField(
        label="Leitura Atual (m³)",
        keyboard_type=ft.KeyboardType.NUMBER,
        autofocus=True,
        max_length=9,
        color="white",
        input_filter=ft.InputFilter(
            allow=True, regex_string=r"^[0-9]*[.,]?[0-9]*$", replacement_string=""),
        on_change=calcular_ao_digitar,
        on_submit=lambda _: salvar_leitura(None)
    )

    # AGORA A LINHA DA CÂMERA FUNCIONA PORQUE input_valor JÁ EXISTE
    linha_input_ocr = ft.Row([
        input_valor,
        ft.IconButton(
            icon=ft.Icons.CAMERA_ALT,
            icon_color="blue",
            on_click=abrir_camera_ocr,
            tooltip="Ler com a câmera"
        )
    ], alignment=ft.MainAxisAlignment.CENTER)

    def salvar_leitura(e):
        if not input_valor.value:
            abrir_alerta_pular()
        else:
            try:
                valor = float(input_valor.value.strip().replace(",", "."))
                db.registrar_leitura(id_db, valor)
                voltar_menu(recarregar_medicao=True)
            except ValueError:
                input_valor.error_text = "Número inválido"
                page.update()

    def abrir_alerta_pular():
        def confirmar_pulo(e):
            dlg.open = False
            db.registrar_leitura(id_db, 0.0, status="pulado")
            page.update()
            voltar_menu(recarregar_medicao=True)

        dlg = ft.AlertDialog(
            title=ft.Text("Pular Unidade?"),
            content=ft.Text(f"Deseja pular a unidade {nome_unidade}?"),
            actions=[
                ft.TextButton("Sim, Pular", on_click=confirmar_pulo),
                ft.TextButton("Cancelar", on_click=lambda _: (
                    setattr(dlg, "open", False), page.update()))
            ]
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    # LAYOUT FINAL (Usamos linha_input_ocr em vez de apenas input_valor)
    # LAYOUT FINAL
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
                
                linha_input_ocr,  # Linha com o campo e o ícone da câmera
                texto_consumo,
                
                ft.Container(height=20),
                
                # BOTÕES DE AÇÃO
                ft.Row([
                    # Botão Principal: SALVAR
                    ft.FilledButton(
                        "SALVAR LEITURA",
                        icon=ft.Icons.SAVE,
                        on_click=salvar_leitura,
                        width=200
                    ),
                    # Botão para Pular
                    ft.IconButton(
                        icon=ft.Icons.SKIP_NEXT, 
                        icon_color="orange",
                        on_click=lambda _: abrir_alerta_pular(),
                        tooltip="Pular esta unidade"
                    ),
                ], alignment=ft.MainAxisAlignment.CENTER),
                
                ft.TextButton(
                    "Sair da Medição",
                    on_click=lambda _: voltar_menu()
                )
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20
        )
    )
