import flet as ft
import asyncio
from database.database import Database
from database.sync_engine import SyncEngine

# Importação organizada das telas
from views import auth, menu_principal, medicao, relatorios, configuracoes

# Importação dos utilitários (Agora todos dentro da pasta views/utils)
from views.utils import gerador_qr, gerador_pdf, mailer

async def main(page: ft.Page):
    # --- CONFIGURAÇÃO DE TEMA (FUNDO ESCURO) ---
    page.title = "AguaFlow - Vivere Prudente"
    page.theme_mode = ft.ThemeMode.DARK # Mudado para DARK
    page.dark_theme = ft.Theme(color_scheme_seed="blue") # Semente azul como na imagem
    
    Database.init_db()
    palco = ft.Container(expand=True)
    # --- FUNÇÕES DE NAVEGAÇÃO ---

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
        # CORREÇÃO: Removido 'gerar_pdf' que causava o TypeError
        palco.content = relatorios.montar_tela_relatorios(
            page, 
            voltar=ir_para_home, 
            sync_nuvem=ir_para_sync, 
            gerar_qr=ir_para_qr # Deixe apenas os argumentos que o arquivo relatorios.py aceita
        )
        page.update()

    async def ir_para_configs(e=None):
        palco.content = configuracoes.montar_tela_configs(page, voltar=ir_para_home)
        page.update()

    # --- LÓGICA DE NEGÓCIO (PDF, EMAIL E SYNC) ---

    async def ir_para_gerar_e_enviar(e=None):
        """Busca dados, gera PDF e envia por e-mail"""
        page.snack_bar = ft.SnackBar(ft.Text("📊 Processando relatório..."))
        page.snack_bar.open = True
        page.update()

        try:
            # 1. Busca dados do banco (ajuste o nome do método se necessário)
            dados = Database.buscar_ultimas_leituras(limite=96)
            
            # 2. Gera o PDF usando seu módulo na pasta views/utils
            # O gerador_pdf.py deve retornar o caminho do arquivo criado
            caminho_pdf = gerador_pdf.gerar_pdf_relatorio(dados) 
            
            # 3. Envia por e-mail (usando sua senha de app)
            sucesso = await asyncio.to_thread(
                mailer.enviar_email_com_pdf, 
                "clodoaldomaldonado112@gmail.com", 
                caminho_pdf
            )
            
            if sucesso:
                page.snack_bar = ft.SnackBar(ft.Text("✅ Relatório enviado com sucesso!"), bgcolor="green")
            else:
                page.snack_bar = ft.SnackBar(ft.Text("❌ Erro no envio do e-mail."), bgcolor="red")
        except Exception as err:
            page.snack_bar = ft.SnackBar(ft.Text(f"⚠️ Erro: {err}"), bgcolor="orange")
        
        page.update()

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

    # --- INICIALIZAÇÃO ---
    palco.content = auth.criar_tela_login(page, ao_logar_sucesso=ir_para_home)
    page.add(palco)

    async def background_sync():
        while True:
            await asyncio.sleep(60)
            try: await asyncio.to_thread(SyncEngine.sincronizar_tudo)
            except: pass

    page.run_task(background_sync)

if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")