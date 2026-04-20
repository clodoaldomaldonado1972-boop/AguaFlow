import flet as ft
import asyncio
import os
from database.database import Database
from utils.relatorio_engine import RelatorioEngine
from views import styles as st
# INTEGRAÇÃO DEFINITIVA: Importa o serviço que lida com múltiplos anexos (Água e Gás)
from utils.email_service import enviar_relatorios_por_email

def montar_tela_relatorio(page: ft.Page, voltar):
    """
    Tela de fechamento e relatórios. 
    Exibe o progresso das 96 unidades e permite exportar e enviar os dados.
    """
    
    # 1. BUSCA DE DADOS E CÁLCULO DE PROGRESSO
    try:
        # Busca todas as leituras realizadas no ciclo atual no SQLite
        leituras_atuais = Database.buscar_relatorio_geral() 
    except:
        leituras_atuais = []

    total_unidades = 96
    lidas = len(leituras_atuais)
    # Progresso para a ProgressBar (0.0 a 1.0)
    progresso_valor = lidas / total_unidades if total_unidades > 0 else 0

    # --- FUNÇÕES DE AÇÃO ---

    async def clicar_gerar_pdf(e):
        """Gera os documentos PDF localmente na pasta storage."""
        e.control.disabled = True
        page.snack_bar = ft.SnackBar(ft.Text("A gerar relatórios PDF..."), bgcolor=ft.colors.BLUE_700)
        page.snack_bar.open = True
        page.update()
        
        try:
            # O RelatorioEngine agora retorna uma LISTA (ex: [pdf_agua, pdf_gas])
            caminhos = await asyncio.to_thread(RelatorioEngine.gerar_pdf_relatorio_mensal, leituras_atuais)
            
            nomes_arquivos = ", ".join([os.path.basename(p) for p in caminhos])
            page.snack_bar = ft.SnackBar(
                ft.Text(f"PDF(s) gerado(s): {nomes_arquivos}"), 
                bgcolor=ft.colors.GREEN_700
            )
        except Exception as err:
            page.snack_bar = ft.SnackBar(ft.Text(f"Erro ao gerar: {err}"), bgcolor=ft.colors.RED_700)
        
        e.control.disabled = False
        page.snack_bar.open = True
        page.update()

    async def acao_finalizar_mes(e):
        """
        Gera os ficheiros de Água e Gás e envia-os via e-mail unificado.
        """
        e.control.disabled = True
        page.snack_bar = ft.SnackBar(ft.Text("A iniciar envio dos relatórios..."), bgcolor=ft.colors.BLUE_800)
        page.snack_bar.open = True
        page.update()
        
        try:
            # 1. Gera os PDFs (Gás só será gerado se houver dados)
            arquivos = await asyncio.to_thread(RelatorioEngine.gerar_pdf_relatorio_mensal, leituras_atuais)
            
            if not arquivos:
                raise Exception("Nenhum dado encontrado para exportação.")

            # 2. Envio unificado (o serviço já limpa a pasta 'relatorios' após o envio)
            sucesso = await asyncio.to_thread(enviar_relatorios_por_email, arquivos)
            
            if sucesso:
                page.snack_bar = ft.SnackBar(
                    ft.Text("✅ Sucesso! Relatórios enviados e memória limpa."), 
                    bgcolor=ft.colors.GREEN_800
                )
            else:
                page.snack_bar = ft.SnackBar(
                    ft.Text("❌ Falha no envio. Verifique a internet ou o .env"), 
                    bgcolor=ft.colors.RED_800
                )
        except Exception as err:
            page.snack_bar = ft.SnackBar(ft.Text(f"Erro Crítico: {err}"), bgcolor=ft.colors.RED_900)
        
        e.control.disabled = False
        page.snack_bar.open = True
        page.update()

    # --- INTERFACE (IHC) ---
    return ft.View(
        route="/relatorios",
        bgcolor=st.BG_DARK,
        controls=[
            ft.AppBar(
                title=ft.Text("Fechamento Mensal", weight="bold"),
                center_title=True,
                bgcolor=ft.colors.SURFACE_VARIANT,
                leading=ft.IconButton(ft.icons.ARROW_BACK, on_click=voltar)
            ),
            ft.Column([
                ft.Container(height=10),
                
                # Card de Progresso (Feedback visual para o Zelador)
                ft.Container(
                    bgcolor="#232629", padding=25, border_radius=20,
                    border=ft.border.all(1, "white10"),
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.icons.ANALYTICS, color=ft.colors.BLUE_400),
                            ft.Text(f"Progresso: {lidas} de {total_unidades}", size=18, weight="bold"),
                        ], alignment=ft.MainAxisAlignment.CENTER),
                        
                        ft.ProgressBar(value=progresso_valor, color=ft.colors.BLUE_ACCENT, height=12),
                        
                        ft.Text(f"{int(progresso_valor * 100)}% concluído", size=12, color="grey"),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15)
                ),
                
                ft.Divider(height=30, color="transparent"),
                
                # Botões de Ação Principal
                ft.Column([
                    ft.ElevatedButton(
                        "GERAR RELATÓRIOS (LOCAL)", 
                        icon=ft.icons.PICTURE_AS_PDF, 
                        on_click=clicar_gerar_pdf,
                        style=st.BTN_MAIN,
                        width=350, height=55
                    ),
                    
                    ft.ElevatedButton(
                        "FINALIZAR E ENVIAR AO ADM", 
                        icon=ft.icons.SEND_AND_ARCHIVE, 
                        on_click=acao_finalizar_mes,
                        width=350, height=55,
                        style=ft.ButtonStyle(
                            bgcolor=ft.colors.BLUE_700, 
                            color=ft.colors.WHITE,
                            shape=ft.RoundedRectangleBorder(radius=10)
                        )
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15),
                
                ft.Container(height=20),
                
                ft.Text(
                    "O fechamento enviará arquivos separados para Água e Gás.\nA pasta temporária será limpa após o envio.",
                    size=11, color="grey", text_align=ft.TextAlign.CENTER
                ),
                
                ft.TextButton(
                    "Voltar ao Menu", 
                    icon=ft.icons.ARROW_BACK,
                    on_click=voltar,
                    style=ft.ButtonStyle(color="grey")
                )
            ], 
            horizontal_alignment=ft.CrossAxisAlignment.CENTER, 
            scroll=ft.ScrollMode.ADAPTIVE,
            spacing=10
            )
        ]
    )