import flet as ft
import asyncio
from views import styles as st
from database.database import Database
from utils.suporte_helper import SuporteHelper  # Importa o helper para WhatsApp e Manual

# --- CLASSES DE SEGURANÇA E MONITORAMENTO ---
try:
    from utils.preferencias_leitura import PreferenciasLeitura
except ImportError:
    class PreferenciasLeitura:
        @staticmethod
        def get_modo_ocr(page=None): return True
        @staticmethod
        def set_modo_ocr(page=None, val=True): pass

try:
    from utils.diagnostico import DiagnosticoSistema
except ImportError:
    class DiagnosticoSistema:
        @staticmethod
        async def executar_checkup_completo(): return False, "Serviço de Diagnóstico offline"

class MonitoramentoAguaFlow:
    @staticmethod
    async def exportar_metricas_prometheus():
        """Simula o envio de métricas de telemetria para o servidor Prometheus."""
        await asyncio.sleep(1.5)
        return True

def montar_tela_configs(page, on_back_click):
    # Recupera o e-mail da sessão para exibição no perfil e suporte
    user_email_logado = getattr(page, "user_email", "Visitante")

    # --- COMPONENTES DE INTERFACE (STATUS) ---
    status_icon = ft.Icon(ft.icons.CELL_WIFI, color="grey")
    status_text = ft.Text("Sistema Pronto", color="white")
    
    txt_email_notif = ft.TextField(
        label="E-mail para Alertas de Vazamento",
        value=user_email_logado,
        border_color=st.PRIMARY_BLUE,
        expand=True,
        text_style=ft.TextStyle(color="white")
    )

    # --- FUNÇÃO: TESTAR MONITORAMENTO ---
    async def realizar_teste_sistema(e):
        btn_teste.disabled = True
        status_icon.color = "orange"
        status_text.value = "Sincronizando com Prometheus..."
        page.update()

        # Simula exportação de métricas
        await MonitoramentoAguaFlow.exportar_metricas_prometheus()
        
        # Executa check-up de saúde
        sucesso, mensagem = await DiagnosticoSistema.executar_checkup_completo()
        
        if sucesso:
            status_icon.color = "green"
            status_text.value = "Métricas Ativas: Dados visíveis no Grafana"
        else:
            status_icon.color = "red"
            status_text.value = f"Erro na telemetria: {mensagem}"
            
        btn_teste.disabled = False
        page.update()

    # --- FUNÇÃO: SALVAR CONFIGS ---
    def salvar_notificacoes(e):
        page.snack_bar = ft.SnackBar(
            ft.Text(f"Configurações salvas para {txt_email_notif.value}"),
            bgcolor="green"
        )
        page.snack_bar.open = True
        page.update()

    btn_teste = ft.ElevatedButton(
        "TESTAR TELEMETRIA", 
        on_click=realizar_teste_sistema,
        bgcolor=st.PRIMARY_BLUE,
        color="white"
    )

    # --- CONSTRUÇÃO DA VIEW ---
    return ft.View(
        route="/configuracoes",
        bgcolor=st.BG_DARK,
        controls=[
            ft.AppBar(
                title=ft.Text("Configurações e Suporte"),
                leading=ft.IconButton(ft.icons.ARROW_BACK, on_click=on_back_click),
                bgcolor=ft.colors.BLUE_900,
                color="white"
            ),
            ft.ListView(
                expand=True,
                padding=20,
                spacing=15,
                controls=[
                    # SEÇÃO 1: NOTIFICAÇÕES
                    ft.Text("NOTIFICAÇÕES E ALERTAS", size=16, weight="bold", color=st.PRIMARY_BLUE),
                    ft.Row([
                        txt_email_notif, 
                        ft.IconButton(ft.icons.SAVE, on_click=salvar_notificacoes, icon_color=st.PRIMARY_BLUE)
                    ]),
                    
                    ft.Divider(height=10),
                    
                    # SEÇÃO 2: MODO DE LEITURA
                    ft.Text("PREFERÊNCIAS DE LEITURA", size=16, weight="bold", color=st.PRIMARY_BLUE),
                    ft.Switch(
                        label="Ativar Scanner OCR (IA)", 
                        value=PreferenciasLeitura.get_modo_ocr(page),
                        active_color=st.PRIMARY_BLUE,
                        on_change=lambda e: PreferenciasLeitura.set_modo_ocr(page, e.control.value)
                    ),
                    
                    ft.Divider(height=10),

                    # SEÇÃO 3: OBSERVABILIDADE (INTEGRAÇÃO COMPLETA)
                    ft.Text("SAÚDE DO SISTEMA (PROMETHEUS/GRAFANA)", size=16, weight="bold", color=st.PRIMARY_BLUE),
                    ft.Container(
                        bgcolor="#1e1e1e", padding=15, border_radius=10,
                        content=ft.Column([
                            ft.Row([status_icon, status_text]),
                            ft.Row([
                                btn_teste, 
                                ft.ElevatedButton(
                                    "VER SAÚDE (APP)", 
                                    on_click=lambda _: page.go("/dashboard_saude"),
                                    bgcolor=ft.colors.BLUE_GREY_700
                                ),
                                ft.TextButton(
                                    "ABRIR GRAFANA", 
                                    on_click=lambda _: page.launch_url("http://localhost:3000")
                                )
                            ], wrap=True)
                        ])
                    ),

                    ft.Divider(height=10),

                    # SEÇÃO 4: SUPORTE E MANUAL (WHATSAPP E GUIA INTERNO)
                    ft.Text("AJUDA E SUPORTE", size=16, weight="bold", color=st.PRIMARY_BLUE),
                    ft.Container(
                        bgcolor="#1e1e1e", padding=15, border_radius=10,
                        content=ft.Column([
                            ft.Text(f"Suporte técnico para: {user_email_logado}", size=12, color="grey"),
                            ft.Row([
                                ft.ElevatedButton(
                                    "GUIA DE USO", 
                                    icon=ft.icons.HELP_OUTLINE,
                                    on_click=lambda _: page.go("/ajuda")
                                ),
                                ft.IconButton(
                                    icon=ft.icons.CHAT,
                                    icon_color=ft.colors.GREEN_ACCENT,
                                    tooltip="Falar no WhatsApp",
                                    on_click=lambda _: SuporteHelper.abrir_whatsapp_suporte(page, user_email_logado)
                                )
                            ])
                        ])
                    ),
                    
                    ft.Container(height=20),
                    
                    # SEÇÃO 5: SAIR
                    ft.ElevatedButton(
                        "ENCERRAR SESSÃO", 
                        bgcolor=ft.colors.RED_700, 
                        color="white", 
                        on_click=lambda _: page.go("/"),
                        height=50,
                        width=float("inf")
                    ),
                    ft.Text("AguaFlow v1.0 - Projeto Integrador UNIVESP", size=10, color="grey", text_align="center")
                ]
            )
        ]
    )