import flet as ft
import database as db
import processamento  # Módulo de visão computacional (OpenCV/Tesseract)

# Configurações de Identidade Visual do AguaFlow
COR_PRIMARIA = "blue"
COR_ALERTA = "orange"


def montar_tela(page, voltar_menu):
    """
    Constrói a interface de medição.
    Gerencia a lógica de captura de imagem, OCR e persistência no SQLite.
    """

    # 1. FLUXO DE DADOS: Busca a próxima unidade pendente (Regra: Topo para baixo)
    unidade = db.buscar_proximo_pendente()

    # Validação de encerramento: Se não houver pendências, exibe tela de conclusão
    if not unidade:
        return ft.Container(
            expand=True, bgcolor="#1A1C1E", alignment=ft.Alignment(0, 0),
            content=ft.Column([
                ft.Icon(ft.Icons.CHECK_CIRCLE, color="green", size=80),
                ft.Text("Todas as medições concluídas!",
                        size=24, color="white"),
                ft.ElevatedButton("Voltar ao Menu",
                                  on_click=lambda _: voltar_menu())
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )

    # Extração de dados da tupla retornada pelo banco de dados
    id_db, nome_unidade, leitura_anterior = unidade[0], unidade[1], unidade[2]

    # --- 2. LÓGICA DE INTERFACE E CÁLCULOS ---
    texto_consumo = ft.Text("Consumo: 0.00 m³", size=18,
                            color=COR_PRIMARIA, weight="bold")

    def calcular_ao_digitar(e):
        """Realiza o cálculo diferencial de consumo em tempo real."""
        try:
            input_valor.error_text = None
            if input_valor.value:
                # Normalização de entrada (substitui vírgula por ponto)
                val_limpo = input_valor.value.replace(",", ".")
                atual = float(val_limpo)
                consumo = atual - leitura_anterior

                texto_consumo.value = f"Consumo: {consumo:.2f} m³"

                # Alerta visual para consumos atípicos ou erros de digitação
                texto_consumo.color = COR_ALERTA if consumo > 20 or consumo < 0 else COR_PRIMARIA
            else:
                texto_consumo.value = "Consumo: 0.00 m³"
        except ValueError:
            texto_consumo.value = "Consumo: ---"
        page.update()

    input_valor = ft.TextField(
        label="Leitura Atual (m³)",
        keyboard_type=ft.KeyboardType.NUMBER,
        width=250, color="white",
        on_change=calcular_ao_digitar,
    )

    # --- 3. GESTÃO DA CÂMERA E OCR (MÓDULO DE VISÃO) ---
    def ao_selecionar_arquivo(e: ft.FilePickerResultEvent):
        """Processa o retorno da câmera/galeria via OCR e QR Code."""
        if e.files:
            caminho_foto = e.files[0].path
            # Integração com OpenCV/Tesseract para leitura automática
            id_qr, valor_ocr = processamento.processar_foto_hidrometro(
                caminho_foto)

            # Validação de integridade: Garante que o QR Code lido pertence à unidade atual
            if id_qr and str(id_qr).strip() != str(nome_unidade).strip():
                input_valor.error_text = f"Aviso: QR Code ({id_qr}) incorreto!"

            # Preenchimento automático do campo caso o OCR tenha sucesso
            if valor_ocr:
                input_valor.value = str(valor_ocr).strip()
                calcular_ao_digitar(None)
            page.update()

    # --- 4. SOLUÇÃO DE RESILIÊNCIA MOBILE (FILEPICKER) ---
    # Limpeza de memória: Remove instâncias órfãs para evitar o erro "Unknown Control" no Android
    for control in page.overlay[:]:
        if isinstance(control, ft.FilePicker):
            page.overlay.remove(control)

    # Inicialização manual para garantir compatibilidade entre versões do Flet
    seletor_foto = ft.FilePicker()
    seletor_foto.on_result = ao_selecionar_arquivo

    # Registro do componente no overlay da página
    page.overlay.append(seletor_foto)

    # Sincronização obrigatória com o cliente (celular) antes de renderizar os botões
    page.update()

    def abrir_camera(e):
        """Aciona a interface nativa de captura de imagem."""
        seletor_foto.pick_files(
            allow_multiple=False,
            file_type=ft.FilePickerFileType.IMAGE
        )

    # Componente de linha para entrada de dados (OCR + Input)
    linha_input_ocr = ft.Row([
        input_valor,
        ft.IconButton(
            icon=ft.Icons.CAMERA_ALT,
            icon_color="blue",
            on_click=abrir_camera,
            tooltip="Tirar foto do hidrômetro"
        )
    ], alignment=ft.MainAxisAlignment.CENTER)

    # --- 5. PERSISTÊNCIA E NAVEGAÇÃO ---
    def salvar_leitura(e):
        """Valida e registra a medição no banco de dados SQLite."""
        if not input_valor.value:
            abrir_alerta_pular()
        else:
            try:
                valor = float(input_valor.value.strip().replace(",", "."))
                db.registrar_leitura(id_db, valor)
                # Retorna ao menu e dispara o recarregamento dos indicadores de progresso
                voltar_menu(recarregar_medicao=True)
            except:
                input_valor.error_text = "Número inválido"
                page.update()

    def abrir_alerta_pular():
        """Trata casos onde a medição não pode ser realizada (ex: acesso negado)."""
        def confirmar_pulo(e):
            dlg.open = False
            db.registrar_leitura(id_db, 0.0, status="pulado")
            page.update()
            voltar_menu(recarregar_medicao=True)

        dlg = ft.AlertDialog(
            title=ft.Text("Pular Unidade?"),
            actions=[ft.TextButton("Sim", on_click=confirmar_pulo)]
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    # --- 6. RENDERIZAÇÃO DA INTERFACE (CONTAINER) ---
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
                ft.Row([
                    ft.FilledButton("SALVAR", icon=ft.Icons.SAVE,
                                    on_click=salvar_leitura, width=150),
                    ft.IconButton(icon=ft.Icons.SKIP_NEXT,
                                  on_click=lambda _: abrir_alerta_pular())
                ], alignment=ft.MainAxisAlignment.CENTER),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20
        )
    )
