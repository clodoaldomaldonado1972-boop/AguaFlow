import flet as ft
import asyncio
import pytz
import logging
import traceback
from datetime import datetime
from database.database import Database
from database.sync_service import SyncService
import views.styles as st
from utils.auth_utils import validar_sessao
from utils.logger_config import enviar_report_erro

logger = logging.getLogger(__name__)


def _extrair_andar(unit: str) -> str:
    """Extrai o número do andar de qualquer formato de unidade do Vivere.

    Exemplos:
      '166'     → '16'   (andar 16, 3 chars)
      '96'      → '9'    (andar 9, 2 chars)
      '163/164' → '16'   (duplex andar 16)
      '23/24'   → '2'    (duplex andar 2)
      '11'      → '1'    (andar 1, 2 chars)
      'LAZER GÁS' → ''   (área comum, sem andar)
    """
    if not unit or not unit[0].isdigit():
        return ""
    digits = ""
    for c in unit:
        if c.isdigit():
            digits += c
        else:
            break
    return digits[:-1] if len(digits) >= 2 else ""


def _normalizar_unidade_scanner(codigo: str, db_lista: list) -> str:
    """Extrai ID da unidade de códigos de barras como 'AGUAFLOW|166-AGUA' → '166'.
    Tenta match exato primeiro, depois remove prefixo (antes de '|') e sufixo de tipo."""
    if codigo in db_lista:
        return codigo
    if '|' in codigo:
        codigo = codigo.split('|', 1)[1]
    if codigo in db_lista:
        return codigo
    if '-' in codigo:
        base = codigo.rsplit('-', 1)[0]
        if base in db_lista:
            return base
    return codigo


def montar_tela_medicao(page: ft.Page):
    auth_check = validar_sessao(page, "/medicao")
    if auth_check:
        return auth_check

    try:
        db_lista = Database._gerar_lista_unidades()
        fuso_sp = pytz.timezone('America/Sao_Paulo')

        class Unidade:
            def __init__(self, nome):
                self.nome = nome

        page.lista_unidades = [Unidade(u) for u in db_lista]

        user_data = getattr(page, "user_data", {}) or {}

        # ── SKILL Passo A: modo_ronda e estado inicial ────────────────────────
        modo_ronda = user_data.get("modo_ronda", "misto")  # 'agua', 'gas', 'misto'
        modo_selecionado = modo_ronda
        passo_leitura_atual = "agua" if modo_selecionado == "misto" else modo_selecionado
        unidades_concluidas_no_ciclo = set()

        # _modo_legado fica em sync com passo_leitura_atual para compatibilidade
        # com scanner (/scanner lê "AGUA"/"GAS" de page.user_data["modo_leitura"])
        _modo_legado = "AGUA" if modo_selecionado in ("agua", "misto") else "GAS"

        def _unidade_lida(unidade, lidos):
            """Verifica se unidade (ou partes duplex como '163/164') está em lidos."""
            if unidade in lidos:
                return True
            return any(p.strip() in lidos for p in unidade.split('/') if p.strip())

        def buscar_primeira_pendente():
            """Retorna a primeira unidade da lista que ainda não foi lida no mês atual."""
            try:
                leituras_mes = Database.get_leituras_mes_atual()
                if passo_leitura_atual == "agua" or modo_selecionado == "agua":
                    lidos = {l['unidade_id'] for l in leituras_mes if l.get('leitura_agua') is not None}
                else:
                    lidos = {l['unidade_id'] for l in leituras_mes if l.get('leitura_gas') is not None}
                for u in db_lista:
                    if not _unidade_lida(u, lidos):
                        return u
            except Exception:
                pass
            return None

        def buscar_proxima_pendente():
            """Busca a próxima unidade na lista que ainda não foi lida."""
            try:
                leituras_mes = Database.get_leituras_mes_atual()
                if passo_leitura_atual == "agua" or modo_selecionado == "agua":
                    lidos = {l['unidade_id'] for l in leituras_mes if l.get('leitura_agua') is not None}
                else:
                    lidos = {l['unidade_id'] for l in leituras_mes if l.get('leitura_gas') is not None}
                unidade_atual = txt_unidade.value
                idx_atual = db_lista.index(unidade_atual) if unidade_atual in db_lista else -1
                for i in range(idx_atual + 1, len(db_lista)):
                    if not _unidade_lida(db_lista[i], lidos):
                        return db_lista[i]
            except Exception:
                pass
            return None

        def _proxima_pendente_no_andar(andar: str, fase: str):
            """Próxima unidade NÃO lida no mesmo andar, após a unidade atual."""
            try:
                leituras_mes = Database.get_leituras_mes_atual()
                campo = 'leitura_agua' if fase == 'agua' else 'leitura_gas'
                lidos = {l['unidade_id'] for l in leituras_mes if l.get(campo) is not None}
                unidades_andar = [u for u in db_lista if _extrair_andar(u) == andar]
                unidade_atual = txt_unidade.value or ""
                try:
                    i = unidades_andar.index(unidade_atual)
                except ValueError:
                    i = -1
                for u in unidades_andar[i + 1:]:
                    if not _unidade_lida(u, lidos):
                        return u
            except Exception:
                pass
            return None

        def _primeira_pendente_no_andar(andar: str, fase: str):
            """Primeira unidade NÃO lida no andar (varredura completa da lista)."""
            try:
                leituras_mes = Database.get_leituras_mes_atual()
                campo = 'leitura_agua' if fase == 'agua' else 'leitura_gas'
                lidos = {l['unidade_id'] for l in leituras_mes if l.get(campo) is not None}
                for u in db_lista:
                    if _extrair_andar(u) == andar and not _unidade_lida(u, lidos):
                        return u
            except Exception:
                pass
            return None

        # ── Restauração de estado (scanner / client_storage / processo Android) ─
        unidade_retorno_scanner = user_data.pop("unidade_atual_medicao", None)
        modo_retorno = user_data.pop("modo_leitura", None)
        if modo_retorno in ("AGUA", "GAS"):
            _modo_legado = modo_retorno
            passo_leitura_atual = "agua" if modo_retorno == "AGUA" else "gas"

        _cs_unidade = None
        if modo_retorno not in ("AGUA", "GAS"):
            try:
                _andar_gas_pendente = page.client_storage.get("medicao_gas_pendente_andar")
                if _andar_gas_pendente:
                    _modo_legado = "GAS"
                    passo_leitura_atual = "gas"
                    idx_gas = next(
                        (i for i, u in enumerate(db_lista)
                         if _extrair_andar(u) == _andar_gas_pendente),
                        None
                    )
                    if idx_gas is not None:
                        _cs_unidade = db_lista[idx_gas]
                    page.client_storage.remove("medicao_gas_pendente_andar")
                else:
                    _cs_modo = page.client_storage.get("medicao_modo")
                    _cs_unidade = page.client_storage.get("medicao_unidade")
                    if _cs_modo in ("AGUA", "GAS"):
                        _modo_legado = _cs_modo
                        passo_leitura_atual = "agua" if _cs_modo == "AGUA" else "gas"
            except Exception:
                pass

        proxima_pendente = buscar_primeira_pendente()
        initial_unit_value = proxima_pendente if proxima_pendente else (
            db_lista[0] if db_lista else None)
        if unidade_retorno_scanner and unidade_retorno_scanner in db_lista:
            initial_unit_value = unidade_retorno_scanner
        elif _cs_unidade and _cs_unidade in db_lista:
            try:
                _leituras_cs = Database.get_leituras_mes_atual()
                if passo_leitura_atual == "agua":
                    _cs_lidos = {l['unidade_id'] for l in _leituras_cs
                                 if l.get('leitura_agua') is not None}
                else:
                    _cs_lidos = {l['unidade_id'] for l in _leituras_cs
                                 if l.get('leitura_gas') is not None}
                if not _unidade_lida(_cs_unidade, _cs_lidos):
                    initial_unit_value = _cs_unidade
            except Exception:
                pass

        # ── Widgets visuais ───────────────────────────────────────────────────
        _agua_init = (passo_leitura_atual == "agua")
        _cor_init = "blue" if _agua_init else "orange"

        img_icon = ft.Icon(
            ft.Icons.WATER_DROP if _agua_init else ft.Icons.LOCAL_FIRE_DEPARTMENT,
            color=_cor_init, size=140
        )
        icon_save = ft.Icon(ft.Icons.SAVE, color="green", size=140, visible=False)
        lbl_modo = ft.Text(
            "MODO: ÁGUA" if _agua_init else "MODO: GÁS",
            color=_cor_init, weight="bold", size=22
        )
        btn_trocar_modo = ft.TextButton(
            "trocar", icon=ft.Icons.SWAP_HORIZ,
            style=ft.ButtonStyle(color="grey60"),
            visible=False,
        )

        # SKILL Passo A: barra de progresso
        lbl_progresso_status = ft.Text(
            value="Calculando progresso...",
            size=14, weight=ft.FontWeight.W_500, color="bluegray"
        )
        bar_progresso = ft.ProgressBar(
            value=0.0, width=300, color="green", bgcolor="lightgreen"
        )

        # Progresso inicial
        if initial_unit_value and db_lista:
            _pi = (db_lista.index(initial_unit_value) + 1) if initial_unit_value in db_lista else 0
            _pt = len(db_lista)
            bar_progresso.value = _pi / _pt if _pt > 0 else 0
            _pr = _pt - _pi
            lbl_progresso_status.value = (
                "Última unidade!" if _pr == 0
                else f"Progresso: {_pi}/{_pt} (Faltam {_pr} unidades)"
            )

        txt_unidade = ft.Dropdown(
            label="Unidade",
            options=[ft.dropdown.Option(u) for u in db_lista],
            width=320,
            value=initial_unit_value,
            border_color=_cor_init,
        )
        txt_unidade.on_change = lambda e: _atualizar_campos_unidade(e.control.value)

        txt_agua = ft.TextField(
            label="Leitura Água (m³)",
            prefix_icon="water_drop",
            width=320,
            keyboard_type=ft.KeyboardType.NUMBER,
            input_filter=ft.InputFilter(
                allow=True, regex_string=r"^\d{0,5}([,\.]\d{0,2})?$"),
            text_align=ft.TextAlign.CENTER,
            hint_text="00000,00",
            color="white",
            border_color="blue",
            visible=_agua_init,
            disabled=not _agua_init
        )

        txt_gas = ft.TextField(
            label="Leitura Gás (m³)",
            icon="local_fire_department",
            width=320,
            keyboard_type=ft.KeyboardType.NUMBER,
            input_filter=ft.InputFilter(
                allow=True, regex_string=r"^\d{0,5}([,\.]\d{0,3})?$"),
            text_align=ft.TextAlign.CENTER,
            hint_text="00000,000",
            color="white",
            border_color="orange",
            visible=not _agua_init,
            disabled=_agua_init
        )

        btn_gravar = ft.ElevatedButton(
            "GRAVAR LEITURA",
            on_click=lambda e: page.run_task(salvar_clique, e),
            width=320,
            height=65
        )

        # SKILL Passo A: dialog_barreira
        # content é mutável: o texto é atualizado dinamicamente antes de abrir
        _barreira_texto = ft.Text("Detectamos apartamentos não medidos neste andar.")
        dialog_barreira = ft.AlertDialog(
            title=ft.Text("Esqueceu de ler algum apartamento?"),
            content=_barreira_texto,
            actions=[
                ft.TextButton("Voltar e Medir",
                               on_click=lambda e: _fechar_barreira(voltar=True)),
                ft.TextButton("Seguir (Salvar como Nulo)",
                               on_click=lambda e: _fechar_barreira(voltar=False)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        # ── Funções auxiliares ────────────────────────────────────────────────

        def _mostrar_snack(msg, is_error=False):
            page.snack_bar = ft.SnackBar(
                ft.Text(msg), bgcolor=st.RED_ERROR if is_error else None)
            page.snack_bar.open = True
            page.update()

        def _persistir_estado():
            try:
                page.client_storage.set("medicao_modo", _modo_legado)
                page.client_storage.set("medicao_unidade", txt_unidade.value or "")
            except Exception:
                pass

        def _limpar_estado_persistido():
            try:
                page.client_storage.remove("medicao_modo")
                page.client_storage.remove("medicao_unidade")
                page.client_storage.remove("medicao_gas_pendente_andar")
            except Exception:
                pass

        def exibir_concluido():
            _limpar_estado_persistido()
            lbl_modo.value = "TODAS AS UNIDADES LIDAS"
            lbl_modo.color = st.SUCCESS_GREEN
            img_icon.icon = ft.Icons.CHECK_CIRCLE
            img_icon.color = st.SUCCESS_GREEN
            lbl_progresso_status.value = "Ciclo completo!"
            bar_progresso.value = 1.0
            txt_unidade.visible = txt_agua.visible = txt_gas.visible = btn_gravar.visible = False
            btn_finalizar_sinc.visible = True
            page.update()

        def _carregar_proxima_unidade():
            proxima = buscar_proxima_pendente()
            if proxima:
                txt_unidade.value = proxima
                txt_agua.value = ""
                txt_gas.value = ""
                _persistir_estado()
                _atualizar_campos_unidade(proxima)
            else:
                exibir_concluido()

        # SKILL Passo B: exibição condicional de campos e progresso
        def _atualizar_campos_unidade(unidade_nome):
            nonlocal passo_leitura_atual, _modo_legado
            if not unidade_nome:
                return
            nome_unidade_upper = unidade_nome.upper()
            txt_agua.visible = False
            txt_gas.visible = False

            if "LAZER GÁS" in nome_unidade_upper or "LAZER GAS" in nome_unidade_upper:
                if modo_selecionado in ["gas", "misto"]:
                    passo_leitura_atual = "gas"
                    txt_gas.visible = True
                    txt_gas.disabled = False
                    txt_gas.label = "Leitura do Gás (Lazer - LAO 3 Casas)"
                else:
                    _avancar_proxima_unidade_com_seguranca()
                    return

            elif "TERREO GERAL" in nome_unidade_upper:
                if modo_selecionado in ["agua", "misto"]:
                    passo_leitura_atual = "agua"
                    txt_agua.visible = True
                    txt_agua.disabled = False
                    txt_agua.label = "Leitura da Água (Térreo Geral - LAO 1 Casa)"
                else:
                    _avancar_proxima_unidade_com_seguranca()
                    return

            else:
                if passo_leitura_atual == "agua":
                    txt_agua.visible = True
                    txt_agua.disabled = False
                    txt_agua.label = f"Leitura da Água - {unidade_nome} (Renova 2 Casas)"
                elif passo_leitura_atual == "gas":
                    txt_gas.visible = True
                    txt_gas.disabled = False
                    txt_gas.label = f"Leitura do Gás - {unidade_nome} (LAO 3 Casas)"

            # Sync _modo_legado e visual com passo atual
            if passo_leitura_atual == "agua":
                _modo_legado = "AGUA"
                lbl_modo.value = "MODO: ÁGUA"
                lbl_modo.color = "blue"
                img_icon.icon = ft.Icons.WATER_DROP
                img_icon.color = "blue"
                txt_unidade.border_color = "blue"
            else:
                _modo_legado = "GAS"
                lbl_modo.value = "MODO: GÁS"
                lbl_modo.color = "orange"
                img_icon.icon = ft.Icons.LOCAL_FIRE_DEPARTMENT
                img_icon.color = "orange"
                txt_unidade.border_color = "orange"

            # Barra de progresso horizontal
            try:
                if hasattr(page, "lista_unidades") and len(page.lista_unidades) > 0:
                    total = len(page.lista_unidades)
                    atual_idx = 0
                    for idx, u in enumerate(page.lista_unidades):
                        if u.nome == unidade_nome:
                            atual_idx = idx + 1
                            break
                    restantes = total - atual_idx
                    bar_progresso.value = atual_idx / total
                    lbl_progresso_status.value = (
                        "Última unidade!" if restantes == 0
                        else f"Progresso: {atual_idx}/{total} (Faltam {restantes} unidades)"
                    )
            except Exception as e:
                logger.error(f"Erro ao atualizar barra de progresso: {e}")

            page.update()

        # SKILL Passo C: barreira de segurança do andar
        def _avancar_proxima_unidade_com_seguranca():
            nonlocal passo_leitura_atual
            unidade_atual_nome = txt_unidade.value
            andar_atual = _extrair_andar(unidade_atual_nome or "")

            # Áreas comuns ou andar indeterminado: avança direto sem barreira
            if (not andar_atual
                    or "LAZER" in (unidade_atual_nome or "").upper()
                    or "TERREO" in (unidade_atual_nome or "").upper()):
                passo_leitura_atual = "agua" if modo_selecionado == "misto" else modo_selecionado
                _carregar_proxima_unidade()
                return

            # Peek na próxima unidade pendente — barreira só dispara em troca de andar
            proxima = buscar_proxima_pendente()
            andar_proximo = _extrair_andar(proxima) if proxima else ""

            if andar_proximo == andar_atual:
                # Ainda no mesmo andar — avança sem verificar barreira
                passo_leitura_atual = "agua" if modo_selecionado == "misto" else modo_selecionado
                _carregar_proxima_unidade()
                return

            # Mudança de andar (ou fim de ciclo) — verifica se o andar atual foi varrido
            unidades_do_andar = [
                u for u in page.lista_unidades if _extrair_andar(u.nome) == andar_atual
            ]
            total_esperado_andar = len(unidades_do_andar)
            concluidas_do_andar = [
                u for u in unidades_do_andar if u.nome in unidades_concluidas_no_ciclo
            ]

            if len(concluidas_do_andar) < total_esperado_andar:
                faltam = total_esperado_andar - len(concluidas_do_andar)
                _barreira_texto.value = (
                    f"Detectamos que {faltam} apartamento(s) do andar {andar_atual} "
                    "ainda não foram medidos."
                )
                page.dialog = dialog_barreira
                dialog_barreira.open = True
                page.update()
            else:
                passo_leitura_atual = "agua" if modo_selecionado == "misto" else modo_selecionado
                _carregar_proxima_unidade()

        def _fechar_barreira(voltar: bool):
            nonlocal passo_leitura_atual
            dialog_barreira.open = False
            page.update()

            if voltar:
                _mostrar_snack("Retorne e finalize as unidades restantes do andar corrente.")
            else:
                unidade_atual_nome = txt_unidade.value
                andar_atual = _extrair_andar(unidade_atual_nome or "")
                unidades_do_andar = [
                    u for u in page.lista_unidades if _extrair_andar(u.nome) == andar_atual
                ]
                leiturista = user_data.get("nome") or user_data.get("email", "Zelador")

                for u in unidades_do_andar:
                    if u.nome not in unidades_concluidas_no_ciclo:
                        try:
                            Database.salvar_leitura(
                                u.nome, None, None,
                                modo_selecionado.upper(),
                                datetime.now(fuso_sp).isoformat(),
                                None, leiturista
                            )
                            unidades_concluidas_no_ciclo.add(u.nome)
                        except Exception as e:
                            logger.error(f"Erro ao salvar unidade pulada automaticamente: {e}")

                _mostrar_snack("Unidades omitidas salvas como nulas. Avançando...")
                passo_leitura_atual = "agua" if modo_selecionado == "misto" else modo_selecionado
                _carregar_proxima_unidade()

        # ── Avanço modo MISTO: todas as águas do andar → todos os gás do andar ──
        def _avancar_misto():
            nonlocal passo_leitura_atual
            unidade_atual_nome = txt_unidade.value or ""
            andar_atual = _extrair_andar(unidade_atual_nome)
            txt_agua.value = ""
            txt_gas.value = ""

            # Áreas comuns sem andar (LAZER GÁS, TERREO GERAL): usa lógica padrão
            if not andar_atual:
                _avancar_proxima_unidade_com_seguranca()
                return

            if passo_leitura_atual == "agua":
                # Ainda tem água pendente no mesmo andar?
                prox = _proxima_pendente_no_andar(andar_atual, "agua")
                if prox:
                    txt_unidade.value = prox
                    _persistir_estado()
                    _atualizar_campos_unidade(prox)
                    return
                # Água do andar concluída → inicia fase gás a partir da 1ª unidade do andar
                primeira_gas = _primeira_pendente_no_andar(andar_atual, "gas")
                if primeira_gas:
                    passo_leitura_atual = "gas"
                    txt_unidade.value = primeira_gas
                    _persistir_estado()
                    _atualizar_campos_unidade(primeira_gas)
                else:
                    # Andar sem gás (não ocorre no prédio, mas por segurança)
                    passo_leitura_atual = "agua"
                    _avancar_proxima_unidade_com_seguranca()
            else:
                # Ainda tem gás pendente no mesmo andar?
                prox = _proxima_pendente_no_andar(andar_atual, "gas")
                if prox:
                    txt_unidade.value = prox
                    _persistir_estado()
                    _atualizar_campos_unidade(prox)
                    return
                # Gás do andar concluído → marca todas as unidades do andar e avança
                for u in page.lista_unidades:
                    if _extrair_andar(u.nome) == andar_atual:
                        unidades_concluidas_no_ciclo.add(u.nome)
                passo_leitura_atual = "agua"
                _avancar_proxima_unidade_com_seguranca()

        # ── Componentes de conclusão ──────────────────────────────────────────

        async def finalizar_e_gerar_relatorio(e):
            btn_finalizar_sinc.disabled = True
            btn_finalizar_sinc.text = "SINCRONIZANDO..."
            page.update()

            qtd = await SyncService.executar_sincronismo_manual()

            from relatorio_engine import RelatorioEngine
            dados = await asyncio.to_thread(Database.get_leituras_mes_atual)
            leiturista = user_data.get("nome") or user_data.get("email", "Zelador")

            msg_relatorio = ""
            if dados:
                arquivos = await asyncio.to_thread(
                    RelatorioEngine.gerar_todos, dados, leiturista)
                sucesso_email, msg_email = await asyncio.to_thread(
                    RelatorioEngine.enviar_relatorios_por_email, arquivos)
                msg_relatorio = f" | {msg_email}"

            page.show_dialog(ft.SnackBar(
                ft.Text(f"✅ {qtd} leituras sincronizadas e relatórios gerados!{msg_relatorio}")))
            btn_finalizar_sinc.visible = False
            btn_reiniciar_ciclo.visible = True
            page.update()

        async def reiniciar_sistema(e):
            SyncService.limpar_leituras_locais()
            user_data["last_read_unit_id"] = None
            await page.push_route("/menu")

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

        # Recuperação de dados do Scanner
        unidade_ocr = user_data.get("unidade_scanner")
        valor_ocr = user_data.get("valor_scanner")
        ocr_status_scanner = user_data.pop("ocr_status_scanner", None)

        if unidade_ocr:
            unidade_ocr = _normalizar_unidade_scanner(unidade_ocr, db_lista)
            if unidade_ocr in db_lista:
                txt_unidade.value = unidade_ocr
            user_data.pop("unidade_scanner", None)
        if valor_ocr:
            if passo_leitura_atual == "agua":
                txt_agua.value = valor_ocr
            else:
                txt_gas.value = valor_ocr
            user_data.pop("valor_scanner", None)

        if ocr_status_scanner in ("offline",) and not valor_ocr:
            async def _aviso_sem_conexao():
                await asyncio.sleep(0.4)
                try:
                    page.show_snack_bar(ft.SnackBar(
                        ft.Row([
                            ft.Icon(ft.Icons.WIFI_OFF, color="white", size=20),
                            ft.Text(
                                "  Sem conexão — insira o valor manualmente",
                                color="white", size=14,
                            ),
                        ]),
                        bgcolor="#b71c1c",
                        duration=5000,
                        show_close_icon=True,
                    ))
                    page.update()
                except Exception:
                    pass
            asyncio.create_task(_aviso_sem_conexao())

        # SKILL Passo D: lógica de salvamento com barreira integrada
        async def salvar_clique(e):
            nonlocal passo_leitura_atual

            unidade_nome = txt_unidade.value
            if not unidade_nome:
                _mostrar_snack("Selecione uma unidade.", is_error=True)
                return
            nome_unidade_upper = unidade_nome.upper()

            # Validação do campo obrigatório
            if passo_leitura_atual == "agua":
                raw_val = (txt_agua.value or "").strip()
                if not raw_val:
                    _mostrar_snack("A leitura de ÁGUA é obrigatória para este passo!", is_error=True)
                    return
            elif passo_leitura_atual == "gas":
                raw_val = (txt_gas.value or "").strip()
                if not raw_val:
                    _mostrar_snack("A leitura de GÁS é obrigatória para este passo!", is_error=True)
                    return
            else:
                return

            # Validação de sequência
            if unidade_nome not in db_lista:
                _mostrar_snack(f"Unidade '{unidade_nome}' não encontrada na lista.", is_error=True)
                return
            current_unit_index = db_lista.index(unidade_nome)
            if current_unit_index > 0:
                previous_unit = db_lista[current_unit_index - 1]
                _all_leituras = await asyncio.to_thread(Database.get_leituras_mes_atual)
                if passo_leitura_atual == "agua":
                    lidos = {l.get('unidade_id') for l in _all_leituras
                             if l.get('leitura_agua') is not None}
                else:
                    lidos = {l.get('unidade_id') for l in _all_leituras
                             if l.get('leitura_gas') is not None}
                if not _unidade_lida(previous_unit, lidos):
                    page.snack_bar = ft.SnackBar(
                        ft.Text(
                            f"Atenção: A unidade anterior ({previous_unit}) não foi lida."
                            " Por favor, siga a sequência."),
                        bgcolor=st.ACCENT_ORANGE, show_close_icon=True)
                    page.snack_bar.open = True
                    page.update()
                    return

            # Conversão e arredondamento
            try:
                v_agua = None
                v_gas = None
                if passo_leitura_atual == "agua":
                    v_agua = round(float(raw_val.replace(",", ".")), 2)
                else:
                    v_gas = round(float(raw_val.replace(",", ".")), 3)
            except ValueError:
                _mostrar_snack("Valor inválido.", is_error=True)
                return

            foto_url = user_data.pop("foto_url_scanner", None)
            leiturista = user_data.get("nome") or user_data.get("email", "Zelador")
            data_coleta = datetime.now(fuso_sp).isoformat(sep=' ', timespec='seconds')

            res = await asyncio.to_thread(
                Database.salvar_leitura,
                unidade_nome, v_agua, v_gas, _modo_legado, data_coleta, foto_url, leiturista
            )

            if not res["sucesso"]:
                err_str = str(res.get("erro", ""))
                if "registro_unico_unidade_coleta" in err_str:
                    _mostrar_snack("Esta medição já foi registrada nesta rodada!", is_error=True)
                else:
                    _mostrar_snack(f"Erro: {err_str}", is_error=True)
                return

            user_data["last_read_unit_id"] = unidade_nome
            _persistir_estado()
            _mostrar_snack(f"Gravado: {passo_leitura_atual.upper()} de {unidade_nome}")

            # Animação de ícone salvo (não-bloqueante)
            async def _restaurar_icone():
                await asyncio.sleep(0.3)
                try:
                    img_icon.visible, icon_save.visible = True, False
                    page.update()
                except Exception:
                    pass
            img_icon.visible, icon_save.visible = False, True
            page.update()
            asyncio.create_task(_restaurar_icone())

            # Rastreio de unidades concluídas no ciclo
            if modo_selecionado in ["agua", "gas"] or (
                    modo_selecionado == "misto" and passo_leitura_atual == "gas"):
                unidades_concluidas_no_ciclo.add(unidade_nome)

            # Lógica de avanço conforme modo selecionado (SKILL Passo D)
            if modo_selecionado == "misto":
                # Áreas comuns: LAZER GÁS e TERREO GERAL avançam direto
                if ("LAZER GÁS" in nome_unidade_upper or "LAZER GAS" in nome_unidade_upper
                        or "TERREO GERAL" in nome_unidade_upper):
                    unidades_concluidas_no_ciclo.add(unidade_nome)
                    _avancar_proxima_unidade_com_seguranca()
                else:
                    # Modo misto: todas as águas do andar → todos os gás do andar
                    _avancar_misto()
            else:
                _avancar_proxima_unidade_com_seguranca()

            btn_limpar_ultima_leitura.visible = True
            page.update()

        def _abrir_scanner():
            user_data.update({
                "modo_leitura": _modo_legado,
                "unidade_atual_medicao": txt_unidade.value,
            })
            _persistir_estado()
            page.go("/scanner")

        async def limpar_ultima_leitura(e):
            user_data.pop("last_read_unit_id", None)
            user_data.pop("last_read_agua_value", None)
            user_data.pop("last_read_gas_value", None)
            txt_unidade.value = db_lista[0] if db_lista else None
            txt_agua.value = ""
            txt_gas.value = ""
            btn_limpar_ultima_leitura.visible = False
            page.update()

        btn_limpar_ultima_leitura = ft.TextButton(
            "Limpar Última Leitura",
            icon="highlight_off",
            on_click=limpar_ultima_leitura,
            visible=user_data.get("last_read_unit_id") is not None
        )

        # ── Seletor de modo da ronda ──────────────────────────────────────────
        def _trocar_modo(e):
            nonlocal modo_selecionado, passo_leitura_atual, _modo_legado
            novo_modo = e.control.value
            if novo_modo not in ("agua", "gas", "misto"):
                return
            modo_selecionado = novo_modo
            passo_leitura_atual = "agua" if novo_modo in ("agua", "misto") else "gas"
            _modo_legado = "AGUA" if novo_modo in ("agua", "misto") else "GAS"
            user_data["modo_ronda"] = novo_modo
            txt_agua.value = ""
            txt_gas.value = ""
            # Colapsa o seletor após a escolha
            seletor_modo.visible = False
            btn_trocar_modo.visible = True
            if txt_unidade.value:
                _atualizar_campos_unidade(txt_unidade.value)
            else:
                page.update()

        def _reabrir_seletor(e):
            seletor_modo.visible = True
            btn_trocar_modo.visible = False
            page.update()

        seletor_modo = ft.RadioGroup(
            value=modo_selecionado,
            content=ft.Row([
                ft.Radio(value="agua",  label="ÁGUA",
                         label_style=ft.TextStyle(color="lightblue", weight=ft.FontWeight.BOLD)),
                ft.Radio(value="gas",   label="GÁS",
                         label_style=ft.TextStyle(color="orange", weight=ft.FontWeight.BOLD)),
                ft.Radio(value="misto", label="MISTO",
                         label_style=ft.TextStyle(color="white", weight=ft.FontWeight.BOLD)),
            ], alignment=ft.MainAxisAlignment.CENTER),
        )
        seletor_modo.on_change = _trocar_modo
        btn_trocar_modo.on_click = _reabrir_seletor

        # SKILL Passo E: layout com barra de progresso acima de txt_unidade
        return ft.View(
            route="/medicao",
            bgcolor="#121417",
            appbar=ft.AppBar(
                title=ft.Text("Nova Medição"),
                center_title=True,
                leading=ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    on_click=lambda _: page.go("/menu")
                )
            ),
            controls=[
                ft.Column([
                    ft.Container(
                        content=ft.Stack([img_icon, icon_save]),
                        alignment=ft.alignment.Alignment(0, 0),
                        width=320,
                        height=160
                    ),
                    ft.Row([lbl_modo, btn_trocar_modo],
                           alignment=ft.MainAxisAlignment.CENTER,
                           tight=True),
                    seletor_modo,
                    lbl_progresso_status,   # SKILL Passo E
                    bar_progresso,          # SKILL Passo E
                    txt_unidade,
                    txt_agua,
                    txt_gas,
                    ft.Container(height=5),
                    btn_limpar_ultima_leitura,
                    btn_gravar,
                    btn_finalizar_sinc,
                    btn_reiniciar_ciclo,
                    ft.TextButton(
                        "ABRIR SCANNER",
                        icon="qr_code_scanner",
                        on_click=lambda _: _abrir_scanner()
                    )
                ], horizontal_alignment="center", spacing=10,
                   scroll=ft.ScrollMode.AUTO,
                   expand=True)
            ]
        )
    except Exception as e:
        logging.error(e)
        enviar_report_erro(traceback.format_exc(), unidade="CARREGAMENTO_MEDICAO")
        return ft.View(
            route="/medicao",
            controls=[ft.Text(
                f"Erro ao carregar tela de medição: {str(e)}", color="red")]
        )
