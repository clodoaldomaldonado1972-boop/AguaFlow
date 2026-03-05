import flet as ft
import auth, reports, utils, database as db, medicao

def main(page: ft.Page):
    page.title = "ÁguaFlow - Vivere Prudente"
    db.init_db()

    # --- FUNÇÃO DO MENU (DINÂMICO POR PERFIL) ---
    def navegar_menu(e=None):
        page.controls.clear()
        
        # CORREÇÃO: Lendo a sessão como dicionário
        # .get() ainda funciona em dicionários Python para evitar erros se a chave não existir
        perfil = page.session.get("perfil")
        
        # Botões comuns
        coluna = ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        coluna.controls.append(ft.FilledButton("INICIAR LEITURA", on_click=lambda _: page.add(medicao.montar_tela(page, navegar_menu)), width=280))
        
        # Botões exclusivos de ADMIN
        if perfil == "admin":
            coluna.controls.append(ft.FilledButton("IMPRIMIR ETIQUETAS QR", on_click=abrir_dialogo_qr, width=280))
            coluna.controls.append(ft.FilledButton("RELATÓRIOS MENSAL", on_click=lambda _: reports.gerar_relatorio_leituras_pdf(db.get_dados()), width=280))

        coluna.controls.append(ft.OutlinedButton("AJUDA / GUIA", on_click=lambda _: abrir_ajuda(), width=280))
        page.add(ft.Container(content=coluna, padding=20))
        page.update()

    # --- FUNÇÃO DO DIALOGO DE IMPRESSÃO ---
    def abrir_dialogo_qr(e):
        unid_input = ft.TextField(label="Apto (vazio para todos)")
        def confirmar(e):
            u = unid_input.value.strip()
            # Ajuste aqui: Garante que pegamos a lista correta do banco
            lista = [u] if u else [str(r[0]) for r in db.get_unidades()] 
            pdf = reports.gerar_pdf_etiquetas_qr(lista)
            page.dialog.open = False
            page.snack_bar = ft.SnackBar(ft.Text(f"Gerado: {pdf}"))
            page.snack_bar.open = True
            page.update()

        page.dialog = ft.AlertDialog(
            title=ft.Text("Gerar QR"), 
            content=unid_input, 
            actions=[ft.TextButton("GERAR", on_click=confirmar)]
        )
        page.dialog.open = True
        page.update()

    # --- FUNÇÃO DE AJUDA ---
    def abrir_ajuda():
        page.controls.clear()
        page.add(utils.montar_tela_ajuda(lambda _: navegar_menu()))
        page.update()

    # --- ESTE É O PONTO DE ENTRADA DO APP (DENTRO DO MAIN) ---
    # Limpa a página e mostra o Login
    page.controls.clear()
    page.add(auth.criar_tela_login(page, navegar_menu))
    page.update()

# --- EXECUÇÃO FINAL (FORA DE TUDO) ---
if __name__ == "__main__":
    ft.app(target=main)