import flet as ft
import database as db
import medicao
import reports  
import utils    
import time  
import logging

# Silencia logs de erro do asyncio que acontecem no fechamento
logging.getLogger("asyncio").setLevel(logging.CRITICAL)

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
            conn.close()
            
            lista_nomes = [str(u[0]) for u in unidades_db]
            
            if not lista_nomes:
                mostrar_aviso("Banco vazio!")
                return

            for nome in lista_nomes:
                reports.gerar_qr_unidade(nome)
            
            # CORREÇÃO: Usar 'lista_nomes' em vez de 'lista'
            pdf_nome = reports.gerar_pdf_etiquetas_qr(lista_nomes)
            mostrar_aviso(f"Sucesso! {len(lista_nomes)} etiquetas geradas.")
            
        except Exception as ex:
            mostrar_aviso(f"Erro: {ex}")

    def acao_gerar_relatorio(e):
        try:
            conn = db.get_connection()
            dados = conn.cursor().execute("SELECT * FROM leituras").fetchall()
            conn.close()
            
            pdf_nome = reports.gerar_relatorio_leituras_pdf(dados)
            # COLOQUE SEU E-MAIL ABAIXO
            sucesso_email = reports.enviar_email_com_pdf("DESTINATARIO@gmail.com", pdf_nome)
            
            if sucesso_email:
                mostrar_aviso(f"Relatório enviado para o e-mail!")
            else:
                mostrar_aviso(f"Relatório gerado localmente: {pdf_nome}")

        except Exception as ex:
            mostrar_aviso(f"Erro: {ex}")

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

    # Função de fechar agora dentro do main para reconhecer a 'page'
    def sair_do_sistema(e):
        page.window.destroy()

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
                        on_click=sair_do_sistema 
                    )
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            )
        )
        page.update()

    navegar_para_menu()

# Execução correta
if __name__ == "__main__":
    ft.app(target=main)
    