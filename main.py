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

    # =============================================================================
# 1. INICIALIZAÇÃO (DEVE VIR ANTES DO MAIN)
# =============================================================================


def inicializar_sistema():
    """Garante que o banco e pastas existam antes do app carregar."""
    db.init_db()
    pasta_mensal = datetime.now().strftime("Relatorios_%Y_%m")
    if not os.path.exists(pasta_mensal):
        os.makedirs(pasta_mensal)
    print("✅ SISTEMA AGUA FLOW CONECTADO E PRONTO!")

# =============================================================================
# 2. APP PRINCIPAL
# =============================================================================


async def main(page: ft.Page):
    # ... (todo o seu código da função main aqui dentro) ...

    # Agora chamamos a inicialização que já foi definida acima
    inicializar_sistema()

    # ... (restante do código: palco, carregar_modulo, etc) ...
    page.add(palco)
    await iniciar_app()

# =============================================================================
# 3. EXECUÇÃO (ATUALIZADA)
# =============================================================================

if __name__ == "__main__":
    # Mantemos o ft.app, mas ignore o aviso por enquanto,
    # ou use ft.app(target=main, ...) se estiver na versão mais nova.
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=8080, host="0.0.0.0")
