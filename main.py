import flet as ft
import asyncio
from database.database import Database
from database.sync_engine import SyncEngine
from views import dashboard
# Importação organizada das telas
from views import auth, menu_principal, medicao, relatorios, configuracoes
from views.utils import gerador_qr, gerador_pdf, mailer
import views.relatorios as relatorios

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

    async def ir_para_sync(e=None):
        page.snack_bar = ft.SnackBar(ft.Text("🔄 Sincronizando..."))
        page.snack_bar.open = True
        page.update()
        await asyncio.to_thread(SyncEngine.sincronizar_tudo)
        page.snack_bar = ft.SnackBar(ft.Text("✅ Sincronizado!"), bgcolor="green")
        page.update()

    async def ir_para_qr(e=None):
        gerador_qr.gerar_qr_codes("AMBOS") 
        page.snack_bar = ft.SnackBar(ft.Text("✅ Etiquetas geradas!"), bgcolor="blue")
        page.snack_bar.open = True
        page.update()

    async def acao_gerar_e_enviar_pdf(e=None):
        """Esta é a função que processa o PDF e e-mail"""
        page.snack_bar = ft.SnackBar(ft.Text("📊 Processando relatório..."))
        page.snack_bar.open = True
        page.update()
        # Aqui iria sua lógica de buscar dados e enviar e-mail
        # Ex: mailer.enviar_email_com_pdf(...)
        page.update()

    # --- FUNÇÕES DE NAVEGAÇÃO (INTERFACE) ---

    async def ir_para_home(perfil=None):
        if perfil: 
            page.session.set("perfil", perfil)
        palco.content = menu_principal.montar_menu(
            page, ir_para_medicao, ir_para_relatorios, ir_para_configs
        )
        page.update()

    async def ir_para_medicao(e=None):
        palco.content = await medicao.montar_tela(page, ir_para_home, on_next=ir_para_medicao)
        page.update()

    async def ir_para_relatorios(e=None):
    # Aqui passamos as funções que a tela de relatórios precisa
    palco.content = relatorios.montar_tela_relatorios(
        page, 
        voltar=ir_para_home, 
        sync_nuvem=acao_sincronizar, 
        gerar_e_enviar_pdf=acao_pdf_email, 
        gerar_qr=acao_gerar_qr
    )
    page.update()

    async def ir_para_configs(e=None):
        palco.content = configuracoes.montar_tela_configs(page, voltar=ir_para_home)
        page.update()

    # --- INICIALIZAÇÃO ---
    palco.content = auth.criar_tela_login(
        page, 
        ao_logar_sucesso=lambda perfil: page.run_task(ir_para_home, perfil)
    )
    page.update()

    async def ir_para_dashboard(e=None):
        palco.content = dashboard.montar_tela_dashboard(page, voltar=ir_para_home)
        page.update()

    async def background_sync():
        while True:
            await asyncio.sleep(60)
            try: await asyncio.to_thread(SyncEngine.sincronizar_tudo)
            except: pass

    page.run_task(background_sync)

if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")