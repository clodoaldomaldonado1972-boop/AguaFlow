import flet as ft
import asyncio
import os
from database.database import Database
from utils.relatorio_engine import RelatorioEngine
from views import styles as st
# Serviço que lida com os anexos
from utils.email_service import enviar_relatorios_por_email

def montar_tela_relatorio(page: ft.Page, voltar):
    """
    Tela de fechamento e relatórios. 
    Exibe o progresso das unidades e permite exportar e enviar os dados por e-mail.
    """
    
    # 1. BUSCA DE DADOS E CÁLCULO DE PROGRESSO INVERSO
    # O total de unidades vem da lista oficial (incluindo Lazer e Geral)
    db_lista_oficial = Database._gerar_lista_unidades()
    total_unidades = len(db_lista_oficial)
    
    # Busca o que já foi lido no banco
    leituras_atuais = Database.get_leituras_mes_atual()
    lidas = len(leituras_atuais)
    faltam = total_unidades - lidas
    
    # Barra que esvazia: 1.0 (cheia/falta tudo) até 0.0 (vazia/concluído)
    progresso_valor = faltam / total_unidades if total_unidades > 0 else 0

    # --- FUNÇÕES DE AÇÃO ---

    async def clicar_gerar_pdf(e):
        """Gera os documentos PDF e CSV localmente."""
        print(f"\n[AGUAFLOW] 📄 Iniciando geração de PDF para {lidas} unidades...")
        e.control.disabled = True
        page.update()

        try:
            # Gera PDF com as leituras do mês
            pdf_path = RelatorioEngine.gerar_relatorio_consumo(leituras_atuais)
            print(f"[AGUAFLOW] ✅ PDF gerado: {pdf_path}")

            # Gera CSV para Excel
            csv_path = RelatorioEngine.gerar_csv_consumo(leituras_atuais)
            print(f"[AGUAFLOW] ✅ CSV gerado: {csv_path}")

            page.snack_bar = ft.SnackBar(ft.Text("PDF e CSV gerados com sucesso!"), bgcolor="green")
        except Exception as err:
            print(f"[AGUAFLOW] ❌ Erro ao gerar relatórios: {err}")
            page.snack_bar = ft.SnackBar(ft.Text(f"Erro: {err}"), bgcolor="red")

        page.snack_bar.open = True
        e.control.disabled = False
        page.update()

    async def acao_finalizar_mes(e):
        """Finaliza o ciclo e envia por e-mail com logs no terminal."""
        print("\n[AGUAFLOW] 📧 Iniciando processo de envio de e-mail...")
        e.control.disabled = True
        page.update()

        page.snack_bar = ft.SnackBar(
            content=ft.Row([
                ft.Icon(ft.icons.SAVE, color="white"),
                ft.Text("Preparando envio de relatório...")
            ]),
            bgcolor=st.PRIMARY_BLUE
        )
        page.snack_bar.open = True
        page.update()

        try:
            # Gera os arquivos primeiro
            dados_envio = Database.get_dados_para_relatorio()

            if not dados_envio:
                print("[AGUAFLOW] ⚠️ Falha: Nenhum dado encontrado para enviar.")
                page.snack_bar = ft.SnackBar(ft.Text("Erro: Sem dados para envio."), bgcolor="red")
            else:
                print(f"[AGUAFLOW] 📤 Gerando arquivos para {len(dados_envio)} registros...")

                # Gera PDF e CSV
                pdf_path = RelatorioEngine.gerar_relatorio_consumo(dados_envio)
                csv_path = RelatorioEngine.gerar_csv_consumo(dados_envio)

                # Envia por e-mail
                print(f"[AGUAFLOW] 📤 Enviando para {os.getenv('EMAIL_DESTINO', 'ADM')}...")
                sucesso, msg = RelatorioEngine.enviar_relatorios_por_email(pdf_path, csv_path)

                if sucesso:
                    print("[AGUAFLOW] ✅ Relatório enviado com sucesso!")
                    page.snack_bar = ft.SnackBar(ft.Text(f"📩 {msg}"), bgcolor="green")
                else:
                    print(f"[AGUAFLOW] ❌ Erro no envio: {msg}")
                    page.snack_bar = ft.SnackBar(ft.Text(f"Falha no envio: {msg}"), bgcolor="red")

        except Exception as err:
            print(f"[AGUAFLOW] ❌ Erro no envio: {err}")
            page.snack_bar = ft.SnackBar(ft.Text(f"Falha no envio: {err}"), bgcolor="red")

        page.snack_bar.open = True
        e.control.disabled = False
        page.update()

    # --- INTERFACE ---
    return ft.View(
        route="/relatorios",
        bgcolor=st.BG_DARK,
        controls=[
            ft.AppBar(
                title=ft.Text("Fechamento Mensal - Vivere"),
                center_title=True,
                bgcolor=st.PRIMARY_BLUE,
                leading=ft.IconButton(ft.icons.ARROW_BACK, on_click=voltar)
            ),
            ft.Column([
                ft.Container(height=20),
                
                # CARD DE PROGRESSO (Barra que diminui)
                ft.Container(
                    content=ft.Column([
                        ft.Text("UNIDADES PENDENTES", weight="bold", size=16),
                        ft.ProgressBar(value=progresso_valor, width=350, color=st.ACCENT_ORANGE),
                        ft.Row([
                            ft.Text(f"Faltam: {faltam}", color="white"),
                            ft.Text(f"Total: {total_unidades}", color="grey"),
                        ], alignment="spaceBetween"),
                    ]),
                    padding=20, bgcolor="#1E2126", border_radius=15
                ),
                
                ft.Container(height=20),
                
                # BOTÕES DE AÇÃO
                ft.ElevatedButton(
                    "GERAR RELATÓRIOS PDF",
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

                ft.Container(height=20),
                ft.Text(
                    "O fechamento envia arquivos de Água e Gás.\nVerifique o terminal para acompanhar o envio.",
                    size=11, color="grey", text_align="center"
                ),
                
                ft.TextButton("Voltar ao Menu", icon=ft.icons.ARROW_BACK, on_click=voltar)

            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, scroll=ft.ScrollMode.ADAPTIVE)
        ]
    )