import flet as ft
from views import styles as st 

VERSION = "1.1.2"

def montar_menu(page: ft.Page):
    def limpar_sessao_usuario():
        if hasattr(page, "client_storage") and page.client_storage:
            return page.client_storage.remove_async("user_email")
        page.session.set("user_email", None)
        return None

    # --- FUNÇÃO DE LOGOUT (LIMPA A SESSÃO) ---
    async def acao_sair(e):
        try:
            # 1. Remove o e-mail do armazenamento local do dispositivo
            resultado = limpar_sessao_usuario()
            if resultado is not None:
                await resultado
            # 2. Limpa a variável de memória global da página
            page.user_email = None
            print("Saída do sistema: Sessão encerrada.")
            # 3. Redireciona para a tela de login (rota raiz)
            page.go("/")
        except Exception as ex:
            print(f"Erro ao sair: {ex}")

    # --- FUNÇÃO AUXILIAR PARA CRIAR BOTÕES ---
    def criar_botao_menu(texto, icone, rota, estilo=None):
        return ft.Container(
            content=ft.ElevatedButton(
                content=ft.Row([
                    ft.Icon(icone, size=24),
                    ft.Text(texto, size=14, weight="bold"),
                ], alignment=ft.MainAxisAlignment.START, spacing=15),
                # Tenta usar o estilo do styles.py, senão usa um padrão básico
                style=estilo if estilo else getattr(st, "BTN_MAIN", None),
                width=300,
                height=55,
                on_click=lambda _: page.go(rota),
            ),
            padding=ft.padding.symmetric(vertical=5),
        )

    # --- ESTRUTURA DA VIEW ---
    view = ft.View(
        route="/menu",
        bgcolor=getattr(st, "BG_DARK", "#121417"),
        appbar=ft.AppBar(
            title=ft.Text("AguaFlow - Menu Principal", size=18, weight="bold"),
            bgcolor=ft.colors.SURFACE_VARIANT,
            center_title=True,
            automatically_imply_leading=False, # Remove o botão 'voltar' no menu
            elevation=2
        ),
        controls=[
            ft.Column([
                ft.Container(height=10),
                
                # GRUPO 1: OPERAÇÃO
                ft.Text("OPERAÇÃO DE CAMPO", size=12, color="grey", weight="bold"),
                criar_botao_menu("NOVA MEDIÇÃO", ft.icons.SPEED, "/medicao"),
                criar_botao_menu("SCANNER OCR", ft.icons.QR_CODE_SCANNER, "/scanner"),

                ft.Divider(height=20, color="transparent"),
                
                # GRUPO 2: DADOS
                ft.Text("DADOS E RELATÓRIOS", size=12, color="grey", weight="bold"),
                criar_botao_menu("SINCRONIZAR", ft.icons.CLOUD_SYNC, "/sincronizar"),
                criar_botao_menu("HISTÓRICO", ft.icons.ASSIGNMENT_OUTLINED, "/relatorios"),

                ft.Divider(height=20, color="transparent"),
                
                # GRUPO 3: GESTÃO
                ft.Text("GESTÃO E SUPORTE", size=12, color="grey", weight="bold"),
                criar_botao_menu("DASHBOARD", ft.icons.DASHBOARD_ROUNDED, "/dashboard"),
                criar_botao_menu("SAÚDE DO SISTEMA", ft.icons.MONITOR_HEART, "/dashboard_saude"),
                criar_botao_menu("QR CODES", ft.icons.QR_CODE_2, "/qrcodes"),
                criar_botao_menu("CONFIGURAÇÕES", ft.icons.SETTINGS_OUTLINED, "/configuracoes", estilo=getattr(st, "BTN_SPECIAL", None)),
                criar_botao_menu("AJUDA & SUPORTE", ft.icons.HELP_OUTLINE, "/ajuda"),

                ft.Container(height=30),
                
                # BOTÃO DE SAÍDA (LOGOUT)
                ft.Row([
                    ft.TextButton(
                        "Sair do Sistema", 
                        icon=ft.icons.LOGOUT, 
                        icon_color="red", 
                        on_click=acao_sair # Chama a função assíncrona de limpeza
                    ),
                ], alignment=ft.MainAxisAlignment.CENTER),
                
                ft.Divider(height=10, color="transparent"),
                ft.Text(f"v{VERSION} - Residencial Vivere", size=10, color=ft.colors.GREY_600),
                ft.Container(height=20),

            ], 
            horizontal_alignment=ft.CrossAxisAlignment.CENTER, 
            scroll=ft.ScrollMode.ALWAYS, # Permite scroll em ecrãs pequenos
            expand=True
            )
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER
    )
    
    return view