import flet as ft
import auth, reports, utils, database as db, medicao
import os 
import sys

def main(page: ft.Page):
    # 1. Configurações Iniciais da Página
    page.theme_mode = ft.ThemeMode.DARK  
    page.title = "ÁguaFlow - Vivere Prudente"
    page.window_width = 450
    page.window_height = 800
    page.bgcolor = ft.Colors.SURFACE_CONTAINER_HIGHEST# Força o fundo escuro para evitar faixas brancas
    
    # Inicializa o Banco de Dados
    db.init_db()

    # 2. Definição das Funções de Navegação (Dentro do escopo da main)
    def navegar_menu(perfil):
        page.controls.clear()
        # Criamos um Container principal para garantir que o fundo ocupe tudo
        coluna = ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15)
        
        coluna.controls.append(ft.Text(f"Perfil: {perfil.upper()}", color="blue", weight="bold", size=20))
        coluna.controls.append(ft.Divider())

        # Botão Iniciar Leitura
        coluna.controls.append(ft.FilledButton("INICIAR LEITURA", 
            on_click=lambda _: (page.controls.clear(), page.add(medicao.montar_tela(page, lambda: navegar_menu(perfil))), page.update()), 
            width=280))
        
        # Botões de ADMIN
        if perfil == "admin":
            coluna.controls.append(ft.FilledButton("IMPRIMIR ETIQUETAS QR", on_click=abrir_dialogo_qr, width=280))
            
            def acao_relatorio(e):
                try:
                    dados = db.get_dados()
                    nome_arquivo = reports.gerar_relatorio_leituras_pdf(dados)
                    if os.path.exists(nome_arquivo):
                        os.startfile(nome_arquivo) 
                    page.snack_bar = ft.SnackBar(ft.Text(f"Relatório aberto: {nome_arquivo}"), bgcolor="green")
                except Exception as ex:
                    page.snack_bar = ft.SnackBar(ft.Text(f"Erro ao gerar: {ex}"), bgcolor="red")
                page.snack_bar.open = True
                page.update()
            
            coluna.controls.append(ft.FilledButton("RELATÓRIOS MENSAL", on_click=acao_relatorio, width=280))

            def resetar_clique(e):
                db.fechar_mes_e_resetar()
                page.snack_bar = ft.SnackBar(ft.Text("Mês encerrado com sucesso!"), bgcolor="blue")
                page.snack_bar.open = True
                navegar_menu(perfil) 

            coluna.controls.append(ft.FilledButton("ENCERRAR MÊS ATUAL", 
                on_click=resetar_clique, style=ft.ButtonStyle(bgcolor="red", color="white"), width=280))

        # Botão Ajuda
        coluna.controls.append(ft.OutlinedButton("AJUDA / GUIA", on_click=lambda _: abrir_ajuda(perfil), width=280))
        
        # Botão Logout
        coluna.controls.append(
            ft.TextButton("LOGOUT / TROCAR USUÁRIO", 
                on_click=lambda _: (page.controls.clear(), page.add(auth.criar_tela_login(page, navegar_menu)), page.update()), 
                icon="logout")
        )

        # Lógica do Ícone de Status
        leitura_em_andamento = db.buscar_proximo_pendente() is not None
        cor_status = "green" if leitura_em_andamento else "red"
        texto_dica = "Leituras em andamento" if leitura_em_andamento else "Tudo lido"

        coluna.controls.append(
            ft.IconButton(
                icon="power_settings_new", 
                icon_color=cor_status, 
                icon_size=40,
                tooltip=texto_dica,
                on_click=lambda _: page.window_destroy()
            )
        )

        # Adiciona tudo em um container expandido para evitar a faixa branca
        page.add(ft.Container(content=coluna, padding=20, expand=True))
        page.update()

    def abrir_dialogo_qr(e):
        unid_input = ft.TextField(label="Apto (vazio para todos)")
        def confirmar(e):
            u = unid_input.value.strip()
            dados_atuais = db.get_dados()
            lista = [u] if u else [str(r[1]) for r in dados_atuais]
            pdf_etiquetas = reports.gerar_pdf_etiquetas_qr(lista)
            if os.path.exists(pdf_etiquetas):
                os.startfile(pdf_etiquetas)
            page.dialog.open = False
            page.update()

        page.dialog = ft.AlertDialog(
            title=ft.Text("Gerar QR"), 
            content=unid_input, 
            actions=[ft.TextButton("GERAR", on_click=confirmar)]
        )
        page.dialog.open = True
        page.update()

    def abrir_ajuda(perfil):
        page.controls.clear()
        page.add(utils.montar_tela_ajuda(lambda _: navegar_menu(perfil)))
        page.update()

    # 3. Início do Fluxo: Tela de Login
    page.add(auth.criar_tela_login(page, navegar_menu))

# 4. Execução do App (Sempre no final do arquivo e fora da função main)
if __name__ == "__main__":
    ft.run(main)