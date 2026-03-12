import flet as ft
import database as db
import camera_utils
import asyncio

# Constantes para manter o padrão visual do Vivere Prudente
COR_PRIMARIA = "blue"
COR_ALERTA = "orange"


async def montar_tela(page: ft.Page, voltar_menu):
    """
    Constrói a interface de leitura e gerencia a lógica de negócio.
    """
    processando = False  # Trava para evitar cliques duplos no botão Salvar

    # Limpa a tela anterior para evitar sobreposição de elementos invisíveis (modais/seletores)
    page.overlay.clear()
    await page.update_async()

    # Busca no SQLite qual é o próximo hidrômetro na sequência (do topo para baixo)
    unidade = db.buscar_proximo_pendente()

    # Caso todas as unidades tenham sido lidas
    if not unidade:
        return ft.Container(
            expand=True, bgcolor="#1A1C1E", alignment=ft.Alignment(0, 0),
            content=ft.Column([
                ft.Icon(ft.icons.CHECK_CIRCLE, color="green", size=80),
                ft.Text("Todas as medições concluídas!",
                        size=24, color="white"),
                ft.ElevatedButton("Voltar ao Menu",
                                  on_click=lambda _: voltar_menu())
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )

    # Desempacota os dados vindos do banco
    id_db, nome_unidade, leitura_anterior = unidade[0], unidade[1], unidade[2]

    # Elemento visual que mostrará o consumo calculado em tempo real
    texto_consumo = ft.Text("Consumo: 0.00 m³", size=18,
                            color=COR_PRIMARIA, weight="bold")

    def calcular_ao_digitar(e):
        """Calcula a diferença entre leitura atual e anterior automaticamente."""
        try:
            input_valor.error_text = None
            if input_valor.value:
                val_limpo = input_valor.value.replace(",", ".")
                atual = float(val_limpo)
                consumo = atual - leitura_anterior
                texto_consumo.value = f"Consumo: {consumo:.2f} m³"
                # Alerta visual se o consumo for negativo ou muito alto (vazamento?)
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

    async def ao_concluir_ocr(id_qr, valor_ocr):
        """
        Função chamada pelo camera_utils quando a foto termina de ser processada.
        """
        # Validação: O QR Code lido é da unidade correta?
        if id_qr and str(id_qr).strip() != str(nome_unidade).strip():
            input_valor.error_text = f"Aviso: QR Code ({id_qr}) não confere!"

        # Preenche o campo de texto com o valor extraído pelo OCR
        if valor_ocr:
            input_valor.value = str(valor_ocr).strip()
            calcular_ao_digitar(None)
        await page.update_async()

    # Inicializa o FilePicker usando o módulo externo
    async def acionar_camera(e):
        nonlocal seletor_camera

        # 1. Verificação de Segurança: Se for None, tenta inicializar de novo
        if seletor_camera is None:
            print("Seletor era None, reinicializando...")
            seletor_camera = await camera_utils.inicializar_camera(page, ao_concluir_ocr)

        # 2. Garante o vínculo com a página (evita o AssertionError anterior)
        if seletor_camera not in page.overlay:
            page.overlay.append(seletor_camera)

        seletor_camera.page = page
        await page.update_async()

        # 3. Executa o seletor com tratamento de erro para o 'NoneType'
        try:
            if seletor_camera:
                await seletor_camera.pick_files(
                    allow_multiple=False,
                    file_type=ft.FilePickerFileType.IMAGE
                )
            else:
                print("Falha crítica: Não foi possível criar o seletor de arquivos.")
        except Exception as ex:
            print(f"Erro ao abrir câmera: {ex}")

    # Retorna o layout da tela
    return ft.Container(
        expand=True, bgcolor="#1A1C1E", padding=30,
        content=ft.Column(
            controls=[
                ft.Text(f"Unidade: {nome_unidade}",
                        size=28, weight="bold", color="blue"),
                ft.Text(f"Anterior: {leitura_anterior:.2f} m³",
                        size=18, color="white70"),
                ft.Divider(color="white10"),
                ft.Row([
                    input_valor,
                    ft.IconButton(ft.icons.CAMERA_ALT,
                                  icon_color="blue", on_click=acionar_camera)
                ], alignment=ft.MainAxisAlignment.CENTER),
                texto_consumo,
                ft.Row([
                    ft.FilledButton("SALVAR", icon=ft.icons.SAVE,
                                    on_click=lambda _: None, width=150),
                    ft.IconButton(icon=ft.icons.SKIP_NEXT,
                                  on_click=lambda _: None)
                ], alignment=ft.MainAxisAlignment.CENTER),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20
        )
    )
