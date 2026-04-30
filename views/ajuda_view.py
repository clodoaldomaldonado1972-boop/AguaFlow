import flet as ft

def montar_tela_ajuda(page: ft.Page, on_back): # Garanta que os dois pontos estejam aqui!
    return ft.View(
        route="/ajuda",
        controls=[
            ft.Text("Ajuda do AguaFlow"),
            ft.ElevatedButton("Voltar", on_click=on_back)
        ]
    )