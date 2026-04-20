import flet as ft
import asyncio
import re
from database.database import Database
from views import styles as st
from utils.audio_utils import tocar_alerta
from utils.scanner import ScannerAguaFlow

def montar_tela_medicao(page: ft.Page, on_back_click=None):
    """
    Tela de medição AguaFlow sincronizada:
    - Suporte a unidades Duplex (163/164 e 23/24)
    - Trava Água: 7 dígitos (5+2) | Trava Gás: 8 dígitos (5+3)
    - Scanner OCR com Timeout e Fallback Manual
    """
    db_lista = Database._gerar_lista_unidades()
    
    # 1. Recupera a última unidade para sequência inteligente
    ultima_lida = Database.buscar_ultima_unidade_lida()
    if ultima_lida and ultima_lida in db_lista:
        unidade_inicial = Database.obter_proxima_unidade(ultima_lida, db_lista)
    else:
        unidade_inicial = db_lista[0]

    # --- FUNÇÃO DE CALLBACK DO SCANNER (Sincronizada com scanner.py) ---
    async def processar_retorno_ocr(unidade_ocr, valor_ocr, sucesso):
        if sucesso and valor_ocr:
            txt_agua.value = valor_ocr
            # Dispara a máscara e validação para o valor lido
            aplicar_trava_e_mascara(ft.ControlEvent(name="change", target=txt_agua.uid, control=txt_agua, data=valor_ocr, page=page))
            tocar_alerta("sucesso")
        elif valor_ocr == "TIMEOUT":
            page.snack_bar = ft.SnackBar(ft.Text("⚠️ OCR demorou demais. Insira manualmente."), bgcolor=ft.colors.ORANGE_800)
            page.snack_bar.open = True
            txt_agua.focus()
        
        btn_scanner.disabled = False
        page.update()

    # --- MOTOR DE VALIDAÇÃO E TRAVAS ---
    def aplicar_trava_e_mascara(e):
        campo = e.control
        valor_limpo = re.sub(r"\D", "", campo.value)
        
        if campo == txt_agua:
            if len(valor_limpo) > 7: valor_limpo = valor_limpo[:7]
            campo.value = f"{valor_limpo[:-2]},{valor_limpo[-2:]}" if len(valor_limpo) > 2 else valor_limpo
            
        elif campo == txt_gas:
            if len(valor_limpo) > 8: valor_limpo = valor_limpo[:8]
            campo.value = f"{valor_limpo[:-3]},{valor_limpo[-3:]}" if len(valor_limpo) > 3 else valor_limpo

        # Validação do Botão Salvar
        agua_ok = len(re.sub(r"\D", "", txt_agua.value)) == 7
        gas_valor_puro = re.sub(r"\D", "", txt_gas.value)
        gas_ok = len(gas_valor_puro) == 0 or len(gas_valor_puro) == 8
        
        btn_salvar.disabled = not (agua_ok and gas_ok)
        campo.update()
        btn_salvar.update()

    # --- COMPONENTES ---
    txt_unidade = st.campo_estilo(label="Unidade", icon_name=ft.icons.APARTMENT, read_only=True)
    txt_unidade.value = unidade_inicial

    txt_agua = st.campo_estilo(label="Água (5+2)", icon_name=ft.icons.WATER_DROP, keyboard_type=ft.KeyboardType.NUMBER)
    txt_agua.on_change = aplicar_trava_e_mascara

    txt_gas = st.campo_estilo(label="Gás (5+3)", icon_name=ft.icons.LOCAL_GAS_STATION, keyboard_type=ft.KeyboardType.NUMBER)
    txt_gas.on_change = aplicar_trava_e_mascara

    # Instancia o Scanner passando o novo callback sincronizado
    scanner_engine = ScannerAguaFlow(page=page, ao_detectar_leitura=processar_retorno_ocr)

    async def disparar_ocr(e):
        btn_scanner.disabled = True
        page.update()
        await scanner_engine.iniciar_scan(tipo="Água")

    # --- SALVAMENTO COM REGRA DUPLEX ---
    async def realizar_salvamento(e):
        progresso.visible = True
        btn_salvar.disabled = True
        page.update()

        # Validação e conversão segura dos valores
        try:
            agua_f = float(txt_agua.value.replace(",", ".")) if txt_agua.value else None
            gas_f = float(txt_gas.value.replace(",", ".")) if txt_gas.value else 0.0
        except ValueError:
            page.snack_bar = ft.SnackBar(ft.Text("❌ Valores inválidos. Use apenas números."), bgcolor=ft.colors.RED_700)
            page.snack_bar.open = True
            progresso.visible = False
            page.update()
            return

        if agua_f is None:
            page.snack_bar = ft.SnackBar(ft.Text("❌ Leitura de água é obrigatória."), bgcolor=ft.colors.RED_700)
            page.snack_bar.open = True
            progresso.visible = False
            page.update()
            return

        unidade_atual = txt_unidade.value
        sucesso = await asyncio.to_thread(Database.salvar_leitura_local, unidade_atual, agua_f, gas_f, "Mensal")

        if sucesso:
            tocar_alerta("sucesso")
            # Lógica Duplex centralizada no Database
            txt_unidade.value = Database.obter_proxima_unidade(unidade_atual, db_lista)

            txt_agua.value = ""; txt_gas.value = ""; btn_salvar.disabled = True
            page.snack_bar = ft.SnackBar(ft.Text(f"✅ Unidade {unidade_atual} salva!"), bgcolor=ft.colors.GREEN_700)
        else:
            page.snack_bar = ft.SnackBar(ft.Text("❌ Erro ao salvar dados."), bgcolor=ft.colors.RED_700)

        progresso.visible = False
        page.snack_bar.open = True
        page.update()

    # --- BOTÕES ---
    btn_scanner = ft.ElevatedButton("ABRIR SCANNER OCR", icon=ft.icons.CAMERA_ALT, on_click=disparar_ocr, style=st.BTN_SPECIAL)
    btn_salvar = ft.ElevatedButton("CONFIRMAR E GUARDAR", icon=ft.icons.SAVE, style=st.BTN_MAIN, width=320, height=60, disabled=True, on_click=realizar_salvamento)
    progresso = ft.ProgressBar(width=300, color=st.ACCENT_ORANGE, visible=False)

    return ft.View(
        route="/medicao",
        bgcolor=st.BG_DARK,
        controls=[
            ft.AppBar(title=ft.Text("Nova Medição - Vivere"), center_title=True, leading=ft.IconButton(ft.icons.ARROW_BACK, on_click=lambda _: page.go("/menu"))),
            ft.Column([
                ft.Container(padding=20, content=ft.Column([
                    ft.Text("Captação Residencial", style=st.TEXT_TITLE),
                    ft.Text("Regra Duplex e Travas Ativas", style=st.TEXT_SUB),
                    ft.Divider(height=20, color="transparent"),
                    btn_scanner,
                    ft.Divider(height=10, color="transparent"),
                    txt_unidade, txt_agua, txt_gas,
                    progresso, ft.Divider(height=20),
                    btn_salvar,
                    ft.TextButton("Voltar", on_click=lambda _: page.go("/menu"), style=ft.ButtonStyle(color=st.GREY))
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15))
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, scroll=ft.ScrollMode.ADAPTIVE)
        ]
    )