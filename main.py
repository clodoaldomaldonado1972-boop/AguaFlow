from datetime import datetime
import flet as ft
import os
import auth
import reports
import utils
import medicao
import database as db

# ... inicializar_sistema permanece igual ...

# 1. Transformamos o main em ASYNC


async def main(page: ft.Page):
    page.title = "Agua Flow - Vivere Prudente"
    page.window_bgcolor = "#1A1C1E"
    page.bgcolor = "#1A1C1E"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 450
    page.window_height = 800
    page.window_resizable = False
    page.padding = 0
    page.spacing = 0

    inicializar_sistema()

    palco = ft.Container(expand=True, bgcolor="#1A1C1E")

    # 2. carregar_modulo agora precisa ser ASYNC para suportar o conteúdo vindo da câmera
    async def carregar_modulo(conteudo):
        page.overlay.clear()
        palco.content = ft.Container(
            content=conteudo,
            padding=20,
            expand=True,
            bgcolor="#1A1C1E",
            alignment=ft.Alignment(0, -1)
        )
        await page.update_async()  # Usamos a versão async do update

    async def navegar_menu(perfil):
        try:
            page.clean()
            page.add(palco)

            # 3. A função de retorno agora aguarda o medicao.montar_tela
            async def voltar_e_recarregar(recarregar_medicao=False):
                if recarregar_medicao:
                    # USAMOS AWAIT AQUI!
                    await carregar_modulo(await medicao.montar_tela(page, voltar_e_recarregar))
                else:
                    await navegar_menu(perfil)

            botoes = [
                ft.Icon(ft.Icons.WATER_DROP, color="blue", size=60),
                ft.Text(f"OPERADOR: {perfil.upper()}",
                        color="white", weight="bold", size=20),
                ft.Divider(color="white10", height=40),

                ft.FilledButton(
                    "INICIAR LEITURA",
                    width=300, height=50,
                    icon=ft.Icons.QR_CODE_SCANNER,
                    # Lambda agora chama a versão async
                    on_click=lambda _: page.run_task(
                        lambda: carregar_modulo(
                            medicao.montar_tela(page, voltar_e_recarregar))
                    )
                ),
                # ... outros botões seguem o mesmo padrão ...
            ]

            # Para simplificar o on_click do botão iniciar:
            async def ir_para_leitura(e):
                conteudo = await medicao.montar_tela(page, voltar_e_recarregar)
                await carregar_modulo(conteudo)

            # Substitua o on_click do INICIAR LEITURA por:
            botoes[3].on_click = ir_para_leitura

            await carregar_modulo(ft.Column(botoes, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15))

        except Exception as erro:
            print(f"❌ ERRO NA TROCA DE TELA: {erro}")

    async def iniciar_app():
        await carregar_modulo(auth.criar_tela_login(page, navegar_menu))

    page.add(palco)
    await iniciar_app()

if __name__ == "__main__":
    # Mudança vital: ft.app agora aponta para a função async
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=8080, host="0.0.0.0")
