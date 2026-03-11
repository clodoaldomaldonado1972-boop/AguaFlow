import flet as ft
import database as db
import processamento  # Módulo de visão computacional (OpenCV/Tesseract)

COR_PRIMARIA = "blue"
COR_ALERTA = "orange"


def montar_tela(page, voltar_menu):
    # 1. BUSCA DE DADOS
    unidade = db.buscar_proximo_pendente()

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

    id_db, nome_unidade, leitura_anterior = unidade[0], unidade[1], unidade[2]

    # --- 2. COMPONENTES VISUAIS ---
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

    # --- 3. LÓGICA DE CAPTURA (VERSÃO RESILIENTE) ---
    def ao_selecionar_arquivo(e: ft.FilePickerResultEvent):
        if e.files:
            caminho_foto = e.files[0].path
            id_qr, valor_ocr = processamento.processar_foto_hidrometro(
                caminho_foto)

            if id_qr and str(id_qr).strip() != str(nome_unidade).strip():
                input_valor.error_text = f"Aviso: QR Code ({id_qr}) incorreto!"

            if valor_ocr:
                input_valor.value = str(valor_ocr).strip()
                calcular_ao_digitar(None)
            page.update()

    # LIMPEZA CRÍTICA: Remove lixo de memórias anteriores para evitar "Unknown Control"
    for control in page.overlay[:]:
        if isinstance(control, ft.FilePicker):
            page.overlay.remove(control)

    # 1. Cria o objeto vazio primeiro para evitar o TypeError
    seletor_foto = ft.FilePicker()
    
    # 2. Atribui a função de resposta manualmente
    seletor_foto.on_result = ao_selecionar_arquivo
    
    # 3. Limpeza de segurança: remove seletores antigos para evitar erros no celular
    for control in page.overlay[:]:
        if isinstance(control, ft.FilePicker):
            page.overlay.remove(control)
            
    # 4. Adiciona o novo seletor ao overlay
    page.overlay.append(seletor_foto)
    
    # 5. Sincroniza com o navegador antes do retorno da tela
    page.update()

    # --- 4. SALVAMENTO E NAVEGAÇÃO ---
    def salvar_leitura(e):
        if not input_valor.value:
            abrir_alerta_pular()
        else:
            try:
                valor = float(input_valor.value.strip().replace(",", "."))
                db.registrar_leitura(id_db, valor)
                voltar_menu(recarregar_medicao=True)
            except:
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
            actions=[ft.TextButton("Sim", on_click=confirmar_pulo)]
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    # --- 5. RETORNO DA UI ---
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
