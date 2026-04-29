import flet as ft
from database.database import Database
from utils.report_generator import ReportGenerator
from utils.email_service import enviar_relatorios_por_email # Importação adicionada

async def montar_tela_historico(page: ft.Page):
    
    # 1. CÁLCULO DE CONCLUSÃO
    lista_total = Database._gerar_lista_unidades()
    leituras_mes = Database.get_leituras_mes_atual()
    
    total_esperado = len(lista_total)
    total_realizado = len(leituras_mes)
    
    # O botão só será visível se todas as unidades tiverem sido lidas
    ciclo_concluido = total_realizado >= total_esperado

    async def processar_envio_final(e):
        e.control.disabled = True
        e.control.text = "A enviar..." # Feedback visual
        page.update()
        
        dados = Database.get_leituras_mes_atual()
        
        if dados:
            # Gera os ficheiros temporários
            path_pdf = ReportGenerator.gerar_pdf(dados, "Relatório Geral - Edifício Vivere Prudente")
            path_csv = ReportGenerator.gerar_csv(dados, "leituras_vivere.csv")
            
            # 2. DISPARO DO E-MAIL (Usando o seu email_service.py)
            # A função já limpa a pasta 'relatorios' após o envio
            sucesso = enviar_relatorios_por_email([path_pdf, path_csv])
            
            if sucesso:
                page.snack_bar = ft.SnackBar(ft.Text("✅ Relatórios enviados com sucesso!"))
            else:
                page.snack_bar = ft.SnackBar(ft.Text("❌ Erro ao enviar e-mail. Verifique o .env"))
            
            page.snack_bar.open = True
        
        e.control.disabled = False
        e.control.text = "Enviar CSV e PDF por E-mail"
        page.update()

    # --- UI DINÂMICA ---
    btn_finalizar = ft.Card(
        content=ft.Container(
            padding=20,
            content=ft.Column([
                ft.Text("Finalizar Ciclo de Leitura", size=18, weight="bold"),
                ft.Text(f"Status: {total_realizado}/{total_esperado} unidades lidas", color="grey"),
                ft.Row([
                    ft.ElevatedButton(
                        "Enviar CSV e PDF por E-mail",
                        icon=ft.icons.SEND,
                        on_click=processar_envio_final,
                        visible=ciclo_concluido, # SÓ APARECE SE CONCLUÍDO
                        style=ft.ButtonStyle(color=ft.colors.WHITE, bgcolor=ft.colors.GREEN_800)
                    ),
                ])
            ])
        ),
        visible=ciclo_concluido # O card inteiro pode ficar invisível até ao fim
    )

    return ft.View(
        route="/historico",
        controls=[
            ft.Text("Histórico de Medições", size=24),
            # Se não estiver concluído, mostra um aviso
            ft.Text("Leituras pendentes. O envio estará disponível após concluir todas as unidades.", 
                   visible=not ciclo_concluido, color="orange"),
            btn_finalizar 
        ]
    )