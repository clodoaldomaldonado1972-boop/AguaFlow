from views.sincronizacao import SincronizadorUI
from views.medicao import montar_tela_medicao
from utils.backup import executar_backup_seguranca
from utils.updater import AppUpdater
from database.sync_service import SyncService
from database.database import Database
import flet as ft
import asyncio
import os
import sys
import gc
from pathlib import Path

# Adiciona o diretório raiz do projeto ao sys.path para importações relativas
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importações dos módulos do aplicativo


async def main(page: ft.Page):
    page.title = "AguaFlow - Teste de Fluxo Completo"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#121417"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    status_text = ft.Text("Iniciando teste...", size=18, weight="bold")
    progress_bar = ft.ProgressBar(width=300, visible=False)
    log_output = ft.Column(scroll=ft.ScrollMode.ALWAYS, expand=True)

    def log_message(message, color=ft.colors.WHITE):
        log_output.controls.append(ft.Text(message, color=color))
        page.update()

    async def run_full_test(e):
        status_text.value = "Preparando ambiente..."
        progress_bar.visible = True
        page.update()
        log_output.controls.clear()

        try:
            log_message("1. Inicializando tabelas do banco de dados local...")
            await asyncio.to_thread(Database.inicializar_tabelas)
            await asyncio.to_thread(SyncService.init_sync_log_table)
            log_message("   Tabelas inicializadas com sucesso.")

            log_message("2. Simulando medição offline para 3 unidades...")
            unidades = Database._gerar_lista_unidades()
            if not unidades:
                log_message(
                    "   Nenhuma unidade encontrada. Por favor, popule o banco de dados.", ft.colors.RED)
                return

            for i in range(min(3, len(unidades))):
                unidade = unidades[i]
                valor_agua = 100.0 + i
                log_message(
                    f"   Registrando leitura para unidade {unidade}: {valor_agua} m³")
                await asyncio.to_thread(Database.salvar_leitura, unidade, valor_agua, None, "AGUA", "01/01/2024 10:00:00")
            log_message("   Medições offline simuladas com sucesso.")

            log_message(
                "3. Iniciando sincronização assíncrona com Supabase...")
            sincronizador_ui = SincronizadorUI(page)
            await sincronizador_ui.executar_sincronismo(None)
            log_message(
                "   Sincronização concluída. Verifique os logs acima para detalhes.")

            log_message("4. Verificando backup de segurança...")
            await asyncio.to_thread(executar_backup_seguranca)
            log_message("   Backup de segurança executado.")

            status_text.value = "Teste de fluxo completo CONCLUÍDO com sucesso!"
            status_text.color = ft.colors.GREEN

        except Exception as ex:
            log_message(f"ERRO CRÍTICO DURANTE O TESTE: {ex}", ft.colors.RED)
            status_text.value = "Teste de fluxo completo FALHOU!"
            status_text.color = ft.colors.RED
        finally:
            progress_bar.visible = False
            gc.collect()  # Limpar memória após o teste
            page.update()

    page.add(
        ft.Column([
            status_text,
            progress_bar,
            ft.ElevatedButton("EXECUTAR TESTE COMPLETO",
                              on_click=run_full_test),
            ft.Divider(),
            log_output
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True)
    )

if __name__ == "__main__":
    ft.app(target=main)
