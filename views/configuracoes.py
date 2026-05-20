import flet as ft
import asyncio
import views.styles as st
from utils.auth_utils import validar_sessao
from database.database import Database, get_supabase_client
from database.supabase_client import deletar_usuario_supabase
from utils.audio_utils import tocar_alerta
from utils.backup import BackupManager

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
            page.open(ft.SnackBar(ft.Text(msg), bgcolor=st.SUCCESS_GREEN))
            txt_nova_senha.value = ""
            txt_confirmar_senha.value = ""
            lbl_mensagem.value = ""
        else:
            page.open(ft.SnackBar(ft.Text("Erro ao atualizar senha no dispositivo."), bgcolor=st.RED_ERROR))

        page.update()

    async def limpar_cache_local_clique(e):
        """Limpa o cache local do aplicativo (leituras e logs de sincronização)."""
        if Database.limpar_cache_local():
            page.open(ft.SnackBar(
                ft.Text("Cache local limpo com sucesso!"),
                bgcolor=st.SUCCESS_GREEN
            ))
            tocar_alerta(page, "sucesso")
        else:
            page.open(ft.SnackBar(
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
            page.open(ft.SnackBar(ft.Text(msg), bgcolor=st.SUCCESS_GREEN))
            tocar_alerta(page, "sucesso")
            page.user_data = {}
            page.go("/")
        else:
            page.open(ft.SnackBar(
                ft.Text("Erro ao excluir conta no dispositivo."), bgcolor=st.RED_ERROR))
            tocar_alerta(page, "erro")

        page.update()

    async def confirmar_excluir_conta(e):
        """Exibe um diálogo de confirmação antes de excluir a conta."""
        def realizar_exclusao_confirmada(e):
            page.close(page.dialog)
            page.run_task(excluir_conta_clique, e)

        def cancelar_exclusao(e):
            page.close(page.dialog)

        page.open(ft.AlertDialog(
            title=ft.Text("Confirmar Exclusão de Conta"),
            content=ft.Text(
                "Deseja realmente excluir sua conta? Esta ação é irreversível e apagará seus dados."),
            actions=[
                ft.TextButton("Sim", on_click=realizar_exclusao_confirmada),
                ft.TextButton("Não", on_click=cancelar_exclusao),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        ))

    # --- SEÇÃO: GESTÃO DE BACKUPS ---
    lista_backups_col = ft.Column(spacing=4)
    lbl_backup_status = ft.Text("", size=12)

    def carregar_lista_backups():
        lista_backups_col.controls.clear()
        backups = BackupManager.listar_backups()
        if not backups:
            lista_backups_col.controls.append(
                ft.Text("Nenhum backup encontrado.", color=st.GREY_TEXT, italic=True, size=12)
            )
        for b in backups:
            def on_restaurar(ev, arq=b["arquivo"], nome=b["nome"]):
                def confirmar(ev2):
                    page.close(page.dialog)
                    page.run_task(_restaurar_async, arq, nome)

                page.open(ft.AlertDialog(
                    modal=True,
                    title=ft.Text("Restaurar Backup"),
                    content=ft.Text(
                        f"Restaurar o banco a partir de:\n{nome}\n\nO banco atual será substituído.",
                        size=13,
                    ),
                    actions=[
                        ft.TextButton("Restaurar", on_click=confirmar),
                        ft.TextButton("Cancelar", on_click=lambda _: page.close(page.dialog)),
                    ],
                    actions_alignment=ft.MainAxisAlignment.END,
                ))

            lista_backups_col.controls.append(ft.Container(
                content=ft.Row([
                    ft.Column([
                        ft.Text(b["nome"], size=11, weight="bold"),
                        ft.Text(f"{b['data']}  ·  {b['tamanho_kb']} KB", size=11, color=st.GREY_TEXT),
                    ], spacing=1, expand=True),
                    ft.IconButton(
                        icon=ft.Icons.RESTORE,
                        icon_color=st.ACCENT_ORANGE,
                        icon_size=20,
                        tooltip="Restaurar este backup",
                        on_click=on_restaurar,
                    ),
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor="#1E2126",
                border_radius=8,
                padding=ft.Padding.symmetric(horizontal=10, vertical=6),
            ))
        try:
            page.update()
        except Exception:
            pass

    async def _restaurar_async(arq, nome):
        lbl_backup_status.value = f"⏳ Restaurando {nome}..."
        lbl_backup_status.color = "grey"
        page.update()
        resultado = await asyncio.to_thread(BackupManager.restaurar_backup, arq)
        if resultado["sucesso"]:
            lbl_backup_status.value = f"✅ {resultado['mensagem']}"
            lbl_backup_status.color = "green"
        else:
            lbl_backup_status.value = f"❌ {resultado['mensagem']}"
            lbl_backup_status.color = st.RED_ERROR
        page.update()

    async def criar_backup_agora(_):
        lbl_backup_status.value = "⏳ Criando backup..."
        lbl_backup_status.color = "grey"
        page.update()
        ok = await asyncio.to_thread(BackupManager.executar_backup_seguranca)
        if ok:
            lbl_backup_status.value = "✅ Backup criado com sucesso."
            lbl_backup_status.color = "green"
            carregar_lista_backups()
        else:
            lbl_backup_status.value = "❌ Falha ao criar backup."
            lbl_backup_status.color = st.RED_ERROR
        page.update()

    carregar_lista_backups()

    secao_backup = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.BACKUP, color=st.ACCENT_ORANGE, size=28),
                ft.Text("Gestão de Backups", size=18, weight="bold"),
            ], spacing=8),
            lbl_backup_status,
            ft.ElevatedButton(
                "CRIAR BACKUP AGORA",
                icon=ft.Icons.SAVE,
                on_click=lambda e: page.run_task(criar_backup_agora, e),
                style=ft.ButtonStyle(
                    bgcolor=st.ACCENT_ORANGE, color="white",
                    shape=ft.RoundedRectangleBorder(radius=12),
                ),
                width=280, height=46,
            ),
            ft.Divider(height=10, color="white10"),
            ft.Text("Backups disponíveis:", size=13, color=st.GREY_TEXT),
            lista_backups_col,
        ], spacing=8),
        padding=20,
        bgcolor="#25282D",
        border_radius=15,
        width=360,
    )

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
                secao_backup,
                ft.Divider(height=30, color="white10"),
                ft.TextButton("Voltar ao Menu Principal", on_click=lambda _: page.go("/menu"))
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, scroll=ft.ScrollMode.AUTO, expand=True)
        ]
    )