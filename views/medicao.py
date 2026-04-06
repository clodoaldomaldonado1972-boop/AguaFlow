import flet as ft
from database.database import Database
from . import camera_utils


def montar_tela_medicao(page: ft.Page):
    # Recupera o filtro de leitura (padrão Água)
    filtro = getattr(page, "filtro_leitura", "Água")

    # Busca unidade pendente no banco
    registro = Database.buscar_proximo_pendente(filtro)

    # SE TERMINAR AS LEITURAS: Mostra mensagem de sucesso
    if not registro:
        return ft.View(
            route="/medicao",
            bgcolor="#121417",
            vertical_alignment="center",
            horizontal_alignment="center",
            controls=[
                ft.Icon("check_circle", color="green", size=80),
                ft.Text("Leituras Concluídas!", size=28, weight="bold"),
                ft.Text(f"Todas as medições de {filtro} foram registadas."),
                ft.ElevatedButton("VOLTAR AO MENU", icon="home",
                                  on_click=lambda _: page.go("/menu"))
            ]
        )

    _, unidade, tipo = registro
    unidade_anterior = getattr(page, "ultima_unidade_salva", None)

    # Label para mostrar a unidade atual (agora editável para permitir atualização)
    lbl_unidade = ft.TextField(
        value=f"Unidade: {unidade}",
        read_only=True,
        text_size=32,
        border=ft.InputBorder.NONE,
        bgcolor=ft.Colors.TRANSPARENT,
        text_align="center"
    )

    # Label para mostrar o tipo de medição
    lbl_tipo = ft.Text(f"Medindo agora: {tipo}", color="blue")
    txt_leitura = ft.TextField(
        label=f"Valor para {tipo}",
        keyboard_type=ft.KeyboardType.NUMBER,
        max_length=7,
        width=300,
        text_align="center",
        autofocus=True,
        read_only=True  # Inicialmente read-only, só manual se OCR falhar
    )

    # Progress ring para OCR
    progress_ring = ft.ProgressRing(visible=False)

    # Botão de captura
    btn_capturar = ft.ElevatedButton(
        "CAPTURAR FOTO", icon="camera", width=300, disabled=False)

    # Botão de teclado para entrada manual
    btn_teclado = ft.IconButton(
        icon="edit",
        tooltip="Inserir manualmente",
        icon_size=24
    )

    # Diálogo de confirmação
    dlg_confirmacao = ft.AlertDialog()

    # Diálogo para alerta de unidade pulada
    dlg_alerta_pulada = ft.AlertDialog()

    def exibir_alerta_pulada(mensagem):
        """Exibe alerta quando uma unidade foi pulada"""
        dlg_alerta_pulada.title = ft.Text("Aviso")
        dlg_alerta_pulada.content = ft.Text(mensagem)
        dlg_alerta_pulada.actions = [
            ft.TextButton(
                "Cancelar", on_click=lambda _: fechar_dialogo_pulada()),
            ft.TextButton(
                "Continuar", on_click=lambda _: fechar_dialogo_pulada())
        ]
        page.dialog = dlg_alerta_pulada
        dlg_alerta_pulada.open = True
        page.update()

    def fechar_dialogo_pulada():
        dlg_alerta_pulada.open = False
        page.update()

    def exibir_confirmacao(valor_capturado, pode_inserir_manual=False):
        """Exibe diálogo de confirmação após OCR"""
        def confirmar_e_salvar(e):
            dlg_confirmacao.open = False
            if txt_leitura.value:
                res = Database.registrar_leitura(
                    unidade, txt_leitura.value, tipo)
                if res.get('sucesso'):
                    # Salva a unidade atual como última salva
                    page.ultima_unidade_salva = unidade
                    # Ir para próxima medição
                    page.go("/medicao")
            page.update()

        def refazer_leitura(e):
            dlg_confirmacao.open = False
            txt_leitura.value = ""
            txt_leitura.read_only = not pode_inserir_manual
            page.update()

        dlg_confirmacao.title = ft.Text("Confirmar Leitura")
        dlg_confirmacao.content = ft.Column([
            ft.Text(f"Unidade: {unidade}"),
            ft.Text(f"Tipo: {tipo}"),
            ft.Text(f"Valor lido: {valor_capturado}",
                    weight="bold", color="blue"),
            ft.Text("Deseja confirmar e salvar?", size=14)
        ])

        actions = [
            ft.TextButton("Refazer", on_click=refazer_leitura),
            ft.TextButton("Confirmar e Salvar", on_click=confirmar_e_salvar)
        ]
        dlg_confirmacao.actions = actions
        page.dialog = dlg_confirmacao
        dlg_confirmacao.open = True
        page.update()

    def salvar_leitura_click(e):
        """Salva leitura manual se foi inserida"""
        nonlocal unidade, tipo, filtro  # Permitir modificar as variáveis locais

        if txt_leitura.value:
            print(
                f"\n[GRAVAÇÃO] Unidade: {unidade} | Valor: {txt_leitura.value}")

            res = Database.registrar_leitura(unidade, txt_leitura.value, tipo)

            if res.get('sucesso'):
                # Feedback visual de sucesso
                page.snack_bar = ft.SnackBar(
                    ft.Text(
                        f"Leitura do {unidade} salva com sucesso!", color=ft.Colors.GREEN),
                    duration=3000
                )
                page.snack_bar.open = True

                page.ultima_unidade_salva = unidade

                # Limpar o campo após gravação
                txt_leitura.value = ""

                # Buscar próxima unidade pendente
                prox_registro = Database.buscar_proximo_pendente(filtro)

                if prox_registro:
                    # Atualizar a unidade atual e continuar na mesma tela
                    _, nova_unidade, novo_tipo = prox_registro
                    unidade = nova_unidade  # Atualizar variável global
                    tipo = novo_tipo  # Atualizar variável global
                    lbl_unidade.value = f"Unidade: {unidade}"
                    lbl_tipo.value = f"Medindo agora: {tipo}"
                    # Também atualizar o tipo se necessário
                    page.update()
                else:
                    # Todas as leituras concluídas - mostrar SnackBar e voltar ao menu
                    page.snack_bar = ft.SnackBar(
                        ft.Text("Bloco concluído! Retornando ao menu...",
                                color=ft.Colors.BLUE),
                        duration=2000
                    )
                    page.snack_bar.open = True
                    # Aguardar 2 segundos e voltar ao menu
                    import asyncio

                    async def voltar_menu():
                        await asyncio.sleep(2)
                        page.go('/menu')
                    asyncio.create_task(voltar_menu())
            else:
                # Feedback visual de erro
                page.snack_bar = ft.SnackBar(
                    ft.Text(
                        f"Erro ao salvar leitura: {res.get('erro', 'Erro desconhecido')}", color=ft.Colors.RED),
                    duration=4000
                )
                page.snack_bar.open = True

        page.update()

    async def habilitar_entrada_manual(e):
        """Habilita o campo de entrada manual imediatamente"""
        txt_leitura.read_only = False
        await txt_leitura.focus()
        page.update()

    async def capturar_click(e):
        # Desabilitar botão e mostrar progress
        btn_capturar.disabled = True
        progress_ring.visible = True
        txt_leitura.value = ""
        page.update()

        try:
            # Função callback para quando OCR terminar
            def ao_concluir_ocr(resultado):
                # Esconder progress
                progress_ring.visible = False
                btn_capturar.disabled = False

                status = resultado.get('status', 'Erro')
                valor = resultado.get('valor')
                pode_inserir_manual = resultado.get(
                    'pode_inserir_manual', False)

                if valor:
                    # OCR teve sucesso
                    txt_leitura.value = valor
                    txt_leitura.read_only = True
                    exibir_confirmacao(valor, pode_inserir_manual=False)
                elif pode_inserir_manual:
                    # OCR falhou, permitir entrada manual
                    txt_leitura.read_only = False
                    page.run_task(lambda: txt_leitura.focus())
                    page.update()
                    page.snack_bar = ft.SnackBar(
                        ft.Text(
                            "OCR não detectou números. Por favor, insira manualmente."),
                        duration=3000
                    )
                    page.snack_bar.open = True
                else:
                    # Erro total
                    page.snack_bar = ft.SnackBar(
                        ft.Text(f"Erro ao processar imagem: {status}"),
                        duration=3000
                    )
                    page.snack_bar.open = True

                page.update()

            # Inicializar câmera
            await camera_utils.inicializar_camera(page, ao_concluir_ocr)

        except Exception as erro:
            # Tratamento de erro de câmera não disponível
            print(f"Erro ao acessar câmera: {erro}")
            progress_ring.visible = False
            btn_capturar.disabled = False

            # Habilitar entrada manual automaticamente
            await habilitar_entrada_manual(None)

            page.snack_bar = ft.SnackBar(
                ft.Text("Câmera não detectada. Digite o valor manualmente."),
                duration=4000
            )
            page.snack_bar.open = True
            page.update()

    # Atribuir os handlers
    btn_capturar.on_click = capturar_click
    btn_teclado.on_click = habilitar_entrada_manual

    return ft.View(
        route="/medicao",
        bgcolor="#121417",
        controls=[
            ft.AppBar(
                title=ft.Text(f"Medição {filtro}"),
                leading=ft.IconButton(
                    icon="arrow_back", on_click=lambda _: page.go("/menu"))
            ),
            ft.Container(
                padding=20,
                expand=True,
                content=ft.Column([
                    lbl_unidade,
                    lbl_tipo,
                    progress_ring,
                    txt_leitura,
                    ft.Row([
                        btn_capturar,
                        btn_teclado
                    ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
                    ft.ElevatedButton(
                        "SALVAR MANUAL", icon="save", width=300, on_click=salvar_leitura_click),
                    ft.TextButton(
                        "Voltar", on_click=lambda _: page.go("/menu"), width=300)
                ], horizontal_alignment="center", spacing=20, scroll=ft.ScrollMode.AUTO)
            )
        ]
    )


def extrair_andar(unidade_str):
    """Extrai número do andar da string 'Apto XYZT'"""
    try:
        # Formato: "Apto 1A2" onde 1=andar, A=bloco, 2=pos
        num_str = unidade_str.replace("Apto ", "").strip()
        if len(num_str) >= 2:
            return int(num_str[0])  # Primeiro dígito é o andar
    except:
        pass
    return 0


def numero_unidade(unidade_str):
    """Extrai número para comparação de sequência"""
    try:
        num_str = unidade_str.replace("Apto ", "").strip()
        if len(num_str) >= 2:
            andar = int(num_str[:-1])
            pos = int(num_str[-1])
            return andar * 10 + pos
    except:
        pass
    return 0
