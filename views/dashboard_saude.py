import flet as ft
import asyncio
import datetime
from utils.diagnostico import DiagnosticoSistema
from utils.alertas_engine import enviar_alerta_whatsapp 

def montar_tela_saude(page: ft.Page, voltar):
    # --- COMPONENTES DE STATUS (REATIVOS) ---
    icon_db = ft.Icon(ft.Icons.STORAGE_ROUNDED, color="grey", size=30)
    lbl_db_status = ft.Text("Aguardando...", color="grey", size=16, weight="bold")
    lbl_db_detalhe = ft.Text("Verificando banco local", size=12, color="white54")

    icon_net = ft.Icon(ft.Icons.WIFI_ROUNDED, color="grey", size=30)
    lbl_net_status = ft.Text("Aguardando...", color="grey", size=16, weight="bold")
    lbl_net_detalhe = ft.Text("Verificando conexão", size=12, color="white54")

    lst_logs = ft.ListView(expand=1, spacing=5, padding=10)

    # --- FUNÇÃO DE LOG ---
    # Rota Lógica: Registra cada passo do diagnóstico na lista visual
    def adicionar_log(mensagem, cor="white54"):
        hora = datetime.datetime.now().strftime("%H:%M:%S")
        lst_logs.controls.insert(0, ft.Text(f"[{hora}] {mensagem}", color=cor, size=12))
        page.update()

    # --- FUNÇÃO PRINCIPAL DE DIAGNÓSTICO ---
    # Rota Lógica: Integra com a classe DiagnosticoSistema para testar a infraestrutura
    async def executar_diagnostico(e=None):
        adicionar_log("Iniciando varredura de integridade...", "blue")
        
        # Teste de Banco de Dados
        res_db, msg_db = await DiagnosticoSistema.testar_banco_dados()
        icon_db.color = "green" if res_db else "red"
        lbl_db_status.value = "OPERACIONAL" if res_db else "FALHA"
        lbl_db_status.color = "green" if res_db else "red"
        lbl_db_detalhe.value = msg_db
        adicionar_log(f"DB: {msg_db}", "green" if res_db else "red")

        # Teste de Conectividade
        res_net, msg_net = await DiagnosticoSistema.testar_conexao_internet()
        icon_net.color = "green" if res_net else "red"
        lbl_net_status.value = "ONLINE" if res_net else "OFFLINE"
        lbl_net_status.color = "green" if res_net else "red"
        lbl_net_detalhe.value = msg_net
        adicionar_log(f"Rede: {msg_net}", "green" if res_net else "red")
        
        page.update()

    # --- FUNÇÃO DE SUPORTE (MELHORIA IMPLEMENTADA) ---
    # Rota Lógica: Conecta o status do sistema ao WhatsApp do suporte
    def reportar_erro_suporte(e):
        msg = (
            "🛠️ *SUPORTE TÉCNICO ÁGUAFLOW*\n"
            "O sistema apresenta instabilidade no Vivere Prudente.\n"
            f"Status DB: {lbl_db_status.value}\n"
            f"Status Rede: {lbl_net_status.value}\n"
            f"Data/Hora: {datetime.datetime.now().strftime('%d/%m %H:%M')}"
        )
        enviar_alerta_whatsapp(page, msg)
        adicionar_log("Chamado de suporte enviado via WhatsApp", "orange")

    # --- HELPER: CARDS DE STATUS ---
    def criar_card_status(titulo, icone, status, detalhe):
        return ft.Container(
            content=ft.Column([
                ft.Text(titulo, size=10, color="white54", weight="bold"),
                ft.Row([icone, ft.Column([status, detalhe], spacing=0)]),
            ], spacing=10),
            bgcolor="white10", padding=15, border_radius=10, expand=True
        )

    # Executa o diagnóstico assim que a tela abre
    asyncio.create_task(executar_diagnostico())

    return ft.View(
        route="/dashboard_saude",
        appbar=ft.AppBar(
            title=ft.Text("Saúde do Sistema"),
            leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=voltar),
            bgcolor="black26"
        ),
        controls=[
            ft.Column([
                ft.Text("MÓDULOS CRÍTICOS", size=16, weight="bold"),
                ft.Row([
                    criar_card_status("BANCO DE DADOS", icon_db, lbl_db_status, lbl_db_detalhe),
                    criar_card_status("CONEXÃO REDE", icon_net, lbl_net_status, lbl_net_detalhe),
                ], spacing=15),

                ft.Divider(height=20, color="white10"),
                ft.Text("LOGS DE EVENTOS", size=16, weight="bold"),
                ft.Container(content=lst_logs, bgcolor="black26", border_radius=10, height=250),

                # --- BOTÕES DE AÇÃO ---
                ft.ElevatedButton(
                    "REESCANEAR SISTEMA",
                    icon=ft.Icons.REFRESH_ROUNDED,
                    on_click=executar_diagnostico,
                    width=400, height=50,
                    style=ft.ButtonStyle(bgcolor="blue", color="white")
                ),
                ft.TextButton(
                    "Relatar erro ao suporte técnico (WhatsApp)",
                    icon=ft.Icons.SUPPORT_AGENT,
                    on_click=reportar_erro_suporte
                )
            ], spacing=15, padding=20)
        ]
    )