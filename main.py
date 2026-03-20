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
  2. Vê a sequência de apartamentos (1601, 1602, ..., 101)
  3. Digita a leitura do medidor
  4. App VALIDA em tempo real (rejeita letras, símbolos, valores inválidos)
  5. Salva no "Cofre Local" (banco SQLite local)
  6. Quando Wi-Fi volta, sincroniza com Supabase automaticamente

================================================================================
"""

import views.medicao as medicao
import database.database as db
import flet as ft
import sys
import os

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
    db.init_db()

    palco = ft.Container(expand=True)

    status_icon = ft.Icon(ft.icons.Icons.CLOUD_QUEUE, color='gray', size=16)
    status_text = ft.Text('Supabase: desconectado', color='gray')
    status_bar = ft.Row(
        [status_icon, ft.Text(' ', width=8), status_text],
        alignment=ft.MainAxisAlignment.START
    )

    async def voltar_ao_menu():
        palco.content = menu_principal
        page.update()

    async def iniciar_leitura(e):
        tela_med = await medicao.montar_tela(page, voltar_ao_menu, status_icon, status_text)
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

# USANDO FT.RUN QUE É O CORRETO NA VERSÃO 0.82
if __name__ == "__main__":
    ft.run(main, view=ft.AppView.WEB_BROWSER, port=8080, host="0.0.0.0")
