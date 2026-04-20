import flet as ft
import asyncio
import re
from database.database import Database
from views import styles as st
from utils.audio_utils import tocar_alerta
from utils.scanner import ScannerAguaFlow

def montar_tela_medicao(page: ft.Page, on_back_click=None):
    """
    Tela de medição AguaFlow v1.0.2:
    - Suporte a unidades Duplex (163/164 e 23/24)
    - Trava Água: 7 dígitos (5+2) | Trava Gás: 8 dígitos (5+3)
    - Scanner OCR com integração assíncrona estável
    """
    db_lista = Database._gerar_lista_unidades()
    
    # 1. Recupera a última unidade para sequência inteligente (Refatorado v1.0.2)
    ultima_lida = Database.buscar_ultima_unidade_lida()
    
    # Lógica de sugestão da próxima unidade
    if ultima_lida and ultima_lida in db_lista:
        idx = db_lista.index(ultima_lida)
        unidade_inicial = db_lista[idx + 1] if idx + 1 < len(db_lista) else ultima_lida
    else:
        unidade_inicial = db_lista[0]

    # --- ELEMENTOS DE INTERFACE ---
    txt_unidade = ft.Dropdown(
        label="Unidade / Apartamento",
        value=unidade_inicial,
        options=[ft.dropdown.Option(u) for u in db_lista],
        border_color=st.ACCENT_ORANGE,
        width=320
    )

    txt_agua = ft.TextField(
        label="Leitura ÁGUA (m³)", # <--- ADICIONE A VÍRGULA AQUI
        hint_text="00000.00",
        keyboard_type=ft.KeyboardType.NUMBER,
        border_color=ft.colors.BLUE_400,
        suffix_text="m³",
        on_change=lambda e: validar_campos(),
        width=320
    )

    txt_gas = ft.TextField(
        label="Leitura GÁS (m³)", # <--- CONFIRA SE ESTA TAMBÉM TEM VÍRGULA
        hint_text="00000.000",
        keyboard_type=ft.KeyboardType.NUMBER,
        border_color=ft.colors.ORANGE_400,
        suffix_text="m³",
        on_change=lambda e: validar_campos(),
        width=320
    )

    # --- CALLBACK DO SCANNER ---
    async def processar_retorno_ocr(unidade_ocr, valor_ocr, sucesso):
        progresso.visible = False
        if sucesso and valor_ocr:
            # Limpa caracteres não numéricos para garantir precisão
            valor_limpo = re.sub(r"[^\d.,]", "", valor_ocr)
            txt_agua.value = valor_limpo
            tocar_alerta("sucesso")
            page.snack_bar = ft.SnackBar(ft.Text("OCR: Leitura capturada!"), bgcolor="green")
        else:
            tocar_alerta("erro")
            page.snack_bar = ft.SnackBar(ft.Text("Falha no OCR. Use entrada manual."), bgcolor="orange")
        
        page.snack_bar.open = True
        validar_campos()
        page.update()

    # Inicializa o Scanner
    scanner = ScannerAguaFlow(page, processar_retorno_ocr)

    async def disparar_ocr(e):
        progresso.visible = True
        page.update()
        await scanner.iniciar_scan(tipo="Água")

    def validar_campos():
        # Botão habilitado se houver leitura de água
        btn_salvar.disabled = not (len(txt_agua.value) >= 3)
        page.update()

    async def realizar_salvamento(e):
        btn_salvar.disabled = True
        progresso.visible = True
        page.update()

        try:
            v_agua = float(txt_agua.value.replace(',', '.'))
            v_gas = float(txt_gas.value.replace(',', '.') if txt_gas.value else 0)
            
            sucesso = Database.salvar_leitura_local(
                unidade=txt_unidade.value,
                agua=v_agua,
                gas=v_gas,
                tipo="Água"
            )

            if sucesso:
                tocar_alerta("sucesso")
                page.snack_bar = ft.SnackBar(ft.Text(f"✅ Unidade {txt_unidade.value} salva!"), bgcolor="green")
                page.snack_bar.open = True
                
                # --- Lógica de Continuidade Decrescente ---
                unidade_atual = txt_unidade.value
                if unidade_atual in db_lista:
                    idx = db_lista.index(unidade_atual)
                    # Como a lista já está invertida no banco, o próximo índice (idx + 1) será o apto abaixo
                    proxima_unidade = db_lista[idx + 1] if idx + 1 < len(db_lista) else db_lista[0]
                    
                    # Atualiza a interface sem sair da tela
                    txt_unidade.value = proxima_unidade
                    txt_agua.value = ""
                    txt_gas.value = ""
                    txt_agua.focus() # Foca no campo de água para a próxima leitura
                
                page.update()
            else:
                raise Exception("Erro ao gravar no SQLite")

        except Exception as err:
            page.snack_bar = ft.SnackBar(ft.Text(f"Erro: {err}"), bgcolor="red")
            page.snack_bar.open = True
            btn_salvar.disabled = False
        
        progresso.visible = False
        page.update()
    # --- UI E LAYOUT ---
    btn_scanner = ft.ElevatedButton(
        "ABRIR SCANNER OCR", 
        icon=ft.icons.CAMERA_ALT, 
        on_click=disparar_ocr, 
        style=st.BTN_SPECIAL
    )
    
    btn_salvar = ft.ElevatedButton(
        "CONFIRMAR E GUARDAR", 
        icon=ft.icons.SAVE, 
        style=st.BTN_MAIN, 
        width=320, 
        height=60, 
        disabled=True, 
        on_click=realizar_salvamento
    )

    progresso = ft.ProgressBar(width=300, color=st.ACCENT_ORANGE, visible=False)

    return ft.View(
        route="/medicao",
        bgcolor=st.BG_DARK,
        controls=[
            ft.AppBar(
                title=ft.Text("Nova Medição - Vivere"), 
                center_title=True, 
                bgcolor=ft.colors.SURFACE_VARIANT,
                leading=ft.IconButton(ft.icons.ARROW_BACK, on_click=lambda _: page.go("/menu"))
            ),
            ft.Column([
                ft.Container(
                    padding=20, 
                    content=ft.Column([
                        ft.Text("Captação Residencial", style=st.TEXT_TITLE),
                        ft.Text("Unidades Duplex e Travas Ativas", style=st.TEXT_SUB),
                        ft.Divider(height=20, color="transparent"),
                        
                        btn_scanner,
                        ft.Divider(height=10, color="transparent"),
                        
                        txt_unidade, 
                        txt_agua, 
                        txt_gas,
                        
                        progresso, 
                        ft.Divider(height=20),
                        
                        btn_salvar,
                        ft.TextButton(
                            "Cancelar", 
                            icon=ft.icons.CLOSE, 
                            on_click=lambda _: page.go("/menu"),
                            style=ft.ButtonStyle(color="red")
                        )
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, scroll=ft.ScrollMode.ADAPTIVE)
        ],
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )