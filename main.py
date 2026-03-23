"""
================================================================================
🌊 AGUAFLOW - SISTEMA DE LEITURA DE HIDRÔMETROS
================================================================================
Projeto: Condomínio Vivere Prudente
Função: Capturar leituras de água/gás de forma sequencial e offline

ARQUITETURA DO SISTEMA:
  📁 database/  → "COFRE LOCAL" (dados seguros, validados, offline-first)
  📁 views/     → "VITRINE" (interface amigável para o zelador)
  📄 main.py    → Orquestrador principal

FLUXO DE USO:
  1. Zelador abre app no celular
  2. Vê a sequência de apartamentos (166, 165, ..., 11)
  3. Digita a leitura do medidor
  4. App VALIDA em tempo real (rejeita letras, símbolos, valores inválidos)
  5. Salva no "Cofre Local" (banco SQLite local)
  6. Quando Wi-Fi volta, sincroniza com Supabase automaticamente

================================================================================
"""

import socket
import views.medicao as medicao
import database.database as db
import flet as ft
import sys
import os
import threading
import time

# ========== IMPORTS DINÂMICOS ==========
# Sistema inteligente para encontrar módulos nas pastas database/ e views/
# Funciona independente da localização do projeto

# Adiciona pastas ao path do Python
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, 'database'))
sys.path.insert(0, os.path.join(current_dir, 'views'))

# Importa módulos das pastas organizadas


async def main(page: ft.Page):
    page.theme_mode = ft.ThemeMode.DARK
    db.Database.init_db()

    # --- ROTINA DE SYNC AUTOMÁTICO (Background) ---
    def run_auto_sync():
        """Tenta enviar dados pendentes a cada 5 minutos em background."""
        while True:
            try:
                # Tenta processar a fila (envia se tiver internet)
                db.Database.processar_fila()
            except Exception as e:
                print(f"⚠️ Erro no Auto-Sync: {e}")
            time.sleep(300)  # Pausa de 5 minutos (300 segundos)

    # Inicia a thread como daemon (morre quando o app fecha)
    threading.Thread(target=run_auto_sync, daemon=True).start()

    palco = ft.Container(expand=True)

    # Barra de status da conexão com a nuvem
    status_icon = ft.Icon(ft.icons.Icons.CLOUD_QUEUE, color='gray', size=16)
    # Estado inicial: aguardando conexão (offline)
    status_text = ft.Text('Aguardando Conexão 🔴', color='gray')
    status_bar = ft.Row(
        [status_icon, ft.Text(' ', width=8), status_text],
        alignment=ft.MainAxisAlignment.START
    )

    async def voltar_ao_menu():
        palco.content = menu_principal
        page.update()

    async def iniciar_leitura(e):
        await atualizar_tela_medicao()

    async def atualizar_tela_medicao():
        tela_med = await medicao.montar_tela(
            page=page,
            voltar_ao_menu=voltar_ao_menu,
            on_next=atualizar_tela_medicao
        )
        palco.content = tela_med
        page.update()

    menu_principal = ft.Column([
        ft.Container(height=50),
        ft.Icon(ft.Icons.WATER_DROP, size=100, color="blue"),
        ft.Text("AGUA FLOW", size=30, weight="bold"),
        ft.FilledButton(content=ft.Text("INICIAR LEITURAS"),
                        on_click=iniciar_leitura, width=250, height=50),
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    page.add(ft.Column([palco, ft.Divider(height=1), status_bar], expand=True))
    await voltar_ao_menu()


def find_free_port(start_port=8080, max_port=8090):
    for port in range(start_port, max_port + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("0.0.0.0", port))
                return port
            except OSError:
                continue
    raise OSError(
        f"Nenhuma porta livre encontrada entre {start_port} e {max_port}.")


# USANDO FT.APP para compatibilidade com flet >= 0.10
if __name__ == "__main__":
    porta = find_free_port(8080, 8090)
    print(f"Iniciando AguaFlow em http://0.0.0.0:{porta}")
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=porta, host="0.0.0.0")
