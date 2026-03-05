import flet as ft
import database as db      # Importa o bloco de dados
import medicao            # Importa o bloco de medição que você acabou de criar

def main(page: ft.Page):
    # Configurações de visual do Maestro
    page.title = "ÁguaFlow - Vivere Prudente"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 400
    page.window_height = 750
    
    # Inicializa o alicerce (Banco de Dados)
    db.init_db()

    def navegar_para_medicao(e):
        page.controls.clear()
        # O Maestro pede para o módulo 'medicao' assumir o controle da tela
        page.add(medicao.montar_tela(page, navegar_para_menu))
        page.update()

    def navegar_para_menu(e=None):
        page.controls.clear()
        page.add(
            ft.Container(
                padding=30,
                content=ft.Column([
                    ft.Image(src="https://cdn-icons-png.flaticon.com/512/3105/3105807.png", width=100), # Ícone ilustrativo
                    ft.Text("VIVERE PRUDENTE", size=28, weight="bold", color="#002868"),
                    ft.Text("Gestão de Consumo", size=16, color="grey"),
                    ft.Divider(height=40),
                    
                    ft.ElevatedButton(
                        "INICIAR LEITURA", 
                        icon=ft.icons.PLAY_ARROW,
                        on_click=navegar_para_medicao,
                        width=280, height=60,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
                    ),
                    
                    ft.OutlinedButton(
                        "GERAR ETIQUETAS QR", 
                        icon=ft.icons.QR_CODE, 
                        width=280, height=50,
                        on_click=lambda _: print("Ainda vamos criar este bloco!")
                    ),
                    
                    ft.OutlinedButton(
                        "RELATÓRIOS (PDF)", 
                        icon=ft.icons.PICTURE_AS_PDF, 
                        width=280, height=50,
                        on_click=lambda _: print("Ainda vamos criar este bloco!")
                    ),

                    ft.TextButton("Sair do Sistema", icon=ft.icons.EXIT_TO_APP, on_click=lambda _: page.window_destroy())
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            )
        )
        page.update()

    # Inicia o app no Menu
    navegar_para_menu()

ft.run(main)
