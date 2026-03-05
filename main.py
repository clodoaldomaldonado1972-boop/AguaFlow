import flet as ft
import database as db
import medicao
import reports  
import utils    

def main(page: ft.Page):
    page.title = "ÁguaFlow - Vivere Prudente"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 400
    page.window_height = 750
    
    db.init_db()

    # --- FUNÇÕES DE APOIO ---
    def mostrar_aviso(mensagem):
        page.snack_bar = ft.SnackBar(ft.Text(mensagem))
        page.snack_bar.open = True
        page.update()

    # --- AÇÕES DO SISTEMA ---
    def navegar_para_medicao(e):
        page.controls.clear()
        page.add(medicao.montar_tela(page, navegar_para_menu))
        page.update()

    def acao_gerar_etiquetas(e):
        try:
            conn = db.get_connection()
            unidades_db = conn.cursor().execute("SELECT unidade FROM leituras").fetchall()
            lista_nomes = [str(u[0]) for u in unidades_db]
            for nome in lista_nomes:
                utils.gerar_qr_unidade(nome)
            reports.gerar_pdf_etiquetas_qr(lista_nomes)
            mostrar_aviso("Sucesso! Etiquetas geradas em PDF.")
        except Exception as ex:
            mostrar_aviso(f"Erro ao gerar etiquetas: {ex}")

    def acao_gerar_relatorio(e):
        conn = db.get_connection()
        dados = conn.cursor().execute("SELECT * FROM leituras").fetchall()
        pdf_nome = reports.gerar_relatorio_leituras_pdf(dados)
        mostrar_aviso(f"Relatório {pdf_nome} criado!")

    def confirmar_reset(e):
        def realizar_reset(e):
            db.fechar_mes_e_resetar() 
            dlg.open = False
            mostrar_aviso("Mês fechado e histórico salvo!")
            navegar_para_menu()

        dlg = ft.AlertDialog(
            title=ft.Text("Fechar Mês?"),
            content=ft.Text("Isto moverá as leituras para o histórico. Confirma?"),
            actions=[
                ft.TextButton("Sim, Fechar Mês", on_click=realizar_reset),
                ft.TextButton("Cancelar", on_click=lambda _: setattr(dlg, "open", False))
            ]
        )
        page.dialog = dlg
        dlg.open = True
        page.update()

    # --- INTERFACE DO MENU ---
    def navegar_para_menu(e=None):
        page.controls.clear()
        page.add(
            ft.Container(
                padding=30,
                content=ft.Column([
                    ft.Image(src="https://cdn-icons-png.flaticon.com/512/3105/3105807.png", width=100),
                    ft.Text("VIVERE PRUDENTE", size=28, weight="bold", color="#002868"),
                    ft.Text("Gestão de Consumo", size=16, color="grey"),
                    ft.Divider(height=30),
                    
                    ft.FilledButton(
                        "INICIAR LEITURA", 
                        icon=ft.Icons.PLAY_ARROW, 
                        on_click=navegar_para_medicao, 
                        width=280, height=50
                    ),
                    ft.Container(height=10),
                    ft.FilledButton(
                        "GERAR ETIQUETAS QR", 
                        icon=ft.Icons.QR_CODE_2, 
                        on_click=acao_gerar_etiquetas, 
                        width=280, height=50
                    ),
                    ft.Container(height=10),
                    ft.OutlinedButton(
                        "RELATÓRIOS (PDF)", 
                        icon=ft.Icons.PICTURE_AS_PDF, 
                        width=280, height=50,
                        on_click=acao_gerar_relatorio
                    ),

                    ft.Divider(height=40, thickness=1),

                    ft.TextButton(
                        "FECHAR MÊS (HISTÓRICO)", 
                        icon=ft.Icons.RESTART_ALT, 
                        icon_color="red",
                        on_click=confirmar_reset
                    ),

                    ft.TextButton(
                        "Sair do Sistema", 
                        icon=ft.Icons.EXIT_TO_APP, 
                        on_click=lambda _: page.window.close() 
                    )
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            )
        )
        page.update()

    navegar_para_menu()

# INICIALIZAÇÃO CORRETA
if __name__ == "__main__":
    ft.run(main)
    