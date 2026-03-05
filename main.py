import flet as ft
import database as db
import medicao
import reports  # Importa o motor de PDFs e E-mail
import utils    # Importa o gerador de QR Codes

def main(page: ft.Page):
    page.title = "ÁguaFlow - Vivere Prudente"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 400
    page.window_height = 750
    
    # Garante que o banco de dados e as unidades existam ao abrir
    db.init_db()

    # --- FUNÇÕES DE NAVEGAÇÃO E AÇÃO ---

    def navegar_para_medicao(e):
        page.controls.clear()
        page.add(medicao.montar_tela(page, navegar_para_menu))
        page.update()

    def acao_gerar_etiquetas(e):
        # 1. Busca todas as unidades do banco
        conn = db.get_connection()
        unidades_db = conn.cursor().execute("SELECT unidade FROM leituras").fetchall()
        lista_nomes = [u[0] for u in unidades_db]
        
        # 2. Gera as imagens dos QR Codes (pasta qrcodes/)
        for nome in lista_nomes:
            utils.gerar_qr_unidade(nome)
            
        # 3. Cria o PDF com as etiquetas organizadas
        pdf_path = reports.gerar_pdf_etiquetas_qr(lista_nomes)
        
        mostrar_aviso(f"Sucesso! {len(lista_nomes)} etiquetas geradas em PDF.")

    def acao_gerar_relatorio(e):
        # 1. Busca os dados de leitura
        conn = db.get_connection()
        dados = conn.cursor().execute("SELECT * FROM leituras").fetchall()
        
        # 2. Gera o relatório PDF
        pdf_nome = reports.gerar_relatorio_leituras_pdf(dados)
        
        mostrar_aviso(f"Relatório {pdf_nome} criado com sucesso!")

    def mostrar_aviso(mensagem):
        page.snack_bar = ft.SnackBar(ft.Text(mensagem))
        page.snack_bar.open = True
        page.update()

    def navegar_para_menu(e=None):
        page.controls.clear()
        page.add(
            ft.Container(
                padding=30,
                content=ft.Column([
                    ft.Image(src="https://cdn-icons-png.flaticon.com/512/3105/3105807.png", width=100),
                    ft.Text("VIVERE PRUDENTE", size=28, weight="bold", color="#002868"),
                    ft.Text("Gestão de Consumo", size=16, color="grey"),
                    ft.Divider(height=40),
                    
                    ft.ElevatedButton(
                        "INICIAR LEITURA", 
                        icon=ft.Icons.PLAY_ARROW,
                        on_click=navegar_para_medicao,
                        width=280, height=60,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
                    ),
                    
                    ft.OutlinedButton(
                        "GERAR ETIQUETAS QR", 
                        icon=ft.Icons.QR_CODE_2, 
                        width=280, height=50,
                        on_click=acao_gerar_etiquetas  # AGORA FUNCIONA!
                    ),
                    
                    ft.OutlinedButton(
                        "RELATÓRIOS (PDF)", 
                        icon=ft.Icons.PICTURE_AS_PDF, 
                        width=280, height=50,
                        on_click=acao_gerar_relatorio   # AGORA FUNCIONA!
                    ),

                    ft.TextButton("Sair do Sistema", icon=ft.Icons.EXIT_TO_APP, on_click=lambda _: page.window_destroy())
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            )
        )
        page.update()

    navegar_para_menu()

ft.run(main)
