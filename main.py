import flet as ft
import database as db
import vision
import reports  # Importando o novo arquivo que você criou

def main(page: ft.Page):
    page.title = "AguaFlow - Gestão de Leituras"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 400
    page.window_height = 600
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    def enviar_relatorio_clicado(e):
        # 1. Busca todos os dados (precisamos criar essa função no database.py)
        dados = db.buscar_todos() 
        if not dados:
            page.snack_bar = ft.SnackBar(ft.Text("Nenhum dado para enviar!"))
            page.snack_bar.open = True
            page.update()
            return

        # 2. Gera o PDF
        pdf_nome = reports.gerar_relatorio_leituras_pdf(dados)
        
        # 3. Envia o e-mail
        sucesso = reports.enviar_email_com_pdf("seu_email_destino@gmail.com", pdf_nome)
        
        if sucesso:
            page.snack_bar = ft.SnackBar(ft.Text("✅ Relatório enviado com sucesso!"), bgcolor="green")
        else:
            page.snack_bar = ft.SnackBar(ft.Text("❌ Erro ao enviar e-mail. Verifique a senha."), bgcolor="red")
        
        page.snack_bar.open = True
        page.update()

    def iniciar_leitura(e):
        unidade = db.buscar_proximo_pendente()
        page.clean()
        if unidade:
            page.add(
                ft.Text(f"Unidade: {unidade[1]}", size=30, weight="bold"),
                ft.ElevatedButton("ESCANEAR QR", icon=ft.icons.QR_CODE_SCANNER, 
                                 on_click=lambda _: escanear(unidade[1])),
                ft.TextButton("Voltar", on_click=lambda _: mostrar_inicio())
            )
        else:
            page.add(
                ft.Text("Todas as leituras concluídas! 🎉"),
                ft.ElevatedButton("Voltar", on_click=lambda _: mostrar_inicio())
            )
        page.update()

    def escanear(numero):
        res = vision.escanear_qr()
        # Aqui você salvaria o resultado no banco (db.salvar_leitura)
        page.snack_bar = ft.SnackBar(ft.Text(f"Lido para {numero}: {res}"))
        page.snack_bar.open = True
        page.update()

    def mostrar_inicio():
        page.clean()
        page.add(
            ft.Column(
                [
                    ft.Icon(name=ft.icons.WATER_DROP, size=100, color="blue"),
                    ft.Text("AguaFlow", size=40, weight="bold"),
                    ft.Divider(height=20, color="transparent"),
                    ft.FilledButton("INICIAR LEITURAS", on_click=iniciar_leitura, width=250),
                    ft.OutlinedButton("ENVIAR RELATÓRIO", icon=ft.icons.EMAIL, 
                                     on_click=enviar_relatorio_clicado, width=250),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        )
        page.update()

    mostrar_inicio()

if __name__ == "__main__":
    db.init_db()
    ft.app(target=main)
    