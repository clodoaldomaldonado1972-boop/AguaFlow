import flet as ft
import asyncio
import datetime

# --- IMPORT CORRIGIDO PARA A NOVA PASTA UTILS NA RAIZ ---
from utils.diagnostico import DiagnosticoSistema


def montar_tela_saude(page: ft.Page, voltar):

    # --- COMPONENTES DE STATUS (REATIVOS) ---
    icon_db = ft.Icon(ft.Icons.STORAGE_ROUNDED, color="grey", size=30)
    lbl_db_status = ft.Text(
        "Aguardando...", color="grey", size=16, weight="bold")
    lbl_db_detalhe = ft.Text("Verificando banco local",
                             size=12, color="white54")

    icon_net = ft.Icon(ft.Icons.WIFI_ROUNDED, color="grey", size=30)
    lbl_net_status = ft.Text(
        "Aguardando...", color="grey", size=16, weight="bold")
    lbl_net_detalhe = ft.Text("Verificando conexão", size=12, color="white54")

    lst_logs = ft.ListView(expand=1, spacing=5, padding=10)

    def adicionar_log(mensagem, cor="white54"):
        hora = datetime.datetime.now().strftime("%H:%M:%S")
        lst_logs.controls.insert(0, ft.Text(
            f"[{hora}] {mensagem}", color=cor, size=12))
        page.update()

    async def executar_diagnostico(e=None):
        adicionar_log("Iniciando check-up do sistema...", "blue")

        # Reset visual para "Processando"
        icon_db.color = icon_net.color = "orange"
        lbl_db_status.value = lbl_net_status.value = "Testando..."
        page.update()

        # Teste 1: Banco de Dados (Chamando da utils)
        # O método testar_banco verifica se o SQLite responde[cite: 4]
        db_ok, db_msg = await DiagnosticoSistema.testar_banco()
        icon_db.color = "green" if db_ok else "red"
        lbl_db_status.value = "ONLINE" if db_ok else "ERRO"
        lbl_db_status.color = "green" if db_ok else "red"
        lbl_db_detalhe.value = db_msg
        adicionar_log(db_msg, "green" if db_ok else "red")

        # Teste 2: Internet (Verifica ping 8.8.8.8)[cite: 4]
        net_ok, net_msg = await DiagnosticoSistema.testar_internet()
        icon_net.color = "green" if net_ok else "red"
        lbl_net_status.value = "CONECTADO" if net_ok else "OFFLINE"
        lbl_net_status.color = "green" if net_ok else "red"
        lbl_net_detalhe.value = net_msg
        adicionar_log(net_msg, "green" if net_ok else "red")

        page.update()

    # --- UI LAYOUT ---

    def criar_card_status(titulo, icon_obj, status_obj, detalhe_obj):
        return ft.Container(
            content=ft.Column([
                ft.Text(titulo, size=14, weight="w500", color="blue400"),
                ft.Row([icon_obj, status_obj], alignment="start", spacing=10),
                detalhe_obj
            ], spacing=5),
            bgcolor="#1E2124",
            padding=15,
            border_radius=12,
            expand=True,
            border=ft.border.all(1, "white10")
        )

    # Dispara o teste ao carregar a tela usando a nova tarefa assíncrona
    page.run_task(executar_diagnostico)

    return ft.View(
        route="/dashboard_saude",
        bgcolor="#121417",
        appbar=ft.AppBar(
            title=ft.Text("Saúde do Sistema"),
            bgcolor="#1e1e1e",
            leading=ft.IconButton(
                ft.Icons.ARROW_BACK, on_click=voltar)  # Corrigido para ícone padrão
        ),
        controls=[
            ft.Column([
                ft.Text("Monitor de Infraestrutura", size=24,
                        weight="bold", color="white"),
                ft.Text("Status dos serviços essenciais do AguaFlow",
                        color="grey"),

                ft.Divider(height=10, color="transparent"),

                ft.Row([
                    criar_card_status("BANCO DE DADOS", icon_db,
                                      lbl_db_status, lbl_db_detalhe),
                    criar_card_status("CONEXÃO REDE", icon_net,
                                      lbl_net_status, lbl_net_detalhe),
                ], spacing=15),

                ft.Divider(height=20, color="white10"),

                ft.Text("LOGS DE EVENTOS (Tempo Real)",
                        size=16, weight="bold", color="white"),
                ft.Container(
                    content=lst_logs,
                    bgcolor="black26",
                    border_radius=10,
                    height=250,  # Ajustado para caber melhor na tela mobile
                    border=ft.border.all(1, "white10")
                ),

                ft.ElevatedButton(
                    "REESCANEAR SISTEMA",
                    icon=ft.Icons.REFRESH_ROUNDED,
                    on_click=executar_diagnostico,
                    width=400,
                    height=50,
                    style=ft.ButtonStyle(bgcolor="blue", color="white")
                )
            ], spacing=15, padding=20)
        ]
    )
