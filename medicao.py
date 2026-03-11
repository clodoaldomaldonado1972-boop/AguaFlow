import flet as ft
import database as db
import camera_utils
import asyncio

COR_PRIMARIA = "blue"
COR_ALERTA = "orange"


async def montar_tela(page: ft.Page, voltar_menu):
    # Variável de controle para evitar cliques duplos e erros de ID
    processando = False

    # --- LIMPEZA DE SEGURANÇA NA ENTRADA ---
    page.overlay.clear()
    page.update()

    unidade = db.buscar_proximo_pendente()

    # 1. TELA DE CONCLUSÃO
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

    # 2. DADOS DA UNIDADE (Lógica de cima para baixo conforme definido)
    id_db, nome_unidade, leitura_anterior = unidade[0], unidade[1], unidade[2]

    texto_consumo = ft.Text("Consumo: 0.00 m³", size=18,
                            color=COR_PRIMARIA, weight="bold")

    def calcular_ao_digitar(e):
        try:
            input_valor.error_text = None
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

    input_valor = ft.TextField(
        label="Leitura Atual (m³)",
        keyboard_type=ft.KeyboardType.NUMBER,
        width=250, color="white",
        on_change=calcular_ao_digitar,
    )

    # 3. CÂMERA E OCR (Ajustado para o novo camera_utils)
    async def ao_concluir_leitura_camera(id_qr, valor_ocr):
        if id_qr and str(id_qr).strip() != str(nome_unidade).strip():
            input_valor.error_text = f"Aviso: QR Code ({id_qr}) incorreto!"
        if valor_ocr:
            input_valor.value = str(valor_ocr).strip()
            calcular_ao_digitar(None)
        page.update()

    seletor_camera = await camera_utils.inicializar_camera(page, ao_concluir_leitura_camera)

    async def acionar_camera(e):
        await seletor_camera.pick_files(allow_multiple=False, file_type=ft.FilePickerFileType.IMAGE)

    # 4. PERSISTÊNCIA E NAVEGAÇÃO SEGURA
    async def salvar_leitura(e):
        nonlocal processando
        if processando:
            return

        if not input_valor.value:
            await abrir_alerta_pular(None)
        else:
            try:
                processando = True
                valor = float(input_valor.value.strip().replace(",", "."))
                db.registrar_leitura(id_db, valor)

                # Limpeza antes de sair
                page.overlay.clear()
                await voltar_menu(recarregar_medicao=True)
            except Exception as ex:
                processando = False
                input_valor.error_text = "Número inválido"
                page.update()

    async def abrir_alerta_pular(e):
        async def confirmar_pulo(ev):
            nonlocal processando
            if processando:
                return
            processando = True

            dlg.open = False
            db.registrar_leitura(id_db, 0.0, status="pulado")
            page.overlay.remove(dlg)
            page.update()

            await asyncio.sleep(0.1)
            await voltar_menu(recarregar_medicao=True)

        dlg = ft.AlertDialog(
            title=ft.Text("Pular Unidade?"),
            content=ft.Text("Deseja registrar esta unidade como 'pulada'?"),
            actions=[
                ft.TextButton("Sim", on_click=confirmar_pulo),
                ft.TextButton("Não", on_click=lambda _: (
                    setattr(dlg, "open", False), page.update()))
            ]
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    # 5. INTERFACE FINAL
    return ft.Container(
        expand=True, bgcolor="#1A1C1E", padding=30,
        content=ft.Column(
            controls=[
                ft.Text(f"Unidade: {nome_unidade}",
                        size=28, weight="bold", color="blue"),
                ft.Text(f"Anterior: {leitura_anterior:.2f} m³",
                        size=18, color="white70"),
                ft.Divider(color="white10"),
                ft.Row([input_valor, ft.IconButton(ft.Icons.CAMERA_ALT, icon_color="blue",
                       on_click=acionar_camera)], alignment=ft.MainAxisAlignment.CENTER),
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
