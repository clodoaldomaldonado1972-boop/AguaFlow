import flet as ft
from supabase import create_client, Client
import os

class AppUpdater:
    # --- VERSÃO LOCAL DO APP ---
    VERSION = "1.0.2"
    
    @staticmethod
    def get_version_info():
        return f"v{AppUpdater.VERSION}"

    @staticmethod
    async def checar_atualizacao_supabase(page: ft.Page):
        """Verifica se a versão na nuvem é diferente da instalada."""
        try:
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_KEY")
            supabase: Client = create_client(url, key)

            # Busca a versão mais recente cadastrada
            response = supabase.table("versao_sistema").select("numero_versao").order("id", desc=True).limit(1).execute()

            if response.data:
                versao_nuvem = response.data[0]["numero_versao"]
                
                # Se na nuvem estiver '1.0.3' e aqui for '1.0.2', ele avisa
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
            content=ft.Text(f"Nova versão disponível no servidor: {nova_versao}. Por favor, instale a atualização."),
            actions=[
                ft.TextButton("Mais tarde", on_click=fechar),
                ft.TextButton("Baixar APK", on_click=lambda _: page.launch_url("SEU_LINK_DO_GOOGLE_DRIVE")),
            ],
        )
        page.banner.open = True
        page.update()