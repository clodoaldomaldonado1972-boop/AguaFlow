import flet as ft
import os
from database.database import get_supabase_client

# --- ALTERE SOMENTE AQUI ---
VERSION = "1.1.2"
CONDOMINIO = "Vivere Prudente"

class AppUpdater:
    # Atributo de classe para facilitar o acesso global
    VERSION = VERSION 
    CONDOMINIO = CONDOMINIO

    def __init__(self, page: ft.Page):
        self.page = page
        self.current_version = AppUpdater.VERSION
        
    @staticmethod
    def get_footer():
        """Gera o texto do rodapé para todas as telas do sistema."""
        return f"AguaFlow v{AppUpdater.VERSION} - {AppUpdater.CONDOMINIO}"

    @staticmethod
    async def checar_atualizacao_supabase(page: ft.Page):
        """Compara a versão local com a tabela 'versao_sistema' no Supabase[cite: 4]."""
        try:
            supabase = get_supabase_client()
            if not supabase: return False

            # Busca a última versão inserida no banco de dados[cite: 4]
            response = supabase.table("versao_sistema").select("numero_versao").order("id", desc=True).limit(1).execute()

            if response.data:
                versao_nuvem = response.data[0]["numero_versao"]
                # Se a versão for diferente da constante local, avisa o leiturista[cite: 4]
                if versao_nuvem != AppUpdater.VERSION:
                    AppUpdater.exibir_aviso(page, versao_nuvem)
                    return True
            return False
        except Exception as e:
            print(f"[UPDATER] Erro: {e}")
            return False

    @staticmethod
    def exibir_aviso(page: ft.Page, nova_versao):
        """Exibe um banner de atualização com cores seguras (strings)[cite: 1, 3, 4]."""
        def fechar(e):
            page.banner.open = False
            page.update()

        page.banner = ft.Banner(
            bgcolor="indigo", # Uso de string para evitar erro 'colors is not defined'[cite: 1]
            content=ft.Text(f"Nova versão disponível: {nova_versao}. Atualize para evitar erros no OCR.", color="white"),
            leading=ft.Icon(ft.icons.SYSTEM_UPDATE, color="orange", size=40),
            actions=[
                ft.TextButton("Mais tarde", on_click=fechar, style=ft.ButtonStyle(color="white")),
                ft.TextButton("Baixar Agora", on_click=lambda _: print("Link download"), style=ft.ButtonStyle(color="amber")),
            ],
        )
        page.banner.open = True
        page.update()