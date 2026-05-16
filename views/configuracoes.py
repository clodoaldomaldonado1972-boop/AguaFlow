import flet as ft
import views.styles as st
from utils.auth_utils import validar_sessao
from database.database import Database, get_supabase_client
from database.supabase_client import deletar_usuario_supabase # Import the new delete function
from utils.audio_utils import tocar_alerta # Assuming this exists for feedback

def montar_tela_configs(page: ft.Page):
    # Proteção de Rota
    auth_check = validar_sessao(page, "/configuracoes")
    if auth_check:
        return auth_check

    user_email = page.user_data.get("email") if page.user_data else "Desconhecido"
    supabase = get_supabase_client()

    txt_nova_senha = st.campo_estilo("Nova Senha", password=True)
    txt_confirmar_senha = st.campo_estilo("Confirmar Nova Senha", password=True)
    lbl_mensagem = ft.Text("", size=12)

    async def trocar_senha_clique(e):
        nova = txt_nova_senha.value
        confirma = txt_confirmar_senha.value

        if not nova or not confirma:
            lbl_mensagem.value = "Por favor, preencha as senhas."
            lbl_mensagem.color = "orange"
            page.update()
            return

        if nova != confirma:
            lbl_mensagem.value = "As senhas não coincidem."
            lbl_mensagem.color = "red"
            page.update()
            return
        
        if len(nova) < 6: # Basic password strength check
            lbl_mensagem.value = "A senha deve ter no mínimo 6 caracteres."
            lbl_mensagem.color = "red"
            page.update()
            return
        
        # 1. Tenta atualizar no Supabase (se estiver online)
        sucesso_cloud = False
        if supabase:
            try:
                res = supabase.auth.update_user({"password": nova})
                if res.user:
                    sucesso_cloud = True
            except Exception as ex:
                print(f"⚠️ Erro ao atualizar senha na nuvem: {ex}")

        # 2. Atualiza no SQLite local
        sucesso_local = Database.atualizar_senha(user_email, nova)

        if sucesso_local:
            msg = "Senha atualizada com sucesso!" if sucesso_cloud else "Senha atualizada localmente."
            page.show_dialog(ft.SnackBar(ft.Text(msg), bgcolor=st.SUCCESS_GREEN))
            txt_nova_senha.value = ""
            txt_confirmar_senha.value = ""
            lbl_mensagem.value = ""
        else:
            page.show_dialog(ft.SnackBar(ft.Text("Erro ao atualizar senha no dispositivo."), bgcolor=st.RED_ERROR))

        page.update()

    async def limpar_cache_local_clique(e):
        """Limpa o cache local do aplicativo (leituras e logs de sincronização)."""
        if Database.limpar_cache_local():
            page.show_dialog(ft.SnackBar(
                ft.Text("Cache local limpo com sucesso!"),
                bgcolor=st.SUCCESS_GREEN
            ))
            tocar_alerta(page, "sucesso")
        else:
            page.show_dialog(ft.SnackBar(
                ft.Text("Erro ao limpar cache local."),
                bgcolor=st.RED_ERROR
            ))
        page.update()

    async def excluir_conta_clique(e):
        """Exclui a conta do usuário localmente e no Supabase."""
        # 1. Tenta deletar do Supabase
        sucesso_cloud = False
        if supabase:
            try:
                result = deletar_usuario_supabase(user_email)
                sucesso_cloud = result['sucesso']
                if not sucesso_cloud:
                    print(f"Erro ao deletar do Supabase: {result['mensagem']}")
            except Exception as ex:
                print(f"⚠️ Erro ao deletar conta na nuvem: {ex}")

        # 2. Deleta do SQLite local
        sucesso_local = Database.deletar_usuario_local(user_email)

        if sucesso_local:
            msg = "Conta excluída com sucesso!"
            if not sucesso_cloud:
                msg += " (Falha ao excluir na nuvem)"
            page.show_dialog(ft.SnackBar(ft.Text(msg), bgcolor=st.SUCCESS_GREEN))
            tocar_alerta(page, "sucesso")
            page.user_data = {}
            page.go("/")
        else:
            page.show_dialog(ft.SnackBar(
                ft.Text("Erro ao excluir conta no dispositivo."), bgcolor=st.RED_ERROR))
            tocar_alerta(page, "erro")

        page.update()

    async def confirmar_excluir_conta(e):
        """Exibe um diálogo de confirmação antes de excluir a conta."""
        def realizar_exclusao_confirmada(e):
            page.pop_dialog()
            page.run_task(excluir_conta_clique, e)

        def cancelar_exclusao(e):
            page.pop_dialog()

        page.show_dialog(ft.AlertDialog(
            title=ft.Text("Confirmar Exclusão de Conta"),
            content=ft.Text(
                "Deseja realmente excluir sua conta? Esta ação é irreversível e apagará seus dados."),
            actions=[
                ft.TextButton("Sim", on_click=realizar_exclusao_confirmada),
                ft.TextButton("Não", on_click=cancelar_exclusao),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        ))

    return ft.View(
        route="/configuracoes",
        bgcolor=st.BG_DARK,
        appbar=ft.AppBar(
            title=ft.Text("Configurações"),
            bgcolor=st.PRIMARY_BLUE,
            leading=ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=lambda _: page.go("/menu"))
        ),
        controls=[
            ft.Column([
                ft.Container(height=20),
                ft.Icon(ft.Icons.LOCK_PERSON, size=64, color=st.PRIMARY_BLUE),
                ft.Text("Trocar Senha", size=20, weight="bold"),
                ft.Text(f"Utilizador: {user_email}", size=14, color="grey"),
                
                ft.Container(height=10),
                txt_nova_senha,
                txt_confirmar_senha,
                lbl_mensagem,
                
                ft.ElevatedButton(
                    "ATUALIZAR SENHA", 
                    on_click=trocar_senha_clique,
                    width=320,
                    height=50,
                    style=st.BTN_MAIN
                ),
                
                ft.Divider(height=40, color="white10"),
                ft.TextButton("Voltar ao Menu Principal", on_click=lambda _: page.go("/menu"))
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, scroll=ft.ScrollMode.AUTO, expand=True)
        ]
    )