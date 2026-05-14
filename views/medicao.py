import flet as ft
import asyncio
import pytz  # Para garantir o horário de Brasília
import logging
import traceback
from datetime import datetime
from database.database import Database
from database.sync_service import SyncService
import views.styles as st  # Importando seus estilos personalizados
from utils.auth_utils import validar_sessao
from utils.logger_config import enviar_report_erro

logger = logging.getLogger(__name__)


def montar_tela_medicao(page: ft.Page):
    # Proteção de Rota
    auth_check = validar_sessao(page, "/medicao")
    if auth_check:
        return auth_check

    try:
        # Recupera a lista de unidades (ex: 98 unidades do Vivere)
        db_lista = Database._gerar_lista_unidades()
        state = {"modo": "AGUA", "lidas_no_hall": 0}

        # Configuração de fuso horário para a coleta
        fuso_sp = pytz.timezone('America/Sao_Paulo')

        def buscar_proxima_pendente():
            """Busca a próxima unidade na lista que ainda não foi lida."""
            try:
                # Busca leituras do mês para filtrar pendências por tipo
                leituras_mes = Database.get_leituras_mes_atual()
                if state["modo"] == "AGUA":
                    lidos = {l['unidade_id']
                             for l in leituras_mes if l['leitura_agua'] is not None}
                else:
                    lidos = {l['unidade_id']
                             for l in leituras_mes if l['leitura_gas'] is not None}

                unidade_atual = txt_unidade.value
                idx_atual = db_lista.index(
                    unidade_atual) if unidade_atual in db_lista else -1

                # Procura da atual em diante
                for i in range(idx_atual + 1, len(db_lista)):
                    if db_lista[i] not in lidos:
                        return db_lista[i]
            except:
                pass
            return None

        # Determine initial unit value for the dropdown
        # 1. Check for last_read_unit_id in page.user_data
        user_data = getattr(page, "user_data", {}) or {}
        last_read_unit_id = user_data.get("last_read_unit_id")
        last_read_agua_value = user_data.get("last_read_agua_value")
        last_read_gas_value = user_data.get("last_read_gas_value")

        proxima_pendente = buscar_proxima_pendente()
        initial_unit_value = proxima_pendente if proxima_pendente else (
            db_lista[0] if db_lista else None)
        if last_read_unit_id and last_read_unit_id in db_lista:
            initial_unit_value = last_read_unit_id

        # Elementos Visuais com ícones padronizados
        img_icon = ft.Icon("water", color="blue", size=140)
        icon_save = ft.Icon("save", color="green",
                            size=140, visible=False)
        lbl_modo = ft.Text("MODO: ÁGUA", color="blue", weight="bold", size=22)

        txt_unidade = ft.Dropdown(
            label="Unidade",
            options=[ft.dropdown.Option(u) for u in db_lista],
            width=320,
            value=initial_unit_value,  # Use the determined initial value
            border_color="blue"
        )

        txt_agua = ft.TextField(
            label="Leitura Água (m³)",
            icon="water_drop",
            width=320,
            keyboard_type=ft.KeyboardType.NUMBER,
            input_filter=ft.InputFilter(
                allow=True, regex_string=r"^\d{0,5}([,\.]\d{0,2})?$"),
            text_align=ft.TextAlign.CENTER,
            hint_text="00000,00"
        )

        txt_gas = ft.TextField(
            label="Leitura Gás (m³)",
            icon="local_fire_department",
            width=320,
            keyboard_type=ft.KeyboardType.NUMBER,
            input_filter=ft.InputFilter(
                allow=True, regex_string=r"^\d{0,5}([,\.]\d{0,2})?$"),
            text_align=ft.TextAlign.CENTER,
            hint_text="00000,00"
        )

        btn_gravar = ft.ElevatedButton(
            "GRAVAR LEITURA",
            on_click=lambda e: page.run_task(salvar_clique, e),
            width=320,
            height=65
        )

        def atualizar_estilos_modo():
            """Atualiza cores e ícones dos campos conforme o modo (Água ou Gás)."""
            is_agua = state["modo"] == "AGUA"
            cor = "blue" if is_agua else "orange"
            icone = "water_drop" if is_agua else "local_fire_department"

            # Atualiza Dropdown de Unidade
            txt_unidade.border_color = cor
            # Note: Dropdown não suporta prefix_icon em algumas versões do Flet, mas border_color é garantido

            # Destaca a borda do campo correspondente ao modo ativo
            txt_agua.border_color = cor if is_agua else None
            txt_agua.disabled = not is_agua
            txt_gas.border_color = cor if not is_agua else None
            txt_gas.disabled = is_agua

            # Atualiza o cabeçalho visual
            lbl_modo.value = f"MODO: {'ÁGUA' if is_agua else 'GÁS'}"
            lbl_modo.color = cor
            img_icon.name = icone
            img_icon.color = cor
            page.update()

        # --- COMPONENTES DE CONCLUSÃO ---
        async def finalizar_e_gerar_relatorio(e):
            btn_finalizar_sinc.disabled = True
            btn_finalizar_sinc.text = "SINCRONIZANDO..."
            page.update()

            qtd = await SyncService.executar_sincronismo_manual()

            # Aciona geração de relatório se houver dados
            from relatorio_engine import RelatorioEngine
            dados = Database.get_leituras_mes_atual()
            if dados:
                RelatorioEngine.gerar_relatorio_consumo(dados)
                RelatorioEngine.gerar_csv_consumo(dados)

            page.snack_bar = ft.SnackBar(
                ft.Text(f"✅ {qtd} leituras sincronizadas e relatórios gerados!"))
            page.snack_bar.open = True
            btn_finalizar_sinc.visible = False
            btn_reiniciar_ciclo.visible = True
            page.update()

        async def reiniciar_sistema(e):
            SyncService.limpar_leituras_locais()
            page.user_data["last_read_unit_id"] = None
            page.go("/menu")

        btn_finalizar_sinc = ft.ElevatedButton(
            "SINCRONIZAR E GERAR RELATÓRIO",
            icon="cloud_upload",
            bgcolor=st.SUCCESS_GREEN,
            color="white",
            visible=False,
            on_click=finalizar_e_gerar_relatorio,
            width=320, height=65
        )

        btn_reiniciar_ciclo = ft.ElevatedButton(
            "INICIAR NOVO CICLO",
            icon="replay",
            bgcolor="orange800",
            color="white",
            visible=False,
            on_click=reiniciar_sistema,
            width=320, height=65
        )

        # 2. Recuperação de dados do Scanner OCR (Agora após definição dos campos para evitar NameError)
        unidade_ocr = user_data.get("unidade_scanner")
        valor_ocr = user_data.get("valor_scanner")

        if unidade_ocr:
            txt_unidade.value = unidade_ocr
            user_data.pop("unidade_scanner", None)
        if valor_ocr:
            txt_agua.value = valor_ocr
            user_data.pop("valor_scanner", None)

        # --- RESTAURAÇÃO DE VALORES (Agora com campos definidos) ---
        if last_read_unit_id and last_read_unit_id in db_lista:
            if last_read_agua_value:
                txt_agua.value = last_read_agua_value
            if last_read_gas_value:
                txt_gas.value = last_read_gas_value

        # --- FUNÇÕES DE LÓGICA ---
        def exibir_concluido():
            lbl_modo.value = "TODAS AS UNIDADES LIDAS"
            lbl_modo.color = st.SUCCESS_GREEN
            img_icon.name = "check_circle"
            img_icon.color = st.SUCCESS_GREEN
            txt_unidade.visible = txt_agua.visible = txt_gas.visible = btn_gravar.visible = False
            btn_finalizar_sinc.visible = True
            page.update()

        def avancar():
            proxima = buscar_proxima_pendente()
            if proxima:
                txt_unidade.value = proxima
                txt_agua.value = ""
                txt_gas.value = ""
                page.update()
            else:
                exibir_concluido()

        def abrir_dialogo_gas():
            def fechar(escolha_gas):
                page.dialog.open = False
                if escolha_gas:
                    state["modo"] = "GAS"
                    unidade_atual = txt_unidade.value
                    # Extrai o andar (ex: "16" de "166" ou "163/164") para voltar ao início do hall
                    prefixo = unidade_atual[:2] if unidade_atual[0].isdigit() and len(
                        unidade_atual) >= 3 else ""
                    if prefixo:
                        idx_volta = next(i for i, u in enumerate(
                            db_lista) if u.startswith(prefixo))
                        txt_unidade.value = db_lista[idx_volta]
                else:
                    state["modo"] = "AGUA"

                atualizar_estilos_modo()
                if not escolha_gas:
                    avancar()

            page.dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("Hall Concluído"),
                content=ft.Text(
                    "Deseja realizar a leitura de GÁS deste andar?"),
                actions=[
                    ft.TextButton("Sim, ler Gás",
                                  on_click=lambda _: fechar(True)),
                    ft.TextButton("Não, próximo",
                                  on_click=lambda _: fechar(False)),
                ]
            )
            page.dialog.open = True
            page.update()

        async def salvar_clique(e):
            valor_agua = (txt_agua.value or "").replace(",", ".").strip()
            valor_gas = (txt_gas.value or "").replace(",", ".").strip()

            # Validação: Água é obrigatória (bloqueia o salvamento se vazio)
            if not valor_agua:
                page.snack_bar = ft.SnackBar(
                    ft.Text("A leitura de Água é obrigatória!"), bgcolor=st.RED_ERROR)
                page.snack_bar.open = True
                page.update()
                return

            current_unit = txt_unidade.value
            # Otimização para validação
            lidos = {l.get('unidade_id')
                     for l in Database.get_leituras_mes_atual()}

            # --- Validação da Unidade Anterior (Offline-First) ---
            current_unit_index = db_lista.index(current_unit)
            if current_unit_index > 0:  # If it's not the very first unit
                previous_unit = db_lista[current_unit_index - 1]
                if previous_unit not in lidos:
                    page.snack_bar = ft.SnackBar(
                        ft.Text(
                            f"Atenção: A unidade anterior ({previous_unit}) não foi lida. Por favor, siga a sequência."),
                        bgcolor=st.ACCENT_ORANGE
                    )
                    page.snack_bar.open = True
                    page.update()
                    return

            try:
                # Converte para float e garante 2 casas decimais (Padrão Renova)
                v_agua = round(float(valor_agua), 2)
                # Garante que 0.0 seja aceito e campos vazios virem None
                v_gas = round(float(valor_gas), 2) if (
                    valor_gas != "" and valor_gas is not None) else None
                # Padronização para ISO (YYYY-MM-DD) para busca correta no SQLite
                data_coleta = datetime.now(fuso_sp).isoformat(
                    sep=' ', timespec='seconds')
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
            # Update last read unit in page.user_data for resuming
            # Also store the values for potential restoration/clearing
            user_data["last_read_unit_id"] = current_unit
            user_data["last_read_agua_value"] = valor_agua
            user_data["last_read_gas_value"] = valor_gas

            if res["sucesso"]:
                img_icon.visible, icon_save.visible = False, True
                page.update()
                await asyncio.sleep(0.5)
                img_icon.visible, icon_save.visible = True, False

                # Lógica de transição de andar (Hall)
                idx_atual = db_lista.index(current_unit)
                proxima_unid = db_lista[idx_atual +
                                        1] if idx_atual + 1 < len(db_lista) else None

                # Detecta se o próximo item é de outro andar ou área comum
                prefixo_atual = current_unit[:2] if current_unit[0].isdigit() and len(
                    current_unit) >= 3 else "FIM"
                prefixo_prox = proxima_unid[:2] if proxima_unid and proxima_unid[0].isdigit(
                ) and len(proxima_unid) >= 3 else "FIM"

                if prefixo_atual != prefixo_prox and state["modo"] == "AGUA":
                    abrir_dialogo_gas()  # Oferece Gás antes de mudar de andar
                else:
                    avancar()
            # Ensure the clear button visibility is updated
            btn_limpar_ultima_leitura.visible = True
            page.update()

        # Sincroniza o estado visual inicial baseado no modo
        atualizar_estilos_modo()

        async def limpar_ultima_leitura(e):
            """Remove as chaves de última leitura do page.user_data e reseta os campos."""
            user_data.pop("last_read_unit_id", None)
            user_data.pop("last_read_agua_value", None)
            user_data.pop("last_read_gas_value", None)

            txt_unidade.value = db_lista[0] if db_lista else None
            txt_agua.value = ""
            txt_gas.value = ""
            btn_limpar_ultima_leitura.visible = False  # Hide button after clearing
            page.update()

        # Botão para limpar a última leitura, visível apenas se houver uma última leitura salva
        btn_limpar_ultima_leitura = ft.TextButton(
            "Limpar Última Leitura",
            icon="highlight_off",
            on_click=limpar_ultima_leitura,
            visible=user_data.get("last_read_unit_id") is not None
        )

        return ft.View(
            route="/medicao",
            bgcolor="#121417",
            appbar=ft.AppBar(
                title=ft.Text("Nova Medição"),
                center_title=True,
                leading=ft.IconButton("arrow_back",
                                      on_click=lambda _: page.go("/menu"))
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
                    ft.Container(height=5),
                    btn_limpar_ultima_leitura,
                    btn_gravar,
                    btn_finalizar_sinc,
                    btn_reiniciar_ciclo,
                    ft.TextButton("ABRIR SCANNER OCR", icon="camera_alt",
                                  on_click=lambda _: page.go("/scanner"))
                ], horizontal_alignment="center", alignment=ft.MainAxisAlignment.CENTER, expand=True)
            ]
        )
    except Exception as e:
        logging.error(e)
        enviar_report_erro(traceback.format_exc(), unidade="UI-MEDICAO")
        return ft.View(
            route="/medicao",
            controls=[ft.Text(
                f"Erro ao carregar tela de medição: {str(e)}", color="red")]
        )
