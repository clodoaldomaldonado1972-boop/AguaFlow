import flet as ft
import asyncio
from database.database import Database
from database.sync_engine import SyncEngine

# Importação organizada das telas
from views import auth, menu_principal, medicao, relatorios, configuracoes, dashboard
from views.utils import gerador_qr, gerador_pdf, mailer

async def main(page: ft.Page):
    # --- CONFIGURAÇÃO DE TEMA ---
    page.title = "AguaFlow - Vivere Prudente"
    page.theme_mode = ft.ThemeMode.DARK
    page.dark_theme = ft.Theme(color_scheme_seed="blue")
    page.padding = 0 
    
    Database.init_db()
    palco = ft.Container(expand=True)
    page.add(palco)

    # --- FUNÇÕES DE APOIO (LÓGICA) ---

    async def acao_sincronizar(e=None):
        """Função que os relatórios chamam para sincronizar"""
        page.snack_bar = ft.SnackBar(ft.Text("🔄 Sincronizando com a nuvem..."))
        page.snack_bar.open = True
        page.update()
        # Roda o motor de sincronização em uma thread separada para não travar a UI
        await asyncio.to_thread(SyncEngine.sincronizar_tudo)
        page.snack_bar = ft.SnackBar(ft.Text("✅ Sincronização concluída!"), bgcolor="green")
        page.update()

    async def acao_gerar_qr(e=None):
        """Função para gerar etiquetas de unidades"""
        try:
            gerador_qr.gerar_qr_codes("AMBOS") 
            page.snack_bar = ft.SnackBar(ft.Text("✅ Etiquetas geradas com sucesso!"), bgcolor="blue")
        except Exception as err:
            page.snack_bar = ft.SnackBar(ft.Text(f"❌ Erro ao gerar: {err}"), bgcolor="red")
        page.snack_bar.open = True
        page.update()

    async def acao_pdf_email(e=None):
        """Processa o relatório e exporta os dados"""
        page.snack_bar = ft.SnackBar(ft.Text("📊 Gerando relatório de medição..."))
        page.snack_bar.open = True
        page.update()
        
        # Exporta o CSV local primeiro
        if Database.exportar_csv():
            page.snack_bar = ft.SnackBar(ft.Text("✅ Relatórios salvos na pasta /relatorios"), bgcolor="green")
        else:
            page.snack_bar = ft.SnackBar(ft.Text("⚠️ Nenhuma leitura concluída para exportar."), bgcolor="orange")
        page.update()

    # --- FUNÇÕES DE NAVEGAÇÃO (INTERFACE) ---

    async def ir_para_home(perfil=None):
        if perfil: 
            page.session.set("perfil", perfil)
        palco.content = menu_principal.montar_menu(
            page, ir_para_medicao, ir_para_relatorios, ir_para_configs, ir_para_dashboard
        )
        page.update()

    async def ir_para_medicao(e=None):
        # A tela de medição agora recebe o on_next para pular para o próximo apto
        palco.content = await medicao.montar_tela(page, ir_para_home, on_next=ir_para_medicao)
        page.update()

    async def ir_para_relatorios(e=None):
        # CORREÇÃO DE IDENTAÇÃO: Todo o bloco abaixo agora está dentro da função
        palco.content = relatorios.montar_tela_relatorios(
            page, 
            voltar=ir_para_home, 
            sync_nuvem=acao_sincronizar,      # Agora definido acima
            gerar_e_enviar_pdf=acao_pdf_email, # Agora definido acima
            gerar_qr=acao_gerar_qr             # Agora definido acima
        )
        page.update()

    async def ir_para_dashboard(e=None):
        palco.content = dashboard.montar_tela_dashboard(page, voltar=ir_para_home)
        page.update()

    async def ir_para_configs(e=None):
        palco.content = configuracoes.montar_tela_configs(page, voltar=ir_para_home)
        page.update()

    # --- TAREFAS DE SEGUNDO PLANO ---
    async def background_sync():
        """Sincroniza automaticamente a cada 60 segundos"""
        while True:
            await asyncio.sleep(60)
            try: 
                await asyncio.to_thread(SyncEngine.sincronizar_tudo)
            except: 
                pass

    # --- INICIALIZAÇÃO DO APP ---
    # Começa pela tela de login
    palco.content = auth.criar_tela_login(
        page, 
        ao_logar_sucesso=lambda perfil: page.run_task(ir_para_home, perfil)
    )
    
    # Inicia o sync em background
    page.run_task(background_sync)
    page.update()

if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")