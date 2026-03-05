import flet as ft
import database as db
import reports 

NAVY_BLUE = "#002868"

def main(page: ft.Page):
    page.title = "ÁguaFlow - Gestão Total"
    page.window_width = 400
    page.window_height = 800
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.scroll = "adaptive"

    # --- FUNÇÕES DE AÇÃO ---
    def acao_gerar_e_enviar(e):
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, unidade, bloco, leitura_valor, 0, status FROM leituras")
        dados_do_banco = cursor.fetchall()
        conn.close()
        try:
            arquivo_pdf = reports.gerar_relatorio_leituras_pdf(dados_do_banco)
            reports.enviar_email_com_pdf("clodoaldomaldonado112@gmail.com", arquivo_pdf)
            page.snack_bar = ft.SnackBar(ft.Text("Relatório enviado com sucesso!"))
            page.snack_bar.open = True
        except Exception as ex:
            print(f"Erro: {ex}")
        page.update()

    def acao_gerar_etiquetas(e):
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, unidade, bloco FROM leituras")
            unidades = cursor.fetchall()
            conn.close()
            arquivo_qr = reports.gerar_pdf_etiquetas_qr(unidades)
            page.snack_bar = ft.SnackBar(ft.Text(f"Etiquetas criadas: {arquivo_qr}"))
            page.snack_bar.open = True
        except Exception as ex:
            print(f"Erro ao gerar QRs: {ex}")
        page.update()

    def acao_resetar(e):
        db.resetar_todas_leituras()
        page.snack_bar = ft.SnackBar(ft.Text("Banco resetado! Pronto para novas leituras."))
        page.snack_bar.open = True
        mostrar_inicio()

    # --- COMPONENTES VISUAIS ---
    def header(titulo):
        return ft.Container(
            content=ft.Text(titulo, color="white", weight="bold", size=18),
            bgcolor=NAVY_BLUE, padding=20, alignment=ft.Alignment(0, 0), width=float("inf"),
        )

    def custom_button(texto, acao, cor=NAVY_BLUE, largura=300):
        return ft.Button(
            content=ft.Text(texto, weight="bold", color="white" if cor == NAVY_BLUE else "black"),
            style=ft.ButtonStyle(bgcolor=cor, shape=ft.RoundedRectangleBorder(radius=10)),
            width=largura, height=50, on_click=acao
        )

    # --- TELAS ---
    def mostrar_historico():
        page.controls.clear()
        page.add(header("HISTÓRICO DE LEITURAS"))
        try:
            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT unidade, bloco, leitura_valor, status FROM leituras")
            rows = cursor.fetchall()
            conn.close()
            lista = ft.Column(spacing=10, scroll="auto", height=450)
            for r in rows:
                cor_status = "green" if r[3] == 'concluido' else "red"
                valor = r[2] if r[2] else "---"
                lista.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Text(f"Apto {r[0]}-{r[1]}", weight="bold", expand=True),
                            ft.Text(f"Val: {valor}", color=cor_status),
                        ]),
                        padding=10, border=ft.Border.all(1, "#DDD"), border_radius=8
                    )
                )
            page.add(lista)
        except: pass
        page.add(custom_button("VOLTAR", lambda _: mostrar_inicio(), cor="#CCCCCC"))
        page.update()

    def mostrar_leitura_individual():
        page.controls.clear()
        unidade = db.buscar_proximo_pendente()
        if not unidade:
            page.add(
                header("CONCLUÍDO"),
                ft.Text("\n\nLeituras Finalizadas!", size=22, weight="bold", color="green"),
                custom_button("GERAR E ENVIAR RELATÓRIO", acao_gerar_e_enviar, cor="orange"),
                ft.TextButton("Voltar ao Menu", on_click=lambda _: mostrar_inicio())
            )
        else:
            txt_leitura = ft.TextField(label="Valor Atual", width=300, keyboard_type="number", autofocus=True)
            page.add(
                header(f"UNIDADE {unidade[1]}"),
                ft.Text(f"Bloco: {unidade[2]}", size=16),
                txt_leitura,
                custom_button("SALVAR E PRÓXIMO", lambda _: salvar_e_proximo(unidade[0], txt_leitura)),
                ft.TextButton("Cancelar", on_click=lambda _: mostrar_inicio())
            )
        page.update()

    def salvar_e_proximo(id_reg, input_val):
        if input_val.value:
            try:
                num = float(input_val.value.replace(",", "."))
                db.salvar_leitura(id_reg, num)
                mostrar_leitura_individual()
            except: pass
        page.update()

    def mostrar_inicio():
        page.controls.clear()
        page.add(
            header("ÁGUAFLOW - VIVERE PRUDENTE"),
            ft.Divider(height=20, color="transparent"),
            custom_button("INICIAR LEITURAS", lambda _: mostrar_leitura_individual()),
            ft.Divider(height=10, color="transparent"),
            custom_button("VER HISTÓRICO", lambda _: mostrar_historico(), cor="#E3F2FD"),
            ft.Divider(height=10, color="transparent"),
            custom_button("GERAR ETIQUETAS QR", acao_gerar_etiquetas, cor="#F5F5F5"),
            ft.Divider(height=10, color="transparent"),
            custom_button("LIMPAR TUDO / NOVO MÊS", acao_resetar, cor="#FFEBEE"),
            ft.Text("\nStatus: Pronto", size=10, color="grey")
        )
        page.update()

    # Inicialização do Banco e Interface
    db.init_db()
    mostrar_inicio()

# O comando de rodar deve ficar fora da função main
ft.run(main)
