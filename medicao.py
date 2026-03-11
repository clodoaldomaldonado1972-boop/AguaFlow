import flet as ft
import database as db
import camera_utils
import asyncio

# Configurações de cores padrão para manter a identidade visual do app
COR_PRIMARIA = "blue"
COR_ALERTA = "orange"


async def montar_tela(page: ft.Page, voltar_menu):
    """
    Módulo de interface para a medição de hidrômetros.
    Gerencia a lógica de sequência de andares e captura de dados via OCR.
    """

    # Trava de segurança para evitar que múltiplos cliques gerem erros de ID no Flet
    processando = False

    # --- LIMPEZA DE SEGURANÇA ---
    # Garante que diálogos ou seletores de arquivos de unidades anteriores sejam removidos
    page.overlay.clear()
    page.update()

    # Consulta o Banco de Dados (Módulo database.py) para trazer a próxima unidade na fila
    unidade = db.buscar_proximo_pendente()

    # 1. TELA DE CONCLUSÃO (Caso não haja mais pendências no SQLite)
    if not unidade:
        async def finalizar(e):
            await voltar_menu()

        return ft.Container(
            expand=True, bgcolor="#1A1C1E", alignment=ft.Alignment(0, 0),
            content=ft.Column([
                ft.Icon(ft.Icons.CHECK_CIRCLE, color="green", size=80),
                ft.Text("Todas as medições concluídas!",
                        size=24, color="white"),
                ft.ElevatedButton("Voltar ao Menu", on_click=finalizar)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )

    # 2. MAPEAMENTO DE DADOS DA UNIDADE ATUAL
    id_db, nome_unidade, leitura_anterior = unidade[0], unidade[1], unidade[2]

    texto_consumo = ft.Text("Consumo: 0.00 m³", size=18,
                            color=COR_PRIMARIA, weight="bold")

    def calcular_ao_digitar(e):
        """Lógica em tempo real para cálculo de consumo e alerta de anomalias."""
        try:
            input_valor.error_text = None
            if input_valor.value:
                val_limpo = input_valor.value.replace(",", ".")
                atual = float(val_limpo)
                consumo = atual - leitura_anterior
                texto_consumo.value = f"Consumo: {consumo:.2f} m³"

                # Alerta visual se o consumo for negativo ou muito alto (>20m³)
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

    # --- 3. LÓGICA DE INTELIGÊNCIA E PREVENÇÃO DE ERROS ---

    async def abrir_alerta_esquecimento(nome_esquecido):
        """Dialogo que impede o avanço se um andar superior foi pulado."""
        async def seguir(e):
            # Registra '0.0' no banco para a unidade esquecida e mantém o fluxo atual
            db.registrar_leitura_automatica_zero(nome_esquecido)
            dlg_esquecimento.open = False
            page.update()

        async def voltar_atras(e):
            # Apenas fecha o alerta para o operador decidir se volta fisicamente ao andar
            dlg_esquecimento.open = False
            page.update()

        dlg_esquecimento = ft.AlertDialog(
            modal=True,
            title=ft.Text("⚠️ Apto Esquecido!"),
            content=ft.Text(
                f"A unidade {nome_esquecido} (andar superior) ficou sem leitura.\n\nDeseja registrar ZERO e seguir?"),
            actions=[
                ft.TextButton("Registrar 0 e Seguir", on_click=seguir),
                ft.TextButton("Voltar", on_click=voltar_atras),
            ]
        )
        page.overlay.append(dlg_esquecimento)
        dlg_esquecimento.open = True
        page.update()

    async def verificar_sequencia():
        """Verifica no DB se o operador pulou algum apartamento do andar de cima."""
        som_alerta = page.session.get("som_alerta")
        unidade_esquecida = db.verificar_esquecimento_superior(id_db)

        if unidade_esquecida:
            if som_alerta:
                som_alerta.play()  # Dispara o Bipe Sonoro (Módulo audio_utils)
            await abrir_alerta_esquecimento(unidade_esquecida)

    # --- 4. CÂMERA E OCR (Modularizado via camera_utils.py) ---

    async def ao_concluir_leitura_camera(id_qr, valor_ocr):
        """Callback executado após o processamento da imagem pelo módulo de OCR."""
        if id_qr and str(id_qr).strip() != str(nome_unidade).strip():
            input_valor.error_text = f"Aviso: QR Code ({id_qr}) não confere!"
        if valor_ocr:
            input_valor.value = str(valor_ocr).strip()
            calcular_ao_digitar(None)
        page.update()

    # Inicializa o FilePicker para captura da foto
    seletor_camera = await camera_utils.inicializar_camera(page, ao_concluir_leitura_camera)

    async def acionar_camera(e):
        """Ação do botão de câmera: abre o seletor de arquivos do sistema."""
        await seletor_camera.pick_files(allow_multiple=False, file_type=ft.FilePickerFileType.IMAGE)

    # --- 5. PERSISTÊNCIA DOS DADOS ---

    async def salvar_leitura(e):
        nonlocal processando
        if processando:
            return  # Bloqueia duplo clique

        if not input_valor.value:
            await abrir_alerta_pular(None)
        else:
            try:
                processando = True
                valor = float(input_valor.value.strip().replace(",", "."))

                # Envia o dado para o módulo de banco de dados
                db.registrar_leitura(id_db, valor)

                # Gatilho para verificação de conclusão total
                if db.total_pendentes() == 0:
                    print("🏁 Fluxo encerrado. Pronto para gerar PDF.")

                page.overlay.clear()
                # Recarrega a tela para buscar a PRÓXIMA unidade da fila
                await voltar_menu(recarregar_medicao=True)
            except Exception:
                processando = False
                input_valor.error_text = "Valor inválido"
                page.update()

    async def abrir_alerta_pular(e):
        """Alerta para quando o operador decide pular a unidade manualmente."""
        async def confirmar_pulo(ev):
            nonlocal processando
            if processando:
                return
            processando = True
            dlg_pulo.open = False
            db.registrar_leitura(id_db, 0.0, status="pulado")
            page.overlay.remove(dlg_pulo)
            page.update()
            await asyncio.sleep(0.1)
            await voltar_menu(recarregar_medicao=True)

        dlg_pulo = ft.AlertDialog(
            title=ft.Text("Pular Unidade?"),
            content=ft.Text("Deseja marcar como pulada?"),
            actions=[
                ft.TextButton("Sim", on_click=confirmar_pulo),
                ft.TextButton("Não", on_click=lambda _: (
                    setattr(dlg_pulo, "open", False), page.update()))
            ]
        )
        page.overlay.append(dlg_pulo)
        dlg_pulo.open = True
        page.update()

    # --- EXECUÇÃO AO CARREGAR A TELA ---
    # Verifica esquecimentos no andar de cima antes de liberar a interface
    await verificar_sequencia()

    # 6. CONSTRUÇÃO VISUAL (Interface Mobile)
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
                    ft.IconButton(ft.Icons.CAMERA_ALT,
                                  icon_color="blue", on_click=acionar_camera)
                ], alignment=ft.MainAxisAlignment.CENTER),
                texto_consumo,
                ft.Row([
                    ft.FilledButton("SALVAR", icon=ft.Icons.SAVE,
                                    on_click=salvar_leitura, width=150),
                    ft.IconButton(icon=ft.Icons.SKIP_NEXT,
                                  on_click=abrir_alerta_pular)
                ], alignment=ft.MainAxisAlignment.CENTER),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20
        )
    )
