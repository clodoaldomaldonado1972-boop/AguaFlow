import flet as ft
import asyncio
import pytz  # Para garantir o horário de Brasília
from datetime import datetime
from database.database import Database
import views.styles as st  # Importando seus estilos personalizados
from utils.auth_utils import validar_sessao


def montar_tela_medicao(page: ft.Page):
    # Proteção de Rota
    auth_check = validar_sessao(page, "/medicao")
    if auth_check:
        return auth_check

    # Recupera a lista de unidades (ex: 98 unidades do Vivere)[cite: 2]
    db_lista = Database._gerar_lista_unidades()
    state = {"modo": "AGUA", "lidas_no_hall": 0}

    # Configuração de fuso horário para a coleta
    fuso_sp = pytz.timezone('America/Sao_Paulo')

    # Helper function to check if a unit has been read for the current month
    def is_unit_read(unit_id_to_check):
        leituras_mes = Database.get_leituras_mes_atual()
        for leitura in leituras_mes:
            if leitura.get('unidade_id') == unit_id_to_check:
                return True
        return False

    # Determine initial unit value for the dropdown
    # 1. Check for last_read_unit_id in client_storage
    last_read_unit_id = page.client_storage.get("last_read_unit_id") # Key for last unit read
    last_read_agua_value = page.client_storage.get("last_read_agua_value") # Key for last water value
    last_read_gas_value = page.client_storage.get("last_read_gas_value") # Key for last gas value

    initial_unit_value = db_lista[0] if db_lista else None

    if last_read_unit_id and last_read_unit_id in db_lista:
        initial_unit_value = last_read_unit_id
        # If unit is restored, try to restore values too
        if last_read_agua_value: txt_agua.value = last_read_agua_value
        if last_read_gas_value: txt_gas.value = last_read_gas_value

    # 2. Recuperação de dados do Scanner OCR (takes precedence if available)
    unidade_ocr = page.session.get("unidade_scanner")
    valor_ocr = page.session.get("valor_scanner")

    if unidade_ocr: # OCR takes precedence
        initial_unit_value = unidade_ocr # Overwrite if OCR has a unit
        page.session.set("unidade_scanner", None)
    if valor_ocr:
        txt_agua.value = valor_ocr
        page.session.set("valor_scanner", None)

    # 1. Elementos Visuais com cores em string para evitar erro de 'colors not defined'[cite: 1]
    img_icon = ft.Icon("water", color="blue", size=140)
    icon_save = ft.Icon("save", color="green", size=140, visible=False)
    lbl_modo = ft.Text("MODO: ÁGUA", color="blue", weight="bold", size=22)

    txt_unidade = ft.Dropdown(
        label="Unidade",
        options=[ft.dropdown.Option(u) for u in db_lista],
        width=320,
        value=initial_unit_value, # Use the determined initial value
        border_color="blue"
    )

    txt_agua = ft.TextField(
        label="Leitura Água (m³)",
        icon="water_drop",
        width=320,
        keyboard_type=ft.KeyboardType.NUMBER,
        input_filter=ft.InputFilter(
            allow=True, regex_string=r"^\d{0,5}(\.\d{0,3})?$"),
        text_align=ft.TextAlign.CENTER,
        hint_text="00000.000"
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

    # --- FUNÇÕES DE LÓGICA ---
    def avancar():
        try:
            idx = db_lista.index(txt_unidade.value)
            if idx + 1 < len(db_lista):
                next_unit = db_lista[idx + 1]
                # Skip units already read if advancing
                while is_unit_read(next_unit) and db_lista.index(next_unit) + 1 < len(db_lista):
                    next_unit = db_lista[db_lista.index(next_unit) + 1]
                txt_unidade.value = next_unit
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

        current_unit = txt_unidade.value

        # --- Validação da Unidade Anterior (Offline-First) ---
        current_unit_index = db_lista.index(current_unit)
        if current_unit_index > 0: # If it's not the very first unit
            previous_unit = db_lista[current_unit_index - 1]
            if not is_unit_read(previous_unit):
                page.snack_bar = ft.SnackBar(
                    ft.Text(f"Atenção: A unidade anterior ({previous_unit}) não foi lida. Por favor, siga a sequência."),
                    bgcolor=st.ACCENT_ORANGE
                )
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
        # Use current_unit for saving
        res = Database.salvar_leitura(
            unidade=current_unit,
            valor_agua=v_agua,
            valor_gas=v_gas,
            modo=state["modo"],
            data_hora=data_coleta  # Passando a data formatada
        )
        # Update last read unit in client storage for resuming
        # Also store the values for potential restoration/clearing
        page.client_storage.set("last_read_unit_id", current_unit)
        page.client_storage.set("last_read_agua_value", valor_agua)
        page.client_storage.set("last_read_gas_value", valor_gas)

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
        # Ensure the clear button visibility is updated
        btn_limpar_ultima_leitura.visible = True
        page.update()

    async def limpar_ultima_leitura(e):
        """Remove as chaves de última leitura do client_storage e reseta os campos."""
        page.client_storage.remove("last_read_unit_id")
        page.client_storage.remove("last_read_agua_value")
        page.client_storage.remove("last_read_gas_value")

        txt_unidade.value = db_lista[0] if db_lista else None
        txt_agua.value = ""
        txt_gas.value = ""
        btn_limpar_ultima_leitura.visible = False # Hide button after clearing
        page.update()

    # Botão para limpar a última leitura, visível apenas se houver uma última leitura salva
    btn_limpar_ultima_leitura = ft.TextButton(
        "Limpar Última Leitura",
        icon=ft.icons.HIGHLIGHT_OFF,
        on_click=limpar_ultima_leitura,
        visible=page.client_storage.get("last_read_unit_id") is not None
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
                ft.Container(height=5),
                btn_limpar_ultima_leitura, # Add the new button here
                ft.ElevatedButton(
                    "GRAVAR LEITURA", on_click=salvar_clique, width=320, height=65),
                ft.TextButton("ABRIR SCANNER OCR", icon=ft.icons.CAMERA_ALT,
                              on_click=lambda _: page.go("/scanner"))
            ], horizontal_alignment="center", alignment=ft.MainAxisAlignment.CENTER, expand=True)
        ]
    )
