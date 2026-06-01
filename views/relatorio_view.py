import flet as ft
import asyncio
import gc
import csv
import os
from datetime import datetime
from database.database import Database
from views import styles as st
from database.gestao_periodos import finalizar_mes_e_enviar
from utils.export_manager import ExportManager, EXPORT_AVAILABLE
from utils.auth_utils import validar_sessao

try:
    from utils.report_generator import ReportGenerator
    _REPORT_OK = True
except Exception:
    _REPORT_OK = False


def montar_tela_relatorio(page: ft.Page):
    # Proteção de Rota
    auth_check = validar_sessao(page, "/relatorios")
    if auth_check:
        return auth_check

    # --- 1. ELEMENTOS DE FEEDBACK VISUAL ---
    lbl_status = ft.Text("Pronto para processar", color="grey700", size=14)
    pr = ft.ProgressBar(width=300, visible=False, color=st.PRIMARY_BLUE)

    async def acao_gerar_qrs(tipo):
        if not EXPORT_AVAILABLE:
            page.show_dialog(ft.SnackBar(
                ft.Text("reportlab não instalado. Execute: pip install reportlab"),
                bgcolor="orange900",
            ))
            page.update()
            return
        lbl_status.value = f"⏳ Gerando etiquetas de {tipo} (50 por folha)..."
        lbl_status.color = "grey700"
        pr.visible = True
        page.update()
        try:
            await asyncio.sleep(0.1)
            unidades = Database._gerar_lista_unidades()
            caminho_pdf = ExportManager.gerar_etiquetas_qr_50_por_folha(
                unidades, tipo_medidor=tipo)
            lbl_status.value = f"✅ PDF de {tipo} gerado: {caminho_pdf}"
            lbl_status.color = "green"
        except Exception as ex:
            lbl_status.value = f"❌ Erro: {str(ex)}"
            lbl_status.color = "red"
        pr.visible = False
        gc.collect()
        page.update()

    async def acao_virada_ciclo(_):
        lbl_status.value = "⏳ Executando virada de ciclo e envio de relatórios..."
        lbl_status.color = "grey700"
        pr.visible = True
        page.update()
        try:
            ok = await asyncio.to_thread(finalizar_mes_e_enviar)
            if ok:
                lbl_status.value = "✅ Ciclo finalizado com sucesso e banco preparado para o próximo mês."
                lbl_status.color = "green"
            else:
                lbl_status.value = "⚠️ Não foi possível finalizar o ciclo. Verifique backup, dados e e-mail."
                lbl_status.color = st.ACCENT_ORANGE
        except Exception as ex:
            lbl_status.value = f"❌ Erro na virada de ciclo: {ex}"
            lbl_status.color = "red"
        gc.collect()  # Liberar memória após virada de ciclo
        pr.visible = False
        page.update()

    # --- SEÇÃO: RELATÓRIO POR UNIDADE ---
    unidades = ["Todas"] + Database._gerar_lista_unidades()
    hoje = datetime.now()
    meses_disp = []
    for i in range(6):
        from datetime import timedelta
        ref = datetime(hoje.year, hoje.month, 1) - timedelta(days=i * 30)
        meses_disp.append(ref.strftime("%Y-%m"))

    dd_unid = ft.Dropdown(
        label="Unidade",
        options=[ft.dropdown.Option(u) for u in unidades],
        value="Todas",
        width=200,
        text_size=13,
    )
    dd_mes_unid = ft.Dropdown(
        label="Mês",
        options=[ft.dropdown.Option(m) for m in meses_disp],
        value=meses_disp[0],
        width=140,
        text_size=13,
    )
    lbl_unid_status = ft.Text("", size=12, color="grey")

    async def acao_relatorio_unidade(_):
        unidade_sel = dd_unid.value
        mes_sel = dd_mes_unid.value
        lbl_unid_status.value = "⏳ Gerando..."
        lbl_unid_status.color = "grey"
        page.update()

        try:
            dados = await asyncio.to_thread(
                Database.buscar_leituras_filtradas,
                None,
                None if unidade_sel == "Todas" else unidade_sel,
                mes_sel,
            )
            if not dados:
                lbl_unid_status.value = "⚠️ Nenhuma leitura encontrada para o período."
                lbl_unid_status.color = st.ACCENT_ORANGE
                page.update()
                return

            for row in dados:
                row.setdefault("unidade", row.get("unidade_id", "?"))
                row.setdefault("data_leitura_atual", row.get("data_hora_coleta", ""))

            titulo = f"Relatório — {unidade_sel} — {mes_sel}"
            os.makedirs("relatorios", exist_ok=True)
            caminhos = []

            if _REPORT_OK and EXPORT_AVAILABLE:
                caminho_pdf = await asyncio.to_thread(ReportGenerator.gerar_pdf, dados, titulo)
                if caminho_pdf:
                    caminhos.append(caminho_pdf)

            nome_csv = f"relatorio_{unidade_sel.replace('/', '_')}_{mes_sel}.csv"
            caminho_csv = os.path.join("relatorios", nome_csv)
            with open(caminho_csv, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=dados[0].keys())
                writer.writeheader()
                writer.writerows(dados)
            caminhos.append(caminho_csv)

            msg_caminhos = ", ".join(os.path.basename(c) for c in caminhos)
            lbl_unid_status.value = f"✅ Gerado: {msg_caminhos}"
            lbl_unid_status.color = "green"
        except Exception as ex:
            lbl_unid_status.value = f"❌ Erro: {ex}"
            lbl_unid_status.color = st.RED_ERROR
        gc.collect()
        page.update()

    secao_unidade = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.DESCRIPTION, color=st.ACCENT_ORANGE, size=30),
                ft.Text("RELATÓRIO POR UNIDADE", size=16, weight="bold", color="white"),
            ], spacing=8),
            ft.Row([dd_unid, dd_mes_unid], spacing=8, wrap=True),
            lbl_unid_status,
            ft.ElevatedButton(
                "GERAR RELATÓRIO",
                icon=ft.Icons.FILE_DOWNLOAD,
                on_click=lambda _: page.run_task(acao_relatorio_unidade, _),
                style=ft.ButtonStyle(
                    bgcolor=st.ACCENT_ORANGE, color="white",
                    shape=ft.RoundedRectangleBorder(radius=12),
                ),
                width=280, height=48,
            ),
            ft.Text(
                "CSV sempre disponível. PDF requer desktop.",
                size=11, color="grey", italic=True,
            ),
        ], spacing=8),
        padding=20,
        bgcolor="#1E2126",
        border_radius=15,
    )

    # ── CONTEÚDO SCROLLÁVEL DA VIEW ──────────────────────────────────────────
    # Centraliza o conteúdo dentro de uma coluna expansível e força a exibição da barra vertical
    coluna_conteudo = ft.Column(
        [
            ft.Container(height=10),
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.RECYCLING, size=50, color=st.PRIMARY_BLUE),
                    ft.Text("FINALIZAR MÊS ATUAL", size=18, weight="bold", color="white"),
                    pr, lbl_status,
                    ft.ElevatedButton(
                        "EXECUTAR VIRADA DE CICLO",
                        icon="play_circle_fill",
                        on_click=acao_virada_ciclo,
                        style=st.BTN_MAIN, width=320, height=55
                    ),
                ], horizontal_alignment="center"),
                padding=20, bgcolor="#1E2126", border_radius=15
            ),
            ft.Divider(height=25, color="white10"),
            secao_unidade,
            ft.Divider(height=25, color="white10"),
            ft.Text("IMPRESSÃO DE ETIQUETAS (50/FOLHA)", size=14, weight="bold", color="white"),
            ft.Row([
                ft.ElevatedButton(
                    "QR ÁGUA", icon="water",
                    on_click=lambda _: page.run_task(acao_gerar_qrs, "Água"),
                    expand=True
                ),
                ft.ElevatedButton(
                    "QR GÁS", icon="local_fire_department",
                    on_click=lambda _: page.run_task(acao_gerar_qrs, "Gás"),
                    expand=True, bgcolor="orange900", color="white"
                ),
            ], spacing=10),
            ft.Container(height=15),
            ft.TextButton("Voltar ao Menu Principal", on_click=lambda _: page.go("/menu")),
            ft.Container(height=20),
        ],
        scroll=ft.ScrollMode.ALWAYS, # Força a aparição da barra de rolagem na direita
        spacing=15,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        expand=True # Obriga a coluna a preencher a View inteira habilitando o cálculo geométrico do scroll
    )

    return ft.View(
        route="/relatorios",
        bgcolor=st.BG_DARK,
        appbar=ft.AppBar(
            title=ft.Text("Relatórios e Etiquetas"),
            bgcolor=st.PRIMARY_BLUE,
            leading=ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=lambda _: page.go("/menu"))
        ),
        # Passa a coluna expansível com ScrollMode configurado diretamente no gerenciador de controles
        controls=[coluna_conteudo]
    )