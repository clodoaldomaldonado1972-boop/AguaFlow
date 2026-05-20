import flet as ft
from datetime import datetime, timedelta
from database.database import Database
import views.styles as st
from utils.auth_utils import validar_sessao


async def montar_tela_historico(page: ft.Page):
    auth_check = validar_sessao(page, "/historico")
    if auth_check:
        return auth_check

    unidades = ["Todas"] + Database._gerar_lista_unidades()

    # Últimos 6 meses para o filtro
    hoje = datetime.now()
    meses = []
    for i in range(6):
        ref = datetime(hoje.year, hoje.month, 1) - timedelta(days=i * 30)
        meses.append(ref.strftime("%Y-%m"))

    filtros = {"texto": "", "unidade": "Todas", "mes": meses[0]}

    lista_col = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True, spacing=4)
    lbl_total = ft.Text("", size=12, color=st.GREY_TEXT)

    def carregar_leituras():
        dados = Database.buscar_leituras_filtradas(
            texto=filtros["texto"] or None,
            unidade=filtros["unidade"] if filtros["unidade"] != "Todas" else None,
            mes=filtros["mes"],
        )
        lista_col.controls.clear()
        lbl_total.value = f"{len(dados)} registro(s)"
        if not dados:
            lista_col.controls.append(
                ft.Text("Nenhuma leitura encontrada.", color=st.GREY_TEXT, italic=True)
            )
        for d in dados:
            lista_col.controls.append(_criar_card(d))
        page.update()

    def _criar_card(d):
        agua = f"{d['leitura_agua']:.2f} m³" if d.get("leitura_agua") is not None else "—"
        gas = f"{d['leitura_gas']:.3f} m³" if d.get("leitura_gas") is not None else "—"
        data_txt = (d.get("data_hora_coleta") or "")[:16]
        leiturista = d.get("leiturista") or ""

        sinc_icon = (
            ft.Icon(ft.Icons.CLOUD_DONE, color=st.SUCCESS_GREEN, size=14)
            if d.get("sincronizado")
            else ft.Icon(ft.Icons.CLOUD_OFF, color=st.ACCENT_ORANGE, size=14)
        )

        def on_excluir(ev, lid=d["id"], unid=d["unidade_id"]):
            def fazer(ev2):
                page.close(page.dialog)
                ok = Database.deletar_leitura(lid)
                if ok:
                    page.open(ft.SnackBar(
                        ft.Text(f"Leitura da unidade {unid} excluída."),
                        bgcolor=st.SUCCESS_GREEN,
                    ))
                    carregar_leituras()
                else:
                    page.open(ft.SnackBar(
                        ft.Text("Erro ao excluir leitura."), bgcolor=st.RED_ERROR
                    ))

            page.open(ft.AlertDialog(
                modal=True,
                title=ft.Text("Confirmar Exclusão"),
                content=ft.Text(f"Excluir leitura da unidade {unid} de {data_txt}?"),
                actions=[
                    ft.TextButton("Excluir", on_click=fazer),
                    ft.TextButton("Cancelar", on_click=lambda _: page.close(page.dialog)),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            ))

        def on_editar(ev, lid=d["id"], va=d.get("leitura_agua"), vg=d.get("leitura_gas"), unid=d["unidade_id"]):
            txt_a = ft.TextField(
                label="Água (m³)",
                value=str(va) if va is not None else "",
                keyboard_type=ft.KeyboardType.NUMBER,
                width=150,
                border_color=st.PRIMARY_BLUE,
            )
            txt_g = ft.TextField(
                label="Gás (m³)",
                value=str(vg) if vg is not None else "",
                keyboard_type=ft.KeyboardType.NUMBER,
                width=150,
                border_color=st.ACCENT_ORANGE,
            )
            lbl_err = ft.Text("", size=12, color=st.RED_ERROR)

            def salvar(ev2):
                try:
                    nova_agua = float(txt_a.value.replace(",", ".")) if txt_a.value.strip() else None
                    novo_gas = float(txt_g.value.replace(",", ".")) if txt_g.value.strip() else None
                except ValueError:
                    lbl_err.value = "Valor inválido."
                    page.update()
                    return

                if Database.editar_leitura(lid, nova_agua, novo_gas):
                    page.close(page.dialog)
                    page.open(ft.SnackBar(
                        ft.Text("Leitura atualizada com sucesso."), bgcolor=st.SUCCESS_GREEN
                    ))
                    carregar_leituras()
                else:
                    lbl_err.value = "Erro ao salvar alterações."
                    page.update()

            page.open(ft.AlertDialog(
                modal=True,
                title=ft.Text(f"Editar — Unidade {unid}"),
                content=ft.Column([
                    ft.Row([txt_a, txt_g], spacing=8),
                    lbl_err,
                ], tight=True, spacing=8),
                actions=[
                    ft.TextButton("Salvar", on_click=salvar),
                    ft.TextButton("Cancelar", on_click=lambda _: page.close(page.dialog)),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            ))

        info_row = ft.Row([
            ft.Text(d.get("unidade_id", "?"), weight="bold", size=14),
            sinc_icon,
        ], spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER)

        detalhe_row = ft.Text(
            f"Água: {agua}  |  Gás: {gas}", size=12, color=st.GREY_TEXT
        )

        meta_row = ft.Text(
            f"{data_txt}  {('· ' + leiturista) if leiturista else ''}",
            size=11,
            color="#616161",
        )

        return ft.Container(
            content=ft.Row([
                ft.Column([info_row, detalhe_row, meta_row], spacing=2, expand=True),
                ft.Row([
                    ft.IconButton(
                        icon=ft.Icons.EDIT_NOTE,
                        icon_color=st.PRIMARY_BLUE,
                        icon_size=20,
                        tooltip="Editar",
                        on_click=on_editar,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.DELETE_OUTLINE,
                        icon_color=st.RED_ERROR,
                        icon_size=20,
                        tooltip="Excluir",
                        on_click=on_excluir,
                    ),
                ], spacing=0),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor="#1E2126",
            border_radius=8,
            padding=ft.Padding.symmetric(horizontal=12, vertical=8),
        )

    # --- Filtros ---
    def on_unidade(e):
        filtros["unidade"] = e.control.value
        carregar_leituras()

    def on_mes(e):
        filtros["mes"] = e.control.value
        carregar_leituras()

    def on_busca(e):
        filtros["texto"] = e.control.value
        carregar_leituras()

    dd_unidade = ft.Dropdown(
        label="Unidade",
        options=[ft.dropdown.Option(u) for u in unidades],
        value="Todas",
        width=155,
        text_size=12,
    )
    dd_unidade.on_change = on_unidade

    dd_mes = ft.Dropdown(
        label="Mês",
        options=[ft.dropdown.Option(m) for m in meses],
        value=meses[0],
        width=125,
        text_size=12,
    )
    dd_mes.on_change = on_mes

    txt_busca = ft.TextField(
        label="Buscar",
        prefix_icon=ft.Icons.SEARCH,
        width=130,
        text_size=12,
        on_change=on_busca,
    )

    carregar_leituras()

    return ft.View(
        route="/historico",
        bgcolor=st.BG_DARK,
        appbar=ft.AppBar(
            title=ft.Text("Histórico de Leituras"),
            bgcolor=st.PRIMARY_BLUE,
            leading=ft.IconButton(
                icon=ft.Icons.ARROW_BACK,
                on_click=lambda _: page.go("/menu"),
            ),
        ),
        controls=[
            ft.Column(
                [
                    ft.Container(
                        content=ft.Column([
                            ft.Row(
                                [dd_unidade, dd_mes, txt_busca],
                                spacing=6,
                                wrap=True,
                            ),
                            lbl_total,
                        ], spacing=4),
                        padding=ft.Padding.symmetric(horizontal=12, vertical=8),
                    ),
                    ft.Divider(height=1, color="white10"),
                    lista_col,
                ],
                expand=True,
                spacing=0,
            )
        ],
    )
