import flet as ft
import database as db
import camera_utils  # Mantido para compatibilidade se necessário
import asyncio


async def montar_tela(page: ft.Page, voltar_menu):
    processando = False

    # 1. Busca a próxima unidade pendente
    unidade = db.buscar_proximo_pendente()

    if not unidade:
        return ft.Container(
            expand=True, bgcolor="#1A1C1E", alignment=ft.Alignment(0, 0),
            content=ft.Column([
                ft.Icon(ft.Icons.CHECK_CIRCLE, color="green", size=80),
                ft.Text("Todas as medições concluídas!",
                        size=24, color="white"),
                ft.ElevatedButton("Voltar ao Menu", on_click=voltar_menu)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )

    id_db, nome_unidade, leitura_anterior = unidade[0], unidade[1], unidade[2]

    texto_consumo = ft.Text("Consumo: 0.00 m³", size=18,
                            color="blue", weight="bold")
    status_leitura = ft.Text("Aguardando scanner...", color="white54", size=12)

    # Função para calcular o consumo
    def calcular_ao_digitar(e):
        try:
            if input_valor.value:
                val_limpo = input_valor.value.replace(",", ".")
                consumo = float(val_limpo) - leitura_anterior
                texto_consumo.value = f"Consumo: {consumo:.2f} m³"
                texto_consumo.color = "orange" if consumo > 20 or consumo < 0 else "blue"
            page.update()
        except:
            pass

    input_valor = ft.TextField(
        label="Leitura Atual (m³)",
        keyboard_type=ft.KeyboardType.NUMBER,
        width=250, color="white",
        on_change=calcular_ao_digitar,
    )

    # --- NOVO FLUXO: SCANNER EM TEMPO REAL ---
    async def ao_escanear(e):
        """
        Explicação: Esta função é engatilhada pelo sensor de imagem.
        Ela lê o dado (QR ou Número) e joga direto no campo, sem salvar foto.
        """
        if e.data:
            input_valor.value = str(e.data)
            status_leitura.value = "Leitura capturada!"
            status_leitura.color = "green"
            calcular_ao_digitar(None)
            page.update()

    # Componente de Scanner (Não consome RAM com arquivos .jpg)
    scanner = ft.BarcodeScanner(
        on_result=ao_escanear,
    )

    # Garante que o scanner esteja no overlay
    if scanner not in page.overlay:
        page.overlay.append(scanner)

    async def acionar_scanner_vivo(e):
        status_leitura.value = "Scanner ativo..."
        status_leitura.color = "blue"
        page.update()
        # Abre a interface de câmera do sistema para leitura direta
        scanner.get_identifier()

    async def salvar_leitura(e):
        nonlocal processando
        if processando or not input_valor.value:
            input_valor.error_text = "Digite um valor"
            page.update()
            return
        try:
            processando = True
            valor = float(input_valor.value.replace(",", "."))
            db.registrar_leitura(id_db, valor)
            await voltar_menu(recarregar_medicao=True)
        except Exception as ex:
            processando = False
            print(f"Erro ao salvar: {ex}")

    async def pular_unidade(e):
        await voltar_menu(recarregar_medicao=True)

    # --- INTERFACE ---
    return ft.Container(
        expand=True, bgcolor="#1A1C1E", padding=30,
        content=ft.Column(
            controls=[
                ft.Text(f"Unidade: {nome_unidade}",
                        size=28, weight="bold", color="blue"),
                ft.Divider(color="white10"),

                # BOTÃO DE SCANNER REALTIME
                ft.ElevatedButton(
                    "ABRIR SCANNER VIVO",
                    icon=ft.Icons.QR_CODE_SCANNER,
                    on_click=acionar_scanner_vivo,
                    style=ft.ButtonStyle(
                        color="white", bgcolor="blue",
                        shape=ft.RoundedRectangleBorder(radius=10)
                    ),
                    height=60, width=300
                ),

                status_leitura,
                ft.Text("OU AJUSTE MANUALMENTE:", size=14, color="white54"),
                ft.Row([input_valor], alignment="center"),
                texto_consumo,

                ft.Row([
                    ft.FilledButton("SALVAR LEITURA", icon=ft.Icons.SAVE,
                                    on_click=salvar_leitura, width=180),
                    ft.IconButton(icon=ft.Icons.SKIP_NEXT,
                                  icon_color="white54", on_click=pular_unidade)
                ], alignment="center"),
            ],
            horizontal_alignment="center", spacing=20
        )
    )
