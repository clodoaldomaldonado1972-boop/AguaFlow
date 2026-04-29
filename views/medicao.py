import flet as ft
import asyncio
from database.database import Database
from views import styles as st

def montar_tela_medicao(page: ft.Page):
    db_lista = Database._gerar_lista_unidades()
    state = {"modo": "AGUA", "lidas_no_hall": 0}

    # 1. Definição dos Elementos Visuais Primeiro
    img_icon = ft.Icon(name=ft.icons.WATER_DROP, color="blue", size=140)
    icon_save = ft.Icon(name=ft.icons.SAVE, color="green", size=140, visible=False)
    lbl_modo = ft.Text("MODO: ÁGUA", color="blue", weight="bold", size=22)
    
    txt_unidade = ft.Dropdown(
        label="Unidade", 
        options=[ft.dropdown.Option(u) for u in db_lista],
        width=320, 
        value=db_lista[0]
    )

    txt_agua = ft.TextField(
        label="Leitura Água (m³)",
        icon=ft.icons.WATER_DROP,
        icon_color=ft.colors.BLUE,
        width=320,
        keyboard_type=ft.KeyboardType.NUMBER,
        # Regex: Até 5 dígitos, ponto opcional, seguido de até 2 dígitos
        input_filter=ft.InputFilter(allow=True, regex_string=r"^\d{0,5}(\.\d{0,2})?$"),
        text_align=ft.TextAlign.CENTER,
        hint_text="00000.00"
    )
    txt_gas = ft.TextField(
        label="Leitura Gás (m³)",
        icon=ft.icons.LOCAL_FIRE_DEPARTMENT,
        icon_color=ft.colors.ORANGE_700,
        width=320,
        keyboard_type=ft.KeyboardType.NUMBER,
        # Regex: Até 5 dígitos, ponto opcional, seguido de até 3 dígitos
        input_filter=ft.InputFilter(allow=True, regex_string=r"^\d{0,5}(\.\d{0,3})?$"),
        text_align=ft.TextAlign.CENTER,
        hint_text="00000.000"
    )

    # 2. Recupera o que foi lido no scanner (se houver)
    unidade_ocr = page.session.get("unidade_scanner")
    valor_ocr = page.session.get("valor_scanner")
    
    if unidade_ocr:
        txt_unidade.value = unidade_ocr
        page.session.set("unidade_scanner", None)
    if valor_ocr:
        txt_agua.value = valor_ocr
        page.session.set("valor_scanner", None)
        
    # --- LÓGICA DE AVANÇO E GÁS ---
    def avancar():
        idx = db_lista.index(txt_unidade.value)
        if idx + 1 < len(db_lista):
            txt_unidade.value = db_lista[idx + 1]
            txt_agua.value = ""
            txt_gas.value = ""
        page.update()

    def abrir_dialogo_gas():
        def fechar(escolha_gas):
            page.dialog.open = False
            state["lidas_no_hall"] = 0
            if escolha_gas:
                state["modo"] = "GAS"
                lbl_modo.value, lbl_modo.color = "MODO: GÁS", "orange"
                img_icon.name, img_icon.color = ft.icons.LOCAL_FIRE_DEPARTMENT, "orange"
                # Opcional: volta 3 unidades para ler o gás do hall recém lido
                idx = db_lista.index(txt_unidade.value)
                txt_unidade.value = db_lista[max(0, idx - 3)]
            else:
                state["modo"] = "AGUA"
                lbl_modo.value, lbl_modo.color = "MODO: ÁGUA", "blue"
                img_icon.name, img_icon.color = ft.icons.WATER_DROP, "blue"
                avancar()
            page.update()

        page.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Hall Concluído"),
            content=ft.Text("Deseja realizar a leitura de GÁS deste andar?"),
            actions=[
                ft.TextButton("Sim, ler Gás", on_click=lambda _: fechar(True)),
                ft.TextButton("Não, próximo", on_click=lambda _: fechar(False)),
            ]
        )
        page.dialog.open = True
        page.update()

    async def salvar_clique(e):
        valor_agua = (txt_agua.value or "").replace(",", ".").strip()
        valor_gas = (txt_gas.value or "").replace(",", ".").strip()

        if not valor_agua:
            page.snack_bar = ft.SnackBar(ft.Text("Insira o valor!")); page.snack_bar.open = True
            page.update(); return

        try:
            valor_agua_float = float(valor_agua)
            valor_gas_float = float(valor_gas) if valor_gas else None
        except ValueError:
            page.snack_bar = ft.SnackBar(ft.Text("Valor inválido. Use apenas números."))
            page.snack_bar.open = True
            page.update()
            return

        res = Database.salvar_leitura(
            txt_unidade.value,
            valor_agua_float,
            valor_gas_float,
            state["modo"],
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

    # --- RETORNO DA VIEW ---
    return ft.View(
        route="/medicao",
        bgcolor="#121417",
        appbar=ft.AppBar(
            title=ft.Text("Nova Medição"),
            center_title=True,
            leading=ft.IconButton(ft.icons.ARROW_BACK, on_click=lambda _: page.go("/menu"))
        ),
        controls=[
            ft.Column([
                ft.Container(
                    content=ft.Stack([img_icon, icon_save]),
                    alignment=ft.alignment.center
                ),
                lbl_modo,
                txt_unidade,
                txt_agua,
                txt_gas,
                ft.Container(height=10),
                ft.ElevatedButton("GRAVAR LEITURA", on_click=salvar_clique, width=320, height=65),
                ft.TextButton("ABRIR SCANNER OCR", icon=ft.icons.CAMERA_ALT, on_click=lambda _: page.go("/scanner"))
            ], horizontal_alignment="center", alignment=ft.MainAxisAlignment.CENTER, expand=True)
        ]
    )