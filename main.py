import flet as ft


def main(page: ft.Page):
    # Configurações básicas de página
    page.title = "AguaFlow"
    page.window_width = 400
    page.window_height = 700
    page.theme_mode = ft.ThemeMode.LIGHT

    # Dados das Unidades
    unidades = ["Hidrometro Geral", "Area de Lazer", "Apto 161"]
    # Usamos uma lista para o índice para que ele possa ser alterado dentro das funções
    state = {"indice": 0}

    # --- TELA: CONCLUÍDO ---
    def mostrar_concluido():
        page.clean()

        icone = ft.Icon("check_circle")
        icone.size = 100
        icone.color = "green"

        texto = ft.Text("CONCLUÍDO!", size=30, weight="bold")

        btn = ft.FilledButton("RECOMEÇAR", on_click=lambda _: carregar_login())

        page.add(
            ft.Column([icone, texto, btn],
                      horizontal_alignment="center", spacing=20)
        )
        page.update()

    # --- TELA: LEITURA ---
    def ir_leitura(e):
        page.clean()

        txt_agua = ft.TextField(label="ÁGUA (m3)")
        txt_gas = ft.TextField(label="GÁS (m3)")

        def proximo(e):
            if state["indice"] < len(unidades) - 1:
                state["indice"] += 1
                ir_leitura(None)
            else:
                mostrar_concluido()

        titulo = ft.Text(unidades[state["indice"]],
                         size=25, weight="bold", color="blue")
        btn_salvar = ft.FilledButton(
            "SALVAR E PRÓXIMO", on_click=proximo, width=300)

        page.add(
            ft.Column([titulo, txt_agua, txt_gas, btn_salvar],
                      horizontal_alignment="center", spacing=20)
        )
        page.update()

    # --- TELA: LOGIN ---
    def carregar_login():
        state["indice"] = 0
        page.clean()

        icone = ft.Icon("water_drop")
        icone.size = 80
        icone.color = "blue"

        titulo = ft.Text("AguaFlow Login", size=24, weight="bold")
        user = ft.TextField(label="Usuário", width=300)
        senha = ft.TextField(label="Senha", width=300, password=True)
        btn_entrar = ft.FilledButton("ENTRAR", on_click=ir_leitura, width=300)

        page.add(
            ft.Column([icone, titulo, user, senha, btn_entrar],
                      horizontal_alignment="center", spacing=20)
        )
        page.update()

    # Inicia o aplicativo
    carregar_login()


if __name__ == "__main__":
    # COMANDO OBRIGATÓRIO PARA FLET 0.80+
    # Não use ft.app! Use ft.run
    ft.run(main)
