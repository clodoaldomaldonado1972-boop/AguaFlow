import flet as ft
import asyncio
from database.database import Database
from views import styles as st
from utils.scanner import ScannerAguaFlow
# Importa a função corrigida para APK
from utils.audio_utils import tocar_alerta 

try:
    from utils.updater import VERSION
except ImportError:
    VERSION = "1.1.1"

def montar_tela_medicao(page: ft.Page, on_back_click=None):
    # --- CARREGAMENTO INICIAL ---
    db_lista = Database._gerar_lista_unidades()
    ultima_lida = Database.buscar_ultima_unidade_lida()
    
    # Determina a unidade inicial baseada na última leitura
    unidade_inicial = db_lista[0]
    if ultima_lida and ultima_lida in db_lista:
        idx = db_lista.index(ultima_lida)
        unidade_inicial = db_lista[idx + 1] if idx + 1 < len(db_lista) else db_lista[0]

    # --- COMPONENTES DE INTERFACE ---
    progresso_barra = ft.ProgressBar(width=300, visible=False, color=st.PRIMARY_BLUE)
    status_text = ft.Text("", color="orange", size=12)

    txt_unidade = ft.Dropdown(
        label="Unidade / Apartamento",
        value=unidade_inicial,
        options=[ft.dropdown.Option(u) for u in db_lista],
        width=300,
        bgcolor="#1E2126"
    )

    txt_agua = ft.TextField(
        label="Leitura Água (m³)",
        hint_text="00000.00",
        width=300,
        keyboard_type=ft.KeyboardType.NUMBER,
        icon=ft.icons.WATER_DROP
    )

    txt_gas = ft.TextField(
        label="Leitura Gás (m³)",
        hint_text="00000.000",
        width=300,
        keyboard_type=ft.KeyboardType.NUMBER,
        icon=ft.icons.GAS_METER
    )

    # --- CALLBACK DO SCANNER ---
    async def ao_detectar_leitura(unidade, valor, sucesso):
        """Callback que recebe os dados processados pelo OCR em scanner.py"""
        progresso_barra.visible = False
        if sucesso:
            # Se o OCR detectou a unidade, atualiza o dropdown
            if unidade and unidade in db_lista:
                txt_unidade.value = unidade
            
            # Atualiza o valor da água
            if valor:
                txt_agua.value = str(valor)
            
            status_text.value = "✅ Leitura capturada com sucesso!"
            tocar_alerta(page, tipo="sucesso")
        else:
            status_text.value = "⚠️ Falha no OCR. Insira os dados manualmente."
            tocar_alerta(page, tipo="erro")
        
        page.update()

    scanner = ScannerAguaFlow(page, ao_detectar_leitura)

    def disparar_scanner(e):
        """Aciona o scanner com feedback sonoro e visual."""
        metodo = getattr(scanner, 'iniciar_scan', None)
        if callable(metodo):
            tocar_alerta(page, tipo="alerta")
            # Usa run_task para não travar a UI durante a abertura do seletor
            page.run_task(scanner.iniciar_scan)
            status_text.value = "📸 Abrindo câmera / Galeria..."
            progresso_barra.visible = True
        else:
            tocar_alerta(page, tipo="erro")
            status_text.value = "⚠️ Erro técnico: Scanner não inicializado."
        page.update()

    btn_scanner = ft.ElevatedButton(
        "ESCANEAR HIDRÔMETRO",
        icon=ft.icons.CAMERA_ALT,
        on_click=disparar_scanner,
        width=300
    )

    # --- LÓGICA DE SALVAMENTO ---
    def salvar_dados(e):
        if not txt_unidade.value or not txt_agua.value:
            tocar_alerta(page, tipo="erro")
            page.snack_bar = ft.SnackBar(
                ft.Text("Erro: Preencha Unidade e Leitura da Água!"),
                bgcolor="red"
            )
            page.snack_bar.open = True
            page.update()
            return

        # Sanitização das entradas: converte vírgula para ponto e força float
        try:
            agua_sanitizada = str(txt_agua.value).replace(',', '.')
            gas_sanitizado = str(txt_gas.value or "0").replace(',', '.')
            # Validação das travas decimais (2 para água, 3 para gás)
            agua_float = float(agua_sanitizada)
            gas_float = float(gas_sanitizado)
        except (ValueError, AttributeError):
            tocar_alerta(page, tipo="erro")
            page.snack_bar = ft.SnackBar(
                ft.Text("Erro: Valores inválidos. Use formato 00000.00 para água."),
                bgcolor="red"
            )
            page.snack_bar.open = True
            page.update()
            return

        progresso_barra.visible = True
        btn_salvar.disabled = True
        page.update()

        # Chama salvar_leitura que agora possui validações de DUPLICADA e DECREMENTO
        res = Database.salvar_leitura(
            unidade=txt_unidade.value,
            agua=agua_float,
            gas=gas_float,
            tipo=VERSION
        )

        if res == "OK":
            tocar_alerta(page, tipo="sucesso")
            page.snack_bar = ft.SnackBar(
                ft.Text(f"Unidade {txt_unidade.value} salva com sucesso! 💾"), 
                bgcolor="green"
            )
            page.snack_bar.open = True
            status_text.value = ""
            
            # Próxima unidade automática baseada na sequência do condomínio
            try:
                atual_idx = db_lista.index(txt_unidade.value)
                if atual_idx + 1 < len(db_lista):
                    txt_unidade.value = db_lista[atual_idx + 1]
                
                # Limpa os campos de leitura para a próxima entrada
                txt_agua.value = ""
                txt_gas.value = ""
            except ValueError:
                pass
        
        elif res == "DUPLICADA":
            tocar_alerta(page, tipo="erro")
            status_text.value = f"⚠️ Já existe uma leitura para a unidade {txt_unidade.value} hoje."
            page.snack_bar = ft.SnackBar(ft.Text("Erro: Leitura duplicada!"), bgcolor="orange")
            page.snack_bar.open = True
            
        elif res == "DECREMENTO":
            tocar_alerta(page, tipo="erro")
            status_text.value = "❌ Valor informado é menor que a leitura anterior!"
            page.snack_bar = ft.SnackBar(ft.Text("Erro de integridade: Valor decrescente"), bgcolor="red")
            page.snack_bar.open = True

        elif res == "DB_LOCKED":
            tocar_alerta(page, tipo="erro")
            status_text.value = "⚠️ Banco de dados ocupado. Tente salvar novamente."

        progresso_barra.visible = False
        btn_salvar.disabled = False
        page.update()

    btn_salvar = ft.ElevatedButton(
        "SALVAR LEITURA",
        icon=ft.icons.SAVE,
        on_click=salvar_dados,
        style=st.BTN_SPECIAL,
        width=300
    )

    # --- CONSTRUÇÃO DA VIEW ---
    return ft.View(
        route="/medicao",
        bgcolor=st.BG_DARK,
        controls=[
            ft.AppBar(
                title=ft.Text(f"Medição Vivere - v{VERSION}"),
                bgcolor=st.BG_DARK
            ),
            ft.Column(
                [
                    ft.Container(
                        padding=20,
                        content=ft.Column(
                            [
                                ft.Text("Edifício Vivere Prudente", style=st.TEXT_SUB),
                                btn_scanner,
                                txt_unidade,
                                txt_agua,
                                txt_gas,
                                status_text,
                                progresso_barra,
                                btn_salvar,
                                ft.TextButton(
                                    "Voltar ao Menu", 
                                    icon=ft.icons.ARROW_BACK, 
                                    on_click=lambda _: page.go("/menu")
                                ),
                                ft.Container(height=10),
                                ft.Text(
                                    "Dica: Posicione o celular paralelo ao medidor.\nVerifique o OCR e tente novamente se necessário.",
                                    size=11,
                                    color="white70",
                                    text_align=ft.TextAlign.CENTER,
                                    style=ft.TextStyle(italic=True)
                                )
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER
                        )
                    )
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                scroll=ft.ScrollMode.AUTO
            )
        ]
    )