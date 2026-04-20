import flet as ft
from supabase import create_client, Client
import os


# --- ADICIONE ESTA LINHA AQUI NO TOPO ---
VERSION = "1.1.0" 

class AppUpdater:
    def __init__(self, page: ft.Page):
        self.page = page
        self.current_version = VERSION # Agora ele consegue ler a variável acima
        
    async def check_for_updates(self):
        # Seu código existente de verificação...
        print(f"Verificando atualizações para a versão {self.current_version}")
        pass

    @staticmethod
    async def checar_atualizacao_supabase(page: ft.Page):
        """Lógica principal de verificação no Supabase."""
        try:
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_KEY")
            if not url or not key: 
                return False
            
            supabase: Client = create_client(url, key)
            response = supabase.table("versao_sistema").select("numero_versao").order("id", desc=True).limit(1).execute()

            if response.data:
                versao_nuvem = response.data[0]["numero_versao"]
                if versao_nuvem != AppUpdater.VERSION:
                    AppUpdater.exibir_aviso(page, versao_nuvem)
                    return True
            return False
        except Exception as e:
            print(f"[UPDATER] Erro: {e}")
            return False

    @staticmethod
    def exibir_aviso(page: ft.Page, nova_versao):
        def fechar(e):
            page.banner.open = False
            page.update()

        page.banner = ft.Banner(
            bgcolor=ft.colors.INDIGO_900,
            color=ft.colors.WHITE,
            leading=ft.Icon(ft.icons.SYSTEM_UPDATE, color=ft.colors.AMBER, size=40),
            content=ft.Text(f"Nova versão disponível: {nova_versao}. Por favor, atualize o app."),
            actions=[
                ft.TextButton("Mais tarde", on_click=fechar),
                ft.TextButton("Baixar Agora", on_click=lambda _: print("Link de download")),
            ],
        )
        page.banner.open = True
        page.update()