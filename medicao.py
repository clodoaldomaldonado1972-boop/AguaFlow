import flet as ft
import database as db
import processamento  # Módulo de visão computacional

# Definição de cores padrão do sistema
COR_PRIMARIA = "blue"
COR_ALERTA = "orange"


def montar_tela(page, voltar_menu):
    # 1. BUSCA DE DADOS: Procura no banco a próxima unidade pendente
    unidade = db.buscar_proximo_pendente()

    # 2. VERIFICAÇÃO DE CONCLUSÃO
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

    # MAPEAMENTO: Extrai os dados da unidade atual
    id_db, nome_unidade, leitura_anterior = unidade[0], unidade[1], unidade[2]

    # --- LÓGICA DE CAPTURA E PROCESSAMENTO ---

    def ao_capturar_foto(e):
        """Processa a foto assim que o hardware do celular captura a imagem."""
        caminho_foto = e.path

        # Chama o cérebro visual (Modularizado)
        id_qr, valor_ocr = processamento.processar_foto_hidrometro(
            caminho_foto)

        # Validação de segurança: QR Code vs Unidade Esperada
        if id_qr and id_qr != nome_unidade:
            input_valor.error_text = f"Aviso: QR Code ({id_qr}) não bate com {nome_unidade}!"

        # Preenchimento automático via OCR
        if valor_ocr:
            input_valor.value = valor_ocr
            calcular_ao_digitar(None)

        camera_mobile.visible = False
        page.update()

    # --- COMPONENTE DE CÂMERA ---
    camera_mobile = ft.Camera(
        visible=False,
        on_update=lambda e: print("Hardware de vídeo ativado."),
        on_capture=ao_capturar_foto
    )

    if camera_mobile not in page.overlay:
        page.overlay.append(camera_mobile)

    # --- FUNÇÕES DE INTERAÇÃO ---

    def calcular_ao_digitar(e):
        """Calcula o consumo em tempo real."""
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

    def gerenciar_camera(e):
        """Ativa a câmera ou tira a foto se já estiver aberta."""
        if not camera_mobile.visible:
            camera_mobile.visible = True
        else:
            camera_mobile.capture_photo()
        page.update()

    # --- COMPONENTES VISUAIS ---

    texto_consumo = ft.Text("Consumo: 0.00 m³", size=18,
                            color=COR_PRIMARIA, weight="bold")

    input_valor = ft.TextField(
        label="Leitura Atual (m³)",
        keyboard_type=ft.KeyboardType.NUMBER,
        width=250,
        color="white",
        on_change=calcular_ao_digitar,
    )

    linha_input_ocr = ft.Row([
        input_valor,
        ft.IconButton(
            icon=ft.Icons.CAMERA_ALT,
            icon_color="blue",
            on_click=gerenciar_camera,
            tooltip="Capturar Hidrômetro"
        )
    ], alignment=ft.MainAxisAlignment.CENTER)

    def salvar_leitura(e):
        """Grava no banco e chama a próxima unidade."""
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

    return ft.Container(
        expand=True, bgcolor="#1A1C1E", padding=30,
        content=ft.Column(
            controls=[
                ft.Text(f"Unidade: {nome_unidade}",
                        size=28, weight="bold", color="blue"),
                ft.Text(f"Anterior: {leitura_anterior:.2f} m³",
                        size=18, color="white70"),
                ft.Divider(color="white10"),
                linha_input_ocr,
                texto_consumo,
                ft.Container(height=20),
                ft.Row([
                    ft.FilledButton("SALVAR LEITURA", icon=ft.Icons.SAVE,
                                    on_click=salvar_leitura, width=200),
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
