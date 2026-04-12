import flet as ft
from database.database import Database
# Importa o motor de relatórios da pasta utils
from utils.relatorio_engine import RelatorioEngine

def montar_tela_relatorio(page: ft.Page, voltar):
    # Rota Lógica: Busca no SQLite todas as medições feitas no mês atual
    leituras_atuais = Database.buscar_relatorio_geral()
    total_unidades = 96
    lidas = len(leituras_atuais)
    progresso = lidas / total_unidades if total_unidades > 0 else 0

    # --- FUNÇÃO: GERAR PDF ---
    # Rota Lógica: Aciona a RelatorioEngine para criar o arquivo físico no dispositivo
    async def clicar_gerar_pdf(e):
        page.snack_bar = ft.SnackBar(ft.Text("Gerando relatório PDF..."), bgcolor="blue")
        page.snack_bar.open = True
        page.update()
        
        try:
            # Chama o método estático da classe de motor
            caminho = RelatorioEngine.gerar_relatorio_consumo(leituras_atuais)
            page.snack_bar = ft.SnackBar(ft.Text(f"Salvo em: {caminho}"), bgcolor="green")
        except Exception as err:
            page.snack_bar = ft.SnackBar(ft.Text(f"Erro técnico: {err}"), bgcolor="red")
        
        page.snack_bar.open = True
        page.update()

    # --- FUNÇÃO: FINALIZAR E ENVIAR ---
    # Rota Lógica: Gera PDF + CSV e dispara e-mail via servidor SMTP
    async def acao_finalizar_mes(e):
        page.snack_bar = ft.SnackBar(ft.Text("Preparando documentos e enviando e-mail..."), bgcolor="blue")
        page.snack_bar.open = True
        page.update()
        
        try:
            pdf_path = RelatorioEngine.gerar_relatorio_consumo(leituras_atuais)
            csv_path = RelatorioEngine.gerar_csv_consumo(leituras_atuais)
            sucesso, mensagem = RelatorioEngine.enviar_relatorios_por_email(pdf_path, csv_path)
            
            page.snack_bar = ft.SnackBar(ft.Text(mensagem), bgcolor="green" if sucesso else "red")
        except Exception as err:
            page.snack_bar = ft.SnackBar(ft.Text(f"Erro no envio: {err}"), bgcolor="red")
            
        page.snack_bar.open = True
        page.update()

    # Retorno da Visualização (UI)
    return ft.View(
        route="/relatorios",
        appbar=ft.AppBar(
            title=ft.Text("Relatórios de Consumo"),
            leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=voltar) # Volta ao menu principal
        ),
        controls=[
            ft.Column([
                ft.Container(
                    bgcolor="#232629", padding=20, border_radius=15,
                    content=ft.Column([
                        ft.Text(f"Progresso de Leituras: {lidas}/{total_unidades}", size=18, weight="bold"),
                        ft.ProgressBar(value=progresso, color="blue"),
                        ft.Text(f"Status: {int(progresso*100)}% concluído", size=12, color="grey"),
                    ])
                ),
                
                ft.Divider(height=20, color="transparent"),
                
                ft.ElevatedButton(
                    "GERAR RELATÓRIO PDF (LOCAL)", 
                    icon=ft.Icons.PICTURE_AS_PDF, 
                    on_click=clicar_gerar_pdf,
                    width=400, height=50
                ),
                
                ft.ElevatedButton(
                    "FINALIZAR MÊS E ENVIAR AO ESCRITÓRIO", 
                    icon=ft.Icons.EMAIL_OUTLINED, 
                    on_click=acao_finalizar_mes,
                    width=400, height=50,
                    style=ft.ButtonStyle(bgcolor="blue", color="white")
                ),
                
                ft.Text(
                    "Ao finalizar, o sistema enviará automaticamente o PDF e o CSV para o e-mail administrativo configurado.",
                    size=11, color="grey", text_align="center"
                )
            ], scroll=ft.ScrollMode.ADAPTIVE, spacing=15, padding=20)
        ]
    )