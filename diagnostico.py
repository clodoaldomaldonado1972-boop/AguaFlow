import flet as ft
import os


def main(page: ft.Page):
    page.title = "Diagnóstico ÁguaFlow"

    # Verifica se os arquivos necessários existem na pasta
    utils_existe = os.path.exists('utils.py')
    db_existe = os.path.exists('database.py')
    logo_existe = os.path.exists('logo.jpeg')

    page.add(
        ft.Text("🔍 CHECK-UP DO SISTEMA", size=20, weight="bold"),
        ft.Text(f"📂 Pasta atual: {os.getcwd()}"),
        ft.Divider(),
        ft.Text(
            f"✅ Arquivo 'utils.py' encontrado: {utils_existe}", color="green" if utils_existe else "red"),
        ft.Text(
            f"✅ Arquivo 'database.py' encontrado: {db_existe}", color="green" if db_existe else "red"),
        ft.Text(
            f"🖼️ Arquivo 'logo.jpeg' encontrado: {logo_existe}", color="green" if logo_existe else "red"),
        ft.Container(height=20),
        ft.ElevatedButton("FECHAR DIAGNÓSTICO",
                          on_click=lambda _: page.window_close())
    )
    page.update()


# Tenta rodar no navegador caso a janela do Windows esteja falhando
if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.WEB_BROWSER)
