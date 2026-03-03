import flet as ft
import utils  # Isso permite que o main.py "enxergue" a função de gerar etiquetas
import database  # Importa o arquivo de banco de dados do grupo


def main(page: ft.Page):
    # --- CONFIGURAÇÕES INICIAIS DA PÁGINA ---
    page.title = "AguaFlow - Sistema de Medição"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 400
    page.window_height = 700
    page.padding = 20
    # Centraliza o conteúdo na tela de login
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    # --- FUNÇÃO PRINCIPAL: CARREGA APÓS O LOGIN ---
    def carregar_sistema_principal():
        page.clean()  # Limpa a tela de login
        page.vertical_alignment = ft.MainAxisAlignment.START  # Alinha conteúdo no topo

        # Lista de unidades para medição (sequenciamento)
        unidades = ["Hidrômetro Geral", "Área de Lazer",
                    "Apto 166", "Apto 165", "Apto 164"]
        indice = [0]  # Uso de lista para manter a referência do contador

        # --- COMPONENTES DA ABA 1: MEDIÇÃO ---
        lbl_unidade = ft.Text(
            f"UNIDADE: {unidades[0]}", size=22, weight="bold", color="blue900")

        # Campo de entrada para Água com ícone de gota
        txt_agua = ft.TextField(
            label="LEITURA ÁGUA (m³)",
            icon=ft.icons.OPACITY,
            border_color="blue900",
            keyboard_type=ft.KeyboardType.NUMBER
        )

        # Campo de entrada para Gás com ícone de chama
        txt_gas = ft.TextField(
            label="LEITURA GÁS (m³)",
            icon=ft.icons.WHATSHOT,
            border_color="blue900",
            keyboard_type=ft.KeyboardType.NUMBER
        )

        # Lógica para salvar e pular para a próxima unidade
        def proxima_unidade(e):
            if not txt_agua.value:  # Validação de campo vazio
                txt_agua.error_text = "Campo obrigatório"
                page.update()
                return

            # Envia os dados para a função de salvar no database.py
            database.salvar_leitura(unidades[indice[0]], float(
                txt_agua.value), txt_gas.value)

            # Verifica se ainda há unidades na lista
            if indice[0] < len(unidades) - 1:
                indice[0] += 1  # Incrementa o índice
                # Atualiza o texto da tela
                lbl_unidade.value = f"UNIDADE: {unidades[indice[0]]}"
                txt_agua.value = ""  # Limpa campos para a próxima leitura
                txt_gas.value = ""
            else:
                lbl_unidade.value = "✅ Medições Concluídas!"
                btn_proximo.disabled = True  # Desativa o botão ao finalizar
            page.update()

        btn_proximo = ft.ElevatedButton(
            "SALVAR E PRÓXIMO",
            bgcolor="blue900",
            color="white",
            on_click=proxima_unidade,
            width=300
        )

        # Container que agrupa os elementos da Medição
        container_medicao = ft.Column([
            ft.Text("AGUAFLOW - MEDIÇÃO", size=14, color="grey"),
            ft.Divider(),
            lbl_unidade,
            ft.Container(height=10),
            txt_agua,
            txt_gas,
            ft.Container(height=10),
            btn_proximo
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, visible=True)

        # --- COMPONENTES DA ABA 2: RELATÓRIO PDF ---
        def gerar_pdf_clique(e):
            nome_arquivo = database.gerar_pdf_relatorio()  # Chama função do banco
            # Exibe aviso de confirmação na parte inferior (SnackBar)
            page.snack_bar = ft.SnackBar(
                ft.Text(f"Relatório gerado: {nome_arquivo}"), bgcolor="green")
            page.snack_bar.open = True
            page.update()

        # Container que agrupa os elementos do Relatório
        container_relatorio = ft.Column([
            ft.Text("RELATÓRIOS", size=22, weight="bold", color="blue900"),
            ft.Divider(),
            ft.Text(
                "Clique abaixo para exportar os dados do mês em formato PDF.", text_align="center"),
            ft.Container(height=20),
            ft.ElevatedButton(
                "GERAR PDF MENSAL",
                icon=ft.icons.PICTURE_AS_PDF,
                bgcolor="red700",
                color="white",
                width=300,
                on_click=gerar_pdf_clique
            )
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, visible=False)

        # --- LÓGICA DA BARRA DE NAVEGAÇÃO (MENU INFERIOR) ---
        def mudar_aba(e):
            # Controla a visibilidade baseada no índice clicado (0 ou 1)
            container_medicao.visible = (e.control.selected_index == 0)
            container_relatorio.visible = (e.control.selected_index == 1)
            page.update()

        # Cria a barra de menu inferior
        page.navigation_bar = ft.NavigationBar(
            destinations=[
                ft.NavigationDestination(icon=ft.icons.EDIT, label="Medição"),
                ft.NavigationDestination(
                    icon=ft.icons.ASSESSMENT, label="Relatório"),
            ],
            on_change=mudar_aba,
            bgcolor="blue900",
            selected_index=0,
        )

        page.add(container_medicao, container_relatorio)
        page.update()

    # --- TELA DE LOGIN (TELA QUE ABRE PRIMEIRO) ---
    # Carrega a imagem do logo do condomínio
    logo = ft.Image(src="logo.jpeg", width=220, height=220)

    # Campos de Usuário e Senha
    txt_user = ft.TextField(label="Usuário", width=300)
    txt_pass = ft.TextField(label="Senha", width=300,
                            password=True, can_reveal_password=True)

    # Validação simples de acesso
    def validar_login(e):
        if txt_user.value == "admin" and txt_pass.value == "123":
            carregar_sistema_principal()  # Libera o acesso ao sistema
        else:
            # Mostra erro se a senha estiver errada
            page.snack_bar = ft.SnackBar(
                ft.Text("Acesso Negado: Verifique usuário e senha"), bgcolor="red")
            page.snack_bar.open = True
            page.update()

    btn_login = ft.ElevatedButton(
        "ENTRAR NO SISTEMA",
        on_click=validar_login,
        bgcolor="blue900",
        color="white",
        width=300,
        height=50
    )

    # Adiciona os elementos de login na página inicial
    page.add(
        logo,
        ft.Text("CONDOMÍNIO EDIF.VIVERE PRUDENTE",
                weight="bold", color="blue900"),
        ft.Container(height=20),
        txt_user,
        txt_pass,
        ft.Container(height=10),
        btn_login
    )


# Inicializa a aplicação
if __name__ == "__main__":
    ft.app(target=main)
