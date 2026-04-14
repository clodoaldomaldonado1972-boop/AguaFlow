import flet as ft
import asyncio
import datetime
from utils.diagnostico import DiagnosticoSistema
# Sincronizado com o seu alertas_engine.py
from utils.alertas_engine import enviar_alerta_MESSAGE

def montar_tela_saude(page: ft.Page, voltar):
    # --- COMPONENTES DE STATUS ---
    icon_db = ft.Icon(ft.icons.STORAGE_ROUNDED, color="grey", size=30)
    lbl_db_status = ft.Text("Aguardando...", color="grey", size=16, weight="bold")
    lbl_db_detalhe = ft.Text("Verificando integridade", size=12, color="white54")

    # Lista de logs visual
    lst_logs = ft.ListView(expand=1, spacing=5, padding=10)

    def adicionar_log(mensagem, cor="white54"):
        hora = datetime.datetime.now().strftime("%H:%M:%S")
        lst_logs.controls.insert(0, ft.Text(f"[{hora}] {mensagem}", color=cor, size=12))
        page.update()

    async def executar_diagnostico(e=None):
        adicionar_log("Iniciando varredura de integridade...", "blue")
        
        # Chama a função unificada que testa banco e ambiente
        res_geral, msg_geral = await DiagnosticoSistema.executar_checkup_completo()
        
        icon_db.color = "green" if res_geral else "red"
        lbl_db_status.value = "OPERACIONAL" if res_geral else "FALHA"
        lbl_db_detalhe.value = msg_geral
        adicionar_log(f"Resultado: {msg_geral}", "green" if res_geral else "red")
        
        page.update()

    def reportar_erro_suporte(e):
        msg = (
            "🛠️ *SUPORTE TÉCNICO ÁGUAFLOW*\n"
            "Instabilidade detectada no Vivere Prudente.\n"
            f"Status Geral: {lbl_db_status.value}\n"
            f"Detalhe: {lbl_db_detalhe.value}"
        )
        # Usando a função correta importada
        enviar_alerta_MESSAGE(page, msg)
        adicionar_log("Chamado enviado ao suporte", "orange")

    def criar_card_status(titulo, icone, status, detalhe):
        return ft.Container(
            content=ft.Column([
                ft.Text(titulo, size=10, color="white54", weight="bold"),
                ft.Row([icone, ft.Column([status, detalhe], spacing=0)]),
            ], spacing=10),
            bgcolor="white10", padding=15, border_radius=10, expand=True
        )

    # Inicia diagnóstico ao abrir
    asyncio.create_task(executar_diagnostico())

    return ft.View(
        route="/dashboard_saude",
        appbar=ft.AppBar(
            title=ft.Text("Saúde do Sistema"),
            leading=ft.IconButton(ft.icons.ARROW_BACK, on_click=voltar),
            bgcolor="black26"
        ),
        controls=[
            # CONTAINER resolve o erro de padding da Column
            ft.Container(
                padding=20,
                content=ft.Column([
                    ft.Text("MÓDULOS CRÍTICOS", size=16, weight="bold"),
                    ft.Row([
                        criar_card_status("SISTEMA E BANCO", icon_db, lbl_db_status, lbl_db_detalhe),
                    ], spacing=15),

                    ft.Divider(height=20, color="white10"),
                    ft.Text("LOGS DE EVENTOS", size=16, weight="bold"),
                    ft.Container(content=lst_logs, bgcolor="black26", border_radius=10, height=250),

                    ft.ElevatedButton(
                        "REESCANEAR SISTEMA",
                        icon=ft.icons.REFRESH_ROUNDED,
                        on_click=executar_diagnostico,
                        width=400, height=50,
                        style=ft.ButtonStyle(bgcolor="blue", color="white")
                    ),
                    ft.TextButton(
                        "Relatar erro ao suporte técnico",
                        icon=ft.icons.SUPPORT_AGENT,
                        on_click=reportar_erro_suporte
                    )
                ], spacing=15)
            )
        ]
    )