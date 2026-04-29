import flet as ft
import asyncio
from database.database import Database
from views import styles as st
from database.gestao_periodos import finalizar_mes_e_enviar
from utils.export_manager import ExportManager

def montar_tela_relatorio(page: ft.Page):
    # --- 1. ELEMENTOS DE FEEDBACK VISUAL ---
    # Texto que informa ao Marco Aurélio o que o sistema está fazendo
    lbl_status = ft.Text("Pronto para processar", color="grey700", size=14)
    # Barra de progresso para dar a sensação de movimento durante o processamento
    pr = ft.ProgressBar(width=300, visible=False, color=st.PRIMARY_BLUE)
    
    async def acao_gerar_qrs(tipo):
        lbl_status.value = f"⏳ Gerando etiquetas de {tipo} (50 por folha)..."
        lbl_status.color = "grey700"
        pr.visible = True
        page.update()
        try:
            await asyncio.sleep(0.1)
            unidades = Database._gerar_lista_unidades()
            caminho_pdf = ExportManager.gerar_etiquetas_qr_50_por_folha(unidades, tipo_medidor=tipo)
            lbl_status.value = f"✅ PDF de {tipo} gerado: {caminho_pdf}"
            lbl_status.color = "green"
        except Exception as ex:
            lbl_status.value = f"❌ Erro: {str(ex)}"
            lbl_status.color = "red"
        pr.visible = False
        page.update()

    async def acao_virada_ciclo(_):
        lbl_status.value = "⏳ Executando virada de ciclo e envio de relatórios..."
        lbl_status.color = "grey700"
        pr.visible = True
        page.update()
        try:
            ok = await asyncio.to_thread(finalizar_mes_e_enviar)
            if ok:
                lbl_status.value = "✅ Ciclo finalizado com sucesso e banco preparado para o próximo mês."
                lbl_status.color = "green"
            else:
                lbl_status.value = "⚠️ Não foi possível finalizar o ciclo. Verifique backup, dados e e-mail."
                lbl_status.color = st.ACCENT_ORANGE
        except Exception as ex:
            lbl_status.value = f"❌ Erro na virada de ciclo: {ex}"
            lbl_status.color = "red"
        pr.visible = False
        page.update()

    return ft.View(
        route="/relatorios",
        bgcolor=st.BG_DARK,
        controls=[
            ft.AppBar(
                title=ft.Text("Relatórios e Etiquetas"),
                bgcolor=st.PRIMARY_BLUE,
                leading=ft.IconButton(ft.icons.ARROW_BACK, on_click=lambda _: page.go("/menu"))
            ),
            ft.Column([
                ft.Container(height=20),
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.icons.RECYCLING, size=50, color=st.PRIMARY_BLUE),
                        ft.Text("FINALIZAR MÊS ATUAL", size=18, weight="bold"),
                        pr, lbl_status,
                        ft.ElevatedButton(
                            "EXECUTAR VIRADA DE CICLO",
                            icon=ft.icons.PLAY_CIRCLE_FILL,
                            on_click=acao_virada_ciclo,
                            style=st.BTN_MAIN, width=320, height=55
                        ),
                    ], horizontal_alignment="center"),
                    padding=20, bgcolor="#1E2126", border_radius=15
                ),
                ft.Divider(height=40, color="white10"),
                ft.Text("IMPRESSÃO DE ETIQUETAS (50/FOLHA)", size=14, weight="bold", color="grey"),
                ft.Row([
                    ft.ElevatedButton(
                        "QR ÁGUA", icon=ft.icons.WATER_DROP,
                        on_click=lambda _: page.run_task(acao_gerar_qrs, "Água"),
                        expand=True
                    ),
                    ft.ElevatedButton(
                        "QR GÁS", icon=ft.icons.LOCAL_FIRE_DEPARTMENT,
                        on_click=lambda _: page.run_task(acao_gerar_qrs, "Gás"),
                        expand=True, bgcolor=ft.colors.ORANGE_900, color=ft.colors.WHITE 
                    ),
                ], spacing=10),
                ft.Container(height=20),
                ft.TextButton("Voltar ao Menu Principal", on_click=lambda _: page.go("/menu")),
            ], scroll=ft.ScrollMode.AUTO, spacing=20, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        ]
    )