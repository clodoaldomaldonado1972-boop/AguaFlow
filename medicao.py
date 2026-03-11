import flet as ft
import database as db
import processamento  # Módulo de visão computacional (OpenCV/Tesseract)

# Definição de identidade visual do AguaFlow
COR_PRIMARIA = "blue"
COR_ALERTA = "orange"


def montar_tela(page, voltar_menu):
    """
    Função principal que constrói a interface de medição.
    Recebe 'page' para controle da UI e 'voltar_menu' para navegação.
    """

    # 1. BUSCA DINÂMICA DE DADOS (Regra de Negócio: Topo para baixo)
    unidade = db.buscar_proximo_pendente()

    # 2. VALIDAÇÃO DE FLUXO: Se não houver mais unidades, encerra a rota
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

    # Desempacotamento dos dados vindos do SQLite
    id_db, nome_unidade, leitura_anterior = unidade[0], unidade[1], unidade[2]

    # --- 3. ELEMENTOS DE INTERFACE ---

    texto_consumo = ft.Text("Consumo: 0.00 m³", size=18,
                            color=COR_PRIMARIA, weight="bold")

    def calcular_ao_digitar(e):
        """Calcula em tempo real a diferença entre a leitura atual e a anterior"""
        try:
            input_valor.error_text = None
            if input_valor.value:
                # Trata vírgula como ponto para o cálculo matemático
                val_limpo = input_valor.value.replace(",", ".")
                atual = float(val_limpo)
                consumo = atual - leitura_anterior

                texto_consumo.value = f"Consumo: {consumo:.2f} m³"

                # Alerta visual para consumos atípicos (>20m³ ou negativo)
                texto_consumo.color = COR_ALERTA if consumo > 20 or consumo < 0 else COR_PRIMARIA
            else:
                texto_consumo.value = "Consumo: 0.00 m³"
        except ValueError:
            texto_consumo.value = "Consumo: ---"
        page.update()

    input_valor = ft.TextField(
        label="Leitura Atual (m³)",
        keyboard_type=ft.KeyboardType.NUMBER,
        width=250,
        color="white",
        on_change=calcular_ao_digitar,
    )

    # --- 4. LÓGICA DE VISÃO COMPUTACIONAL (OCR/QR CODE) ---

    def ao_selecionar_arquivo(e: ft.FilePickerResultEvent):
        """Processa a imagem após a captura pela câmera do celular"""
        if e.files:
            caminho_foto = e.files[0].path
            input_valor.error_text = None

            # Integração com o módulo de processamento (OpenCV)
            id_qr, valor_ocr = processamento.processar_foto_hidrometro(
                caminho_foto)

            # Validação de Segurança: Garante que o QR Code lido é da unidade correta
            if id_qr and str(id_qr).strip() != str(nome_unidade).strip():
                input_valor.error_text = f"Aviso: QR Code ({id_qr}) não bate com {nome_unidade}!"

            # Preenchimento inteligente via OCR
            if valor_ocr:
                input_valor.value = str(valor_ocr).strip()
                calcular_ao_digitar(None)

            page.update()

    # O FilePicker é um controle invisível que gerencia o acesso à câmera/arquivos
    seletor_foto = ft.FilePicker()
    seletor_foto.on_result = ao_selecionar_arquivo

    # O componente deve estar no 'overlay' para funcionar globalmente na página
    if seletor_foto not in page.overlay:
        page.overlay.append(seletor_foto)

    page.update()  # Garante que o seletor foi registrado pelo navegador/celular

    def abrir_camera(e):
        """Dispara o seletor de arquivos do sistema operacional"""
        page.run_task(seletor_foto.pick_files,
                      allow_multiple=False,
                      file_type=ft.FilePickerFileType.IMAGE)

    # Organização visual da linha de captura
    linha_input_ocr = ft.Row([
        input_valor,
        ft.IconButton(
            icon=ft.Icons.CAMERA_ALT,
            icon_color="blue",
            on_click=abrir_camera,
            tooltip="Tirar foto do hidrômetro"
        )
    ], alignment=ft.MainAxisAlignment.CENTER)

    # --- 5. PERSISTÊNCIA DE DADOS ---

    def salvar_leitura(e):
        """Valida e envia a leitura para o banco de dados SQLite"""
        if not input_valor.value:
            abrir_alerta_pular()
        else:
            try:
                # Bloqueia salvamento se houver erro crítico (exceto avisos de QR Code)
                if input_valor.error_text and "Aviso" not in input_valor.error_text:
                    page.update()
                    return

                valor = float(input_valor.value.strip().replace(",", "."))
                db.registrar_leitura(id_db, valor)

                # Retorna ao menu e força o recarregamento dos cards de progresso
                voltar_menu(recarregar_medicao=True)
            except ValueError:
                input_valor.error_text = "Número inválido"
                page.update()

    def abrir_alerta_pular():
        """Gerencia unidades que não puderam ser medidas (ex: morador ausente)"""
        def confirmar_pulo(e):
            dlg.open = False
            db.registrar_leitura(id_db, 0.0, status="pulado")
            page.update()
            voltar_menu(recarregar_medicao=True)

        dlg = ft.AlertDialog(
            title=ft.Text("Pular Unidade?"),
            content=ft.Text(f"Deseja marcar {nome_unidade} como 'pulada'?"),
            actions=[
                ft.TextButton("Sim, Pular", on_click=confirmar_pulo),
                ft.TextButton("Cancelar", on_click=lambda _: (
                    setattr(dlg, "open", False), page.update()))
            ]
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    # --- 6. RENDERIZAÇÃO FINAL (CONTAINER) ---
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
