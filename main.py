import flet as ft
import os
import auth
import reports
import utils
import medicao
import database as db
import gerador_qr  # <--- NOVO: Para garantir que as imagens existam
import gerador_pdf  # <--- NOVO: Caso precise de algum suporte inicial

# --- INICIALIZAÇÃO E MANUTENÇÃO DO SISTEMA ---


def inicializar_sistema():
    db.init_db()  # Garante que o banco e as tabelas existem

    # Tenta resetar o status se necessário (Manutenção)
    try:
        # Se você tiver a função forcar_reset_agora no database.py:
        # db.forcar_reset_agora()

        # Caso queira garantir que o app comece pronto para leitura:
        conn = db.get_connection()
        cursor = conn.cursor()
        # Opcional: Limpa pendências antigas ao iniciar
        # cursor.execute("UPDATE leituras SET status = 'pendente' WHERE status IS NULL")
        conn.commit()
        conn.close()
        print("✅ BANCO DE DADOS CONECTADO!")
    except Exception as e:
        print(f"⚠️ Erro na manutenção inicial: {e}")

    # GARANTIA DOS QR CODES: Se a pasta estiver vazia, gera tudo
    if not os.path.exists("qrcodes") or len(os.listdir("qrcodes")) < 10:
        print("🚀 Gerando base de QR Codes inicial...")
        gerador_qr.gerar_todos_vivere()


def main(page: ft.Page):
    # --- 1. CONFIGURAÇÃO DE INTERFACE ---
    page.title = "Vivere Flow - Gestão de Consumo"
    page.window_bgcolor = "#1A1C1E"
    page.bgcolor = "#1A1C1E"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 450
    page.window_height = 800
    page.window_resizable = False
    page.padding = 0
    page.spacing = 0

    # Inicializa banco e arquivos
    inicializar_sistema()

    # --- 2. PALCO PRINCIPAL ---
    palco = ft.Container(expand=True, bgcolor="#1A1C1E")

    # --- 3. FUNÇÕES DE NAVEGAÇÃO ---
    def carregar_modulo(conteudo):
        palco.content = ft.Container(
            content=conteudo,
            padding=20,
            expand=True,
            bgcolor="#1A1C1E",
            alignment=ft.alignment.top_center  # Centraliza o conteúdo no topo
        )
        page.update()

    def navegar_menu(perfil):
        def voltar_e_recarregar(recarregar_medicao=False):
            if recarregar_medicao:
                carregar_modulo(medicao.montar_tela(page, voltar_e_recarregar))
            else:
                navegar_menu(perfil)

        # Layout do Menu Principal
        botoes = [
            ft.Icon(ft.Icons.WATER_DROP, color="blue", size=50),
            ft.Text(f"BEM-VINDO", size=14, color="white54"),
            ft.Text(f"{perfil.upper()}", color="white",
                    weight="bold", size=22),
            ft.Divider(color="white10", height=40),

            ft.FilledButton(
                "INICIAR LEITURA",
                width=300,
                icon=ft.Icons.QR_CODE_SCANNER,
                on_click=lambda _: carregar_modulo(
                    medicao.montar_tela(page, voltar_e_recarregar))
            ),

            ft.FilledButton(
                "RELATÓRIOS MENSAL",
                width=300,
                icon=ft.Icons.PIE_CHART,
                on_click=lambda _: carregar_modulo(
                    reports.montar_tela_relatorios(page, lambda: navegar_menu(perfil)))
            ),

            ft.FilledButton(
                "AJUDA / CONFIGURAÇÕES",
                width=300,
                icon=ft.Icons.SETTINGS,
                on_click=lambda _: carregar_modulo(
                    utils.montar_tela_ajuda(page, lambda: navegar_menu(perfil)))
            ),

            ft.Container(height=40),
            ft.TextButton("Encerrar Sessão", icon=ft.Icons.LOGOUT,
                          on_click=lambda _: iniciar_app())
        ]

        carregar_modulo(ft.Column(
            botoes,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=15
        ))

    def iniciar_app():
        carregar_modulo(auth.criar_tela_login(page, navegar_menu))

    # --- 4. EXECUÇÃO ---
    page.add(palco)
    iniciar_app()
    page.update()


if __name__ == "__main__":
    # Garante melhor performance visual no Windows/Android
    os.environ["FLET_RENDERER"] = "skia"
    ft.app(target=main)  # Use ft.app para rodar corretamente
