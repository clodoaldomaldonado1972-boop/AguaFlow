import flet as ft
import database as db
import vision
import reports


def main(page: ft.Page):
    page.title = "AguaFlow"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    # --- FUNÇÃO DE RELATÓRIO ---
    def enviar_relatorio_clicado(e):
        dados = db.buscar_todos()
        if not dados:
            page.add(ft.Text("❌ Banco de dados vazio!", color="red"))
            page.update()
            return

        pdf = reports.gerar_relatorio_leituras_pdf(dados)
        sucesso = reports.enviar_email_com_pdf(
            "clodoaldomaldonado112@gmail.com", pdf)

        aviso = "✅ Relatório Enviado!" if sucesso else "❌ Erro no envio."
        page.add(ft.Text(aviso, color="green" if sucesso else "red"))
        page.update()

    # --- FUNÇÃO DE LEITURA ---
    def iniciar_leitura_real(e):
        unidade = db.buscar_proximo_pendente()
        page.clean()
        if unidade:
            page.add(
                ft.Text(
                    f"Unidade Atual: {unidade[1]}", size=25, weight="bold"),
                ft.ElevatedButton(
                    "ESCANEAR AGORA", on_click=lambda _: escanear(unidade[1]), width=300),
                ft.TextButton("Voltar ao Início",
                              on_click=lambda _: mostrar_inicio())
            )
        else:
            page.add(ft.Text("🎉 Todas as leituras concluídas!"), ft.ElevatedButton(
                "Voltar", on_click=lambda _: mostrar_inicio()))
        page.update()

    def escanear(numero):
        vision.escanear_qr()  # Abre a câmera
        page.add(ft.Text(f"✅ Leitura finalizada para {numero}"))
        page.update()

    # --- TELA INICIAL (Igual à da sua foto) ---
    def mostrar_inicio():
        page.clean()
        page.add(
            ft.Text("SISTEMA AGUAFLOW", size=35, weight="bold"),
            ft.Divider(),
            ft.ElevatedButton("INICIAR LEITURAS",
                              on_click=iniciar_leitura_real, width=300),
            ft.ElevatedButton("ENVIAR RELATÓRIO",
                              on_click=enviar_relatorio_clicado, width=300),
            ft.Text("Ambiente Python 3.14 - Operacional",
                    color="blue", size=12)
        )
        page.update()

    mostrar_inicio()


if __name__ == "__main__":
    db.init_db()
    # Mudamos app() para run() para o aviso sumir
    ft.run(main, view=ft.AppView.WEB_BROWSER)
