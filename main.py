import flet as ft
import utils
import database


def main(page: ft.Page):
    # --- 1. CONFIGURAÇÕES INICIAIS ---
    database.criar_banco()
    page.title = "AguaFlow - Sistema"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 400
    page.window_height = 700
    page.vertical_alignment = "center"
    page.horizontal_alignment = "center"

    unidades = ["Hidrometro Geral", "Area de Lazer"]
    for andar in range(16, 0, -1):
        for apto in range(1, 7):
            unidades.append(f"Apto {andar}{apto}")

    indice = [0]
    conteudo_pagina = ft.Column(expand=True, scroll="auto")

    # --- 2. ELEMENTOS DE INTERFACE ---
    lbl_unidade = ft.Text(
        "UNIDADE: " + unidades[0], size=22, weight="bold", color="blue")
    txt_agua = ft.TextField(label="LEITURA AGUA (m3)",
                            border_color="blue", keyboard_type="number")
    txt_gas = ft.TextField(label="LEITURA GAS (m3)", border_color="blue")

    # --- 3. FUNÇÕES DE APOIO ---

    def abrir_scanner_camera(e):
        page.snack_bar = ft.SnackBar(
            ft.Text("Iniciando Câmera e IA de leitura..."))
        page.snack_bar.open = True
        page.update()

    def acao_enviar_email(e):
        page.snack_bar = ft.SnackBar(
            ft.Text("Gerando relatório e enviando..."))
        page.snack_bar.open = True
        page.update()
        dados = database.listar_todas_leituras()
        pdf_gerado = utils.gerar_relatorio_leituras_pdf(dados)
        sucesso = utils.enviar_email_com_pdf(
            "administracao@vivereprudente.com.br", pdf_gerado)

        page.snack_bar = ft.SnackBar(
            ft.Text("E-mail enviado!" if sucesso else "Falha no envio."))
        page.snack_bar.open = True
        page.update()

    def verificar_e_salvar(e):
        unidade_atual = unidades[indice[0]]
        if database.checar_leitura_existente(unidade_atual):
            page.snack_bar = ft.SnackBar(
                ft.Text(f"{unidade_atual} já foi lido!"))
        elif txt_agua.value == "":
            database.salvar_leitura(unidade_atual, 0.0, "PULADO")
            proximo_item()
        else:
            try:
                val = float(txt_agua.value.replace(",", "."))
                database.salvar_leitura(unidade_atual, val, txt_gas.value)
                proximo_item()
            except ValueError:
                page.snack_bar = ft.SnackBar(ft.Text("Valor inválido!"))

        page.snack_bar.open = True
        page.update()

    def proximo_item():
        if indice[0] < len(unidades) - 1:
            indice[0] += 1
            lbl_unidade.value = "UNIDADE: " + unidades[indice[0]]
            txt_agua.value = ""
            txt_gas.value = ""
        else:
            conteudo_pagina.controls.clear()
            conteudo_pagina.controls.append(ft.Text("CONCLUÍDO!", size=30))
        page.update()

    def resetar_sistema():
        indice[0] = 0
        lbl_unidade.value = "UNIDADE: " + unidades[0]
        mudar_aba_manual(0)

    # --- 4. VIEWS (TELAS) ---

    def view_leitura():
        return ft.Column([
            ft.Text("MEDIÇÃO INTELIGENTE", size=20, weight="bold"),
            ft.Divider(),
            ft.FilledButton("ABRIR CÂMERA (SCAN)",
                            icon="camera_alt", on_click=abrir_scanner_camera),
            lbl_unidade, txt_agua, txt_gas,
            ft.FilledButton("SALVAR E PRÓXIMO",
                            on_click=verificar_e_salvar, width=300)
        ], horizontal_alignment="center", spacing=15)

    def view_relatorios():
        registros = database.listar_todas_leituras()
        linhas = [ft.DataRow(cells=[ft.DataCell(ft.Text(str(c)))
                             for c in r]) for r in registros]
        return ft.Column([
            ft.Text("HISTÓRICO", size=20, weight="bold"),
            ft.DataTable(columns=[ft.DataColumn(ft.Text("Unid.")), ft.DataColumn(ft.Text("Água")),
                                  ft.DataColumn(ft.Text("Gás")), ft.DataColumn(ft.Text("Data"))], rows=linhas),
            ft.FilledButton("ENVIAR POR E-MAIL", icon="email",
                            on_click=acao_enviar_email)
        ], horizontal_alignment="center", scroll="auto")

    def view_ajuda():
        return ft.Column([
            ft.Text("AJUDA", size=20, weight="bold"),
            ft.Text("1. Use o Scanner para agilizar."),
            ft.Text("2. Deixe vazio para 'Pular'."),
            ft.FilledButton("VOLTAR AO INÍCIO",
                            on_click=lambda _: resetar_sistema())
        ], horizontal_alignment="center")

    # --- 5. NAVEGAÇÃO CORRIGIDA ---

    def mudar_aba(e):
        opcao = e.control.selected_index
        conteudo_pagina.controls.clear()
        if opcao == 0:
            conteudo_pagina.controls.append(view_leitura())
        elif opcao == 2:
            conteudo_pagina.controls.append(view_relatorios())
        elif opcao == 3:
            conteudo_pagina.controls.append(view_ajuda())
        else:
            conteudo_pagina.controls.append(
                ft.Text("Tela em desenvolvimento..."))
        page.update()

    def mudar_aba_manual(index):
        nav_bar.selected_index = index
        conteudo_pagina.controls.clear()
        conteudo_pagina.controls.append(view_leitura())  # Volta para leitura
        page.update()

    nav_bar = ft.NavigationBar(
        destinations=[
            ft.NavigationBarDestination(icon="edit", label="Leituras"),
            ft.NavigationBarDestination(icon="add", label="Cadastro"),
            ft.NavigationBarDestination(icon="history", label="Histórico"),
            ft.NavigationBarDestination(icon="help", label="Ajuda"),
        ],
        on_change=mudar_aba
    )

    # --- 6. LOGIN ---

    def realizar_login(e):
        if user_input.value == "admin" and pass_input.value == "123":
            page.clean()
            page.navigation_bar = nav_bar
            conteudo_pagina.controls.append(view_leitura())
            page.add(conteudo_pagina)
        else:
            page.snack_bar = ft.SnackBar(ft.Text("Login Inválido!"))
            page.snack_bar.open = True
        page.update()

    user_input = ft.TextField(label="Usuário", width=300)
    pass_input = ft.TextField(label="Senha", width=300, password=True)

    page.add(
        ft.Text("VIVERE PRUDENTE", size=25, weight="bold", color="blue"),
        user_input, pass_input,
        ft.FilledButton("ENTRAR", on_click=realizar_login, width=300)
    )


if __name__ == "__main__":
    # Tente rodar sem o modo web primeiro para testar a janela nativa
    ft.app(target=main)
