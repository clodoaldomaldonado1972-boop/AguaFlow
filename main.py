import sys
import os
import warnings
import asyncio
import flet as ft

# Compatibilidade de ícones entre versões do Flet:
# no desktop atual, os ícones válidos estão em ft.Icons (I maiúsculo).
if hasattr(ft, "Icons"):
    ft.icons = ft.Icons

# 1. AJUSTE DE PATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
warnings.filterwarnings("ignore", category=DeprecationWarning)

# 2. IMPORTS (Módulos e Views)
import views.auth as auth_view
from database.database import Database
# No topo do arquivo main.py
from database.sync_service import SyncService
from views.autenticacao import montar_tela_autenticacao
from views.menu_principal import montar_menu
from views.medicao import montar_tela_medicao
from views.scanner_view import montar_tela_scanner
from views.sincronizacao import montar_tela_sincronizacao
from views.relatorio_view import montar_tela_relatorio
from views.dashboard import montar_tela_dashboard
from views.dashboard_saude import montar_tela_saude
from views.configuracoes import montar_tela_configs
from views.qrcodes_view import montar_tela_qrcodes
from views.ajuda_view import montar_tela_ajuda
from views.recuperar_senha_email import criar_tela_recuperacao

async def main(page: ft.Page):
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#121417"
    page.title = "AguaFlow - Edifício Vivere"

    async def route_change(e):
        try:
            print(f"Mudando rota para: {page.route}")
            page.views.clear()
            
            # MAPEAMENTO DAS ROTAS
            if page.route == "/":
                try:
                    page.views.append(auth_view.criar_tela_login(page))
                except Exception as e:
                    # ISSO VAI MOSTRAR O ERRO REAL NA TELA PRETA
                    page.views.append(ft.View("/", [ft.Text(f"ERRO: {e}", color="red")]))
            elif page.route == "/registro":
                page.views.append(montar_tela_autenticacao(page))
            elif page.route == "/esqueci_senha":
                page.views.append(auth_view.montar_tela_esqueci_senha(page))
            elif page.route == "/recuperar-email":
                page.views.append(criar_tela_recuperacao(page))
            elif page.route == "/menu":
                print("Montando tela do menu principal")
                page.views.append(montar_menu(page))
            elif page.route == "/medicao":
                page.views.append(montar_tela_medicao(page))
            elif page.route == "/scanner":
                page.views.append(montar_tela_scanner(page))
            elif page.route == "/sincronizar":
                page.views.append(montar_tela_sincronizacao(page))
            elif page.route == "/relatorios":
                page.views.append(montar_tela_relatorio(page))
            elif page.route == "/dashboard":
                page.views.append(montar_tela_dashboard(page, lambda _: page.go("/menu")))
            elif page.route == "/dashboard_saude":
                page.views.append(montar_tela_saude(page, lambda _: page.go("/menu")))
            # No main.py, altere para:
            elif page.route == "/configuracoes":
                view_configs = await montar_tela_configs(page, lambda _: page.go("/menu")) # Mantenha o await
                page.views.append(view_configs)
            elif page.route == "/qrcodes":
                page.views.append(montar_tela_qrcodes(page, lambda _: page.go("/menu")))
            elif page.route == "/ajuda":
                page.views.append(montar_tela_ajuda(page, lambda _: page.go("/menu")))
            else:
                page.views.append(
                    ft.View(
                        route=page.route,
                        controls=[
                            ft.Text("Rota não encontrada", size=20, color="red"),
                            ft.Text(f"Rota: {page.route}", color="white70"),
                            ft.ElevatedButton("Voltar ao menu", on_click=lambda _: page.go("/menu")),
                        ],
                        vertical_alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    )
                )

            page.update()
        except Exception as ex:
            print(f"ERRO CRITICO NA ROTA {page.route}: {ex}")
            page.views.clear()
            page.views.append(
                ft.View(
                    route=page.route,
                    controls=[
                        ft.Text("Erro ao carregar tela", size=20, color="red"),
                        ft.Text(str(ex), color="white70"),
                        ft.ElevatedButton("Voltar ao menu", on_click=lambda _: page.go("/menu")),
                    ],
                    vertical_alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                )
            )
            page.update()

    async def bootstrap_background():
        """
        Fase 2 do startup: executa inicialização pesada apenas após o primeiro paint.
        """
        try:
            # Garante que a UI tenha oportunidade de pintar antes de I/O.
            await asyncio.sleep(0.1)
            await asyncio.to_thread(Database.inicializar_tabelas)
            await SyncService.init_sync_log_table()
            page.run_task(SyncService.processar_fila)
        except Exception as e:
            print(f"Erro no bootstrap em background: {e}")

    # 1. Registar o evento de mudança de rota.
    # Em Flet Desktop, o callback de rota deve disparar a corrotina via run_task.
    page.on_route_change = lambda e: page.run_task(route_change, e)
    
    # 2. Rota inicial fixa para evitar bloqueio no primeiro paint.
    rota_inicial = "/"
    print(f"Iniciando na rota: {rota_inicial}")

    # 3. Primeiro paint da interface (fase leve).
    # Em alguns builds desktop, o on_route_change não dispara no primeiro page.go("/")
    # quando a rota já é "/". Então renderizamos explicitamente a tela inicial.
    try:
        page.route = rota_inicial
        page.views.clear()
        page.views.append(auth_view.criar_tela_login(page))
        page.update()

        # Mantém o estado de rota consistente para próximas navegações.
        page.go(rota_inicial)
        await asyncio.sleep(0)
        # 4. Bootstrap pesado desacoplado da pintura inicial.
        page.run_task(bootstrap_background)
    except Exception as e:
        print(f"Erro ao iniciar interface: {e}")

if __name__ == "__main__":
    # Garante que o app rode em modo Desktop nativo
    ft.app(target=main)