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
        # No Flet assíncrono, o update pode ser disparado normalmente se o loop estiver ativo
        page.update()

    async def executar_diagnostico(e=None):
        adicionar_log("Iniciando varredura de integridade...", "blue")
        
        # Reseta os ícones para estado de carregamento
        icon_db.color = "orange"
        lbl_db_status.value = "Analisando..."
        lbl_db_status.color = "orange"
        page.update()

        # Chama a função unificada do seu arquivo utils/diagnostico.py
        res_geral, msg_geral = await DiagnosticoSistema.executar_checkup_completo()
        
        if res_geral:
            icon_db.color = "green"
            icon_db.name = ft.icons.CHECK_CIRCLE_ROUNDED
            lbl_db_status.value = "SISTEMA SAUDÁVEL"
            lbl_db_status.color = "green"
            lbl_db_detalhe.value = msg_geral
            adicionar_log("Check-up concluído: Nenhuma irregularidade encontrada.", "green")
        else:
            icon_db.color = "red"
            icon_db.name = ft.icons.ERROR_OUTLINED
            lbl_db_status.value = "ALERTA DE FALHA"
            lbl_db_status.color = "red"
            lbl_db_detalhe.value = msg_geral
            adicionar_log(f"Falha detectada: {msg_geral}", "red")
            
            # Envia alerta via engine se houver falha crítica
            try:
                enviar_alerta_MESSAGE("Falha detectada no Diagnóstico do ÁguaFlow")
            except:
                adicionar_log("Não foi possível enviar alerta externo.", "orange")
        
        page.update()

    def criar_card_status(titulo, icone, texto_status, texto_detalhe):
        return ft.Container(
            content=ft.Column([
                ft.Row([icone, ft.Text(titulo, size=12, weight="bold", color="white54")], spacing=10),
                ft.Divider(height=10, color="transparent"),
                texto_status,
                texto_detalhe
            ]),
            padding=15,
            bgcolor="black26",
            border_radius=15,
            expand=True,
            border=ft.border.all(1, "white10")
        )

    # --- ESTRUTURA DA VIEW ---
    return ft.View(
        route="/dashboard_saude",
        appbar=ft.AppBar(
            title=ft.Text("Saúde do Sistema"),
            leading=ft.IconButton(ft.icons.ARROW_BACK, on_click=voltar),
            bgcolor="black26",
            center_title=True
        ),
        controls=[
            ft.Container(
                padding=20,
                content=ft.Column([
                    ft.Text("MÓDULOS CRÍTICOS", size=14, weight="bold", color="blue"),
                    ft.Row([
                        criar_card_status("SISTEMA E BANCO", icon_db, lbl_db_status, lbl_db_detalhe),
                    ], spacing=15),

                    ft.Divider(height=20, color="white10"),
                    ft.Text("LOGS DE EVENTOS", size=14, weight="bold", color="blue"),
                    ft.Container(
                        content=lst_logs, 
                        bgcolor="black26", 
                        border_radius=10, 
                        height=250,
                        border=ft.border.all(1, "white10")
                    ),

                    ft.ElevatedButton(
                        "REESCANEAR SISTEMA",
                        icon=ft.icons.REFRESH_ROUNDED,
                        on_click=executar_diagnostico,
                        width=400, height=50,
                        style=ft.ButtonStyle(bgcolor="blue", color="white")
                    ),
                    
                    # Novo botão para facilitar o acesso ao Grafana que você mencionou
                    ft.ElevatedButton(
                        "ABRIR MÉTRICAS (GRAFANA)",
                        icon=ft.icons.INSERT_CHART_OUTLINED_ROUNDED,
                        on_click=lambda _: page.launch_url("https://grafana.com/orgs/clodoaldomaldonado1972boop"),
                        width=400, height=50,
                        style=ft.ButtonStyle(bgcolor="orange", color="white")
                    ),

                    ft.TextButton(
                        "Relatar erro ao suporte técnico",
                        icon=ft.icons.SUPPORT_AGENT,
                        on_click=lambda _: page.launch_url("clodoaldomaldonado112@gmail.com"), # Ajuste para seu contato
                        style=ft.ButtonStyle(color="white54")
                    ),
                ], spacing=15, scroll=ft.ScrollMode.ADAPTIVE)
            )
        ]
    )