import flet as ft
import database as db
import vision
import reports

def main(page: ft.Page):
    page.title = "AguaFlow"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    def enviar_relatorio_clicado(e):
        dados = db.buscar_todos()
        if not dados:
            page.snack_bar = ft.SnackBar(ft.Text("Nenhum dado encontrado."))
            page.snack_bar.open = True
            page.update()
            return
        
        pdf = reports.gerar_relatorio_leituras_pdf(dados)
        sucesso = reports.enviar_email_com_pdf("clodoaldomaldonado112@gmail.com", pdf)
        
        texto = "✅ Enviado!" if sucesso else "❌ Erro no envio."
        page.snack_bar = ft.SnackBar(ft.Text(texto))
        page.snack_bar.open = True
        page.update()

    def iniciar_leitura(e):
        unidade = db.buscar_proximo_pendente()
        page.clean()
        if unidade:
            page.add(
                ft.Text(f"Unidade: {unidade[1]}", size=30, weight="bold"),
                ft.ElevatedButton("ESCANEAR", on_click=lambda _: escanear(unidade[1])),
                ft.TextButton("Voltar", on_click=lambda _: mostrar_inicio())
            )
        else:
            page.add(
                ft.Text("Concluído!"),
                ft.ElevatedButton("Voltar", on_click=lambda _: mostrar_inicio())
            )
        page.update()

    def escanear(numero):
        res = vision.escanear_qr()
        page.snack_bar = ft.SnackBar(ft.Text(f"Lido: {res}"))
        page.snack_bar.open = True
        page.update()

    def mostrar_inicio():
        page.clean()
        # Aqui removemos todos os nomes de argumentos que causam erro
        page.add(
            ft.Icon(ft.icons.WATER_DROP, size=100, color="blue"),
            ft.Text("AguaFlow", size=40, weight="bold"),
            ft.FilledButton("INICIAR", on_click=iniciar_leitura, width=200),
            ft.OutlinedButton("RELATÓRIO", on_click=enviar_relatorio_clicado, width=200)
        )
        page.update()

    mostrar_inicio()

if __name__ == "__main__":
    db.init_db()
    # Forçando o modo estável
    ft.app(target=main, view=ft.AppView.WEB_BROWSER)
    
