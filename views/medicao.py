import flet as ft
import asyncio
import pytz  # Para garantir o horário de Brasília
from datetime import datetime
from database.database import Database
import views.styles as st  # Importando seus estilos personalizados


def montar_tela_medicao(page: ft.Page):
    # Recupera a lista de unidades (ex: 98 unidades do Vivere)[cite: 2]
    db_lista = Database._gerar_lista_unidades()
    state = {"modo": "AGUA", "lidas_no_hall": 0}

    # Configuração de fuso horário para a coleta
    fuso_sp = pytz.timezone('America/Sao_Paulo')

    # 1. Elementos Visuais com cores em string para evitar erro de 'colors not defined'[cite: 1]
    img_icon = ft.Icon("water", color="blue", size=140)
    icon_save = ft.Icon("save", color="green", size=140, visible=False)
    lbl_modo = ft.Text("MODO: ÁGUA", color="blue", weight="bold", size=22)

    txt_unidade = ft.Dropdown(
        label="Unidade",
        options=[ft.dropdown.Option(u) for u in db_lista],
        width=320,
        value=db_lista[0] if db_lista else None,
        border_color="blue"
    )

    txt_agua = ft.TextField(
        label="Leitura Água (m³)",
        icon="water_drop",
        width=320,
        keyboard_type=ft.KeyboardType.NUMBER,
        input_filter=ft.InputFilter(
            allow=True, regex_string=r"^\d{0,5}(\.\d{0,2})?$"),
        text_align=ft.TextAlign.CENTER,
        hint_text="00000.00"
    )

    txt_gas = ft.TextField(
        label="Leitura Gás (m³)",
        icon="local_fire_department",
        icon_color="orange",  # Corrigido para evitar NameError[cite: 1]
        width=320,
        keyboard_type=ft.KeyboardType.NUMBER,
        input_filter=ft.InputFilter(
            allow=True, regex_string=r"^\d{0,5}(\.\d{0,3})?$"),
        text_align=ft.TextAlign.CENTER,
        hint_text="00000.000"
    )

    # 2. Recuperação de dados do Scanner OCR[cite: 2]
    unidade_ocr = page.session.get("unidade_scanner")
    valor_ocr = page.session.get("valor_scanner")

    if unidade_ocr:
        txt_unidade.value = unidade_ocr
        page.session.set("unidade_scanner", None)
    if valor_ocr:
        txt_agua.value = valor_ocr
        page.session.set("valor_scanner", None)

    # --- FUNÇÕES DE LÓGICA ---
    def avancar():
        try:
            idx = db_lista.index(txt_unidade.value)
            if idx + 1 < len(db_lista):
                txt_unidade.value = db_lista[idx + 1]
                txt_agua.value = ""
                txt_gas.value = ""
            page.update()
        except:
            pass

    def abrir_dialogo_gas():
        def fechar(escolha_gas):
            page.dialog.open = False
            state["lidas_no_hall"] = 0
            if escolha_gas:
                state["modo"] = "GAS"
                lbl_modo.value, lbl_modo.color = "MODO: GÁS", "orange"
                img_icon.name, img_icon.color = "local_fire_department", "orange"
                idx = db_lista.index(txt_unidade.value)
                txt_unidade.value = db_lista[max(0, idx - 3)]
            else:
                state["modo"] = "AGUA"
                lbl_modo.value, lbl_modo.color = "MODO: ÁGUA", "blue"
                img_icon.name, img_icon.color = "water_drop", "blue"  # Padronizado para string
                avancar()  # ft.icons.WATER_DROP

        page.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Hall Concluído"),
            content=ft.Text("Deseja realizar a leitura de GÁS deste andar?"),
            actions=[
                ft.TextButton("Sim, ler Gás", on_click=lambda _: fechar(True)),
                ft.TextButton("Não, próximo",
                              on_click=lambda _: fechar(False)),
            ]
        )
        page.dialog.open = True
        page.update()

    async def salvar_clique(e):
        valor_agua = (txt_agua.value or "").replace(",", ".").strip()
        valor_gas = (txt_gas.value or "").replace(",", ".").strip()

        if not valor_agua:
            page.snack_bar = ft.SnackBar(ft.Text("Insira o valor!"))
            page.snack_bar.open = True
            page.update()
            return

        try:
            v_agua = float(valor_agua)
            v_gas = float(valor_gas) if valor_gas else None
            # Captura a hora exata da coleta no fuso de SP
            data_coleta = datetime.now(fuso_sp).strftime("%d/%m/%Y %H:%M:%S")
        except ValueError:
            page.snack_bar = ft.SnackBar(ft.Text("Valor inválido."))
            page.snack_bar.open = True
            page.update()
            return

        # Salva no banco local para o SyncService sincronizar depois
        res = Database.salvar_leitura(
            unidade=txt_unidade.value,
            valor_agua=v_agua,
            valor_gas=v_gas,
            modo=state["modo"],
            data_hora=data_coleta  # Passando a data formatada
        )

        if res["sucesso"]:
            img_icon.visible, icon_save.visible = False, True
            page.update()
            await asyncio.sleep(0.5)
            img_icon.visible, icon_save.visible = True, False

            state["lidas_no_hall"] += 1
            if state["lidas_no_hall"] >= 4:
                abrir_dialogo_gas()
            else:
                avancar()
        page.update()

    return ft.View(
        route="/medicao",
        bgcolor="#121417",
        appbar=ft.AppBar(
            title=ft.Text("Nova Medição"),
            center_title=True,
            leading=ft.IconButton("arrow_back",  # Padronizado para string
                                  on_click=lambda _: page.go("/menu"))
        ),
        controls=[
            ft.Column([
                ft.Container(
                    content=ft.Stack([img_icon, icon_save]),
                    alignment="center"  # Corrigido para PascalCase[cite: 1]
                ),
                lbl_modo,
                txt_unidade,
                txt_agua,
                txt_gas,
                ft.Container(height=10),
                ft.ElevatedButton(
                    "GRAVAR LEITURA", on_click=salvar_clique, width=320, height=65),
                ft.TextButton("ABRIR SCANNER OCR", icon=ft.icons.CAMERA_ALT,
                              on_click=lambda _: page.go("/scanner"))
            ], horizontal_alignment="center", alignment=ft.MainAxisAlignment.CENTER, expand=True)
        ]
    )
