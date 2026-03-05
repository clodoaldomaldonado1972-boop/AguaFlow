import flet as ft
import auth, reports, utils, database as db, medicao

def main(page: ft.Page):
    page.title = "ÁguaFlow - Vivere Prudente"
    db.init_db()

    def navegar_menu(perfil):
        page.controls.clear()
        coluna = ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15)
        
        # --- Botão Comum (Leitor e Admin) ---
        coluna.controls.append(ft.FilledButton("INICIAR LEITURA", 
            on_click=lambda _: page.add(medicao.montar_tela(page, lambda: navegar_menu(perfil))), width=280))
        
        # --- Botões Exclusivos de ADMIN ---
        if perfil == "admin":
            # 1. Etiquetas
            coluna.controls.append(ft.FilledButton("IMPRIMIR ETIQUETAS QR", on_click=abrir_dialogo_qr, width=280))
            
            # 2. Relatório
            def acao_relatorio(e):
                pdf = reports.gerar_relatorio_leituras_pdf(db.get_dados())
                page.snack_bar = ft.SnackBar(ft.Text(f"Relatório Gerado: {pdf}"))
                page.snack_bar.open = True
                page.update()
            
            coluna.controls.append(ft.FilledButton("RELATÓRIOS MENSAL", on_click=acao_relatorio, width=280))

            # 3. Encerrar Mês (Reset)
            def resetar_clique(e):
                db.fechar_mes_e_resetar()
                page.snack_bar = ft.SnackBar(ft.Text("Mês encerrado! Dados movidos para o histórico."))
                page.snack_bar.open = True
                navegar_menu(perfil) 

            # Botão moderno (FilledButton com fundo vermelho)
            coluna.controls.append(
                ft.FilledButton(
                    "ENCERRAR MÊS ATUAL", 
                    on_click=resetar_clique, 
                    style=ft.ButtonStyle(bgcolor="red", color="white"),
                    width=280
                )
            )

        # --- Botão Ajuda ---
        coluna.controls.append(ft.OutlinedButton("AJUDA / GUIA", on_click=lambda _: abrir_ajuda(perfil), width=280))
        
        page.add(ft.Container(content=coluna, padding=20))
        page.update()

    def abrir_dialogo_qr(e):
        unid_input = ft.TextField(label="Apto (vazio para todos)")
        def confirmar(e):
            u = unid_input.value.strip()
            lista = [u] if u else [str(r[1]) for r in db.get_dados()]
            pdf = reports.gerar_pdf_etiquetas_qr(lista)
            page.dialog.open = False
            page.snack_bar = ft.SnackBar(ft.Text(f"Gerado: {pdf}"))
            page.snack_bar.open = True
            page.update()

        page.dialog = ft.AlertDialog(title=ft.Text("Gerar QR"), content=unid_input, actions=[ft.TextButton("GERAR", on_click=confirmar)])
        page.dialog.open = True
        page.update()

    def abrir_ajuda(perfil):
        page.controls.clear()
        page.add(utils.montar_tela_ajuda(lambda _: navegar_menu(perfil)))
        page.update()

    # Inicia com a tela de login
    page.add(auth.criar_tela_login(page, navegar_menu))

if __name__ == "__main__":
    ft.run(main)