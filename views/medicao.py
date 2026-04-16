import flet as ft
import asyncio
from database.database import Database
from views import styles as st
from utils.audio_utils import tocar_alerta
from utils.scanner import ScannerAguaFlow

def montar_tela_medicao(page: ft.Page, on_back_click=None):
    # 1. Gera a lista de unidades baseada na regra do hall (Ex: 166, 165... 11)
    db_lista = Database._gerar_lista_unidades()
    
    # 2. Busca a última unidade salva para definir o ponto de partida automático
    try:
        ultima_lida = Database.buscar_ultima_unidade_lida()
        if ultima_lida in db_lista:
            idx = db_lista.index(ultima_lida)
            unidade_inicial = db_lista[idx + 1] if idx + 1 < len(db_lista) else db_lista[0]
        else:
            unidade_inicial = db_lista[0]
    except:
        unidade_inicial = "166"

    # --- COMPONENTES DE INTERFACE ---
    txt_unidade = st.campo_estilo("Unidade Atual", ft.icons.HOME, read_only=True)
    txt_unidade.value = unidade_inicial
    
    txt_agua = st.campo_estilo("Leitura Água (*)", ft.icons.WATER_DROP, keyboard_type=ft.KeyboardType.NUMBER)
    txt_agua.input_filter = ft.InputFilter(allow=True, regex_string=r"^\d*[.,]?\d{0,2}$", replacement_string="")

    txt_gas = st.campo_estilo("Leitura Gás (Opcional)", ft.icons.LOCAL_GAS_STATION, keyboard_type=ft.KeyboardType.NUMBER)
    txt_gas.input_filter = ft.InputFilter(allow=True, regex_string=r"^\d*[.,]?\d{0,2}$", replacement_string="")

    lbl_status = ft.Text("", size=14, weight="bold")

    # --- LÓGICA DO SCANNER ---
    async def processar_retorno_scanner(unidade, valor, sucesso):
        """Atualiza os campos após a leitura da câmera/arquivo."""
        if unidade:
            txt_unidade.value = unidade
        if valor:
            txt_agua.value = str(valor)
        
        if sucesso:
            lbl_status.value = "✅ Leitura capturada com sucesso!"
            lbl_status.color = "green"
        else:
            lbl_status.value = "📍 Unidade lida. Insira o valor manualmente."
            lbl_status.color = "blue"
        page.update()

    scanner_motor = ScannerAguaFlow(page, processar_retorno_scanner)

    async def acionar_scanner(e):
        lbl_status.value = "📷 Abrindo scanner..."
        lbl_status.color = "blue"
        page.update()
        await scanner_motor.iniciar_scan(tipo="Água")

    def disparar_snack(msg, cor="red"):
        page.snack_bar = ft.SnackBar(ft.Text(msg), bgcolor=cor)
        page.snack_bar.open = True
        page.update()

    # --- LÓGICA DE SALVAMENTO E VALIDAÇÃO ---
    async def realizar_salvamento(e):
        if not txt_agua.value:
            disparar_snack("A leitura de ÁGUA é obrigatória!")
            return

        # Validação de Sequência Logística
        ultima_no_db = Database.buscar_ultima_unidade_lida()
        if ultima_no_db:
            idx_esperado = db_lista.index(ultima_no_db) + 1
            if idx_esperado < len(db_lista):
                unidade_esperada = db_lista[idx_esperado]
                
                # Se o operador pular a unidade, dispara Beep e bloqueia
                if txt_unidade.value != unidade_esperada:
                    tocar_alerta() 
                    lbl_status.value = f"⚠️ Sequência Incorreta! Esperado: {unidade_esperada}"
                    lbl_status.color = "red"
                    page.update()
                    return

        try:
            v_agua = round(float(txt_agua.value.replace(',', '.')), 2)

            # Registra leitura de Água
            res_agua = Database.registrar_leitura(
                unidade=txt_unidade.value,
                valor=v_agua,
                tipo_leitura="Água"
            )

            # Registra leitura de Gás se presente
            res_gas = None
            if txt_gas.value:
                v_gas = round(float(txt_gas.value.replace(',', '.')), 2)
                res_gas = Database.registrar_leitura(
                    unidade=txt_unidade.value,
                    valor=v_gas,
                    tipo_leitura="Gás"
                )

            res = {'sucesso': res_agua, 'mensagem': 'OK' if res_agua else 'Falha ao registrar água'}

            if res['sucesso']:
                atual_idx = db_lista.index(txt_unidade.value)
                if atual_idx + 1 < len(db_lista):
                    proxima = db_lista[atual_idx + 1]
                    txt_unidade.value = proxima
                    txt_agua.value = ""
                    txt_gas.value = ""
                    lbl_status.value = f"✅ Salvo! Próxima: {proxima}"
                    lbl_status.color = "green"
                    txt_agua.focus()
                else:
                    lbl_status.value = "🎯 Roteiro de leitura concluído!"
                    lbl_status.color = "blue"
                    page.update()
                    await asyncio.sleep(2)
                    page.go("/menu")
            else:
                disparar_snack(res['mensagem'])

        except ValueError:
            disparar_snack("Valor numérico inválido!")
        
        page.update()

    # --- LAYOUT DA VIEW ---
    return ft.View(
        route="/medicao",
        appbar=ft.AppBar(
            title=ft.Text("Medição AguaFlow"), 
            bgcolor=ft.colors.BLUE_900,
            color="white",
            leading=ft.IconButton(ft.icons.ARROW_BACK, icon_color="white", on_click=lambda _: page.go("/menu"))
        ),
        controls=[
            ft.Column([
                ft.Container(
                    padding=30,
                    bgcolor=ft.colors.with_opacity(0.05, "white"),
                    border_radius=20,
                    content=ft.Column([
                        ft.Icon(ft.icons.SPEED, size=50, color="blue"),
                        ft.Text("Registro de Consumo", size=20, weight="bold"),
                        ft.Divider(height=10, color="transparent"),
                        
                        # Botão de Hardware (Scanner)
                        ft.ElevatedButton(
                            "SCANNER AUTOMÁTICO",
                            icon=ft.icons.CAMERA_ALT,
                            bgcolor=ft.colors.BLUE_700,
                            color=ft.colors.WHITE,
                            width=320,
                            height=50,
                            on_click=acionar_scanner
                        ),
                        
                        ft.Divider(height=10, color="transparent"),
                        txt_unidade,
                        txt_agua,
                        txt_gas,
                        lbl_status,
                        
                        ft.Divider(height=20),
                        ft.ElevatedButton(
                            "CONFIRMAR E SALVAR", 
                            icon=ft.icons.SAVE, 
                            width=320,
                            height=50,
                            on_click=lambda e: page.run_task(realizar_salvamento, e)
                        ),
                        ft.TextButton("Cancelar", on_click=lambda _: page.go("/menu"))
                    ], horizontal_alignment="center", spacing=15)
                )
            ], horizontal_alignment="center", scroll=ft.ScrollMode.AUTO)
        ]
    )