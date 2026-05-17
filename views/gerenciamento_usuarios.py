import flet as ft
import views.styles as st
from utils.auth_utils import validar_sessao
from database.database import Database
from database.supabase_client import deletar_usuario_supabase, testar_conexao_supabase


def montar_tela_usuarios(page: ft.Page):
    # Proteção de Rota: Apenas Administradores podem acessar esta View
    auth_check = validar_sessao(page, "/usuarios", required_role="admin")
    if auth_check:
        return auth_check

    lista_usuarios_ui = ft.Column(
        spacing=10, scroll=ft.ScrollMode.ADAPTIVE, expand=True)

    # Campos para o diálogo de criação de usuário (Definidos no escopo da view)
    txt_novo_nome = ft.TextField(label="Nome Completo", width=300)
    txt_novo_email = ft.TextField(label="E-mail", width=300)
    txt_nova_senha = ft.TextField(
        label="Senha", password=True, can_reveal_password=True, width=300)
    dd_nova_role = ft.Dropdown(
        label="Cargo",
        width=300,
        options=[
            ft.dropdown.Option("user", text="Usuário"),
            ft.dropdown.Option("admin", text="Admin"),
        ],
        value="user"
    )

    txt_busca = ft.TextField(
        label="Buscar por nome ou e-mail",
        prefix_icon="search",
        on_change=lambda e: carregar_usuarios(e.control.value),
        width=350
    )

    async def alterar_role(email, nova_role):
        """Atualiza a role do usuário no banco local com tratamento de erro e resiliência."""
        try:
            # 1. Atualização no SQLite (Prioridade Offline-First)
            if Database.atualizar_role_usuario(email, nova_role):
                # 2. Tentativa de verificar conectividade
                conexao = testar_conexao_supabase()
                
                if conexao['conectado']:
                    Database.marcar_usuario_sincronizado(email)
                    msg = f"Cargo de {email} atualizado e sincronizado na nuvem."
                    cor = st.SUCCESS_GREEN
                else:
                    msg = f"Alteração salva localmente. Sincronização pendente (Sem Sinal)."
                    cor = st.ACCENT_ORANGE
                
                page.show_dialog(ft.SnackBar(ft.Text(msg), bgcolor=cor))
                carregar_usuarios()
            else:
                raise Exception("Falha na gravação local.")
        except Exception as ex:
            page.show_dialog(ft.SnackBar(
                ft.Text(f"Erro ao processar alteração: {str(ex)}"),
                bgcolor=st.RED_ERROR
            ))
        page.update()

    def deletar_usuario_confirmado(email):
        """Executa a exclusão do usuário no banco local e tenta na nuvem."""
        # 1. Tenta deletar do Supabase (Requer privilégios de Admin no Supabase)
        res_cloud = deletar_usuario_supabase(email)

        # 2. Deleta do SQLite local
        if Database.deletar_usuario_local(email):
            msg = f"Usuário {email} excluído com sucesso!"
            if not res_cloud['sucesso']:
                msg += f" (Nuvem: {res_cloud['mensagem']})"

            page.show_dialog(ft.SnackBar(ft.Text(msg), bgcolor=st.SUCCESS_GREEN))
            carregar_usuarios()
        else:
            page.show_dialog(ft.SnackBar(
                ft.Text("Erro ao excluir no banco local."), bgcolor=st.RED_ERROR))

        page.update()

    def abrir_dialogo_exclusao(email):
        def fechar(e):
            page.pop_dialog()

        def confirmar(e):
            fechar(e)
            deletar_usuario_confirmado(email)

        page.show_dialog(ft.AlertDialog(
            title=ft.Text("Confirmar Exclusão"),
            content=ft.Text(
                f"Deseja realmente excluir o usuário {email}? Esta ação é irreversível."),
            actions=[
                ft.TextButton("Cancelar", on_click=fechar),
                ft.ElevatedButton("Excluir", bgcolor="red",
                                  color="white", on_click=confirmar),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        ))

    def criar_novo_usuario_dialog(e):
        """Abre o diálogo para criar um novo usuário."""
        def fechar_dialogo(e):
            page.pop_dialog()

        def salvar_novo_usuario(e):
            nome = txt_novo_nome.value
            email = txt_novo_email.value
            senha = txt_nova_senha.value
            role = dd_nova_role.value

            if not nome or not email or not senha:
                page.show_dialog(ft.SnackBar(
                    ft.Text("Todos os campos são obrigatórios."), bgcolor=st.RED_ERROR))
                page.update()
                return

            if Database.email_existe(email):
                page.show_dialog(ft.SnackBar(
                    ft.Text("E-mail já cadastrado."), bgcolor=st.RED_ERROR))
                page.update()
                return

            if Database.criar_usuario(nome, email, senha, role):
                page.show_dialog(ft.SnackBar(
                    ft.Text(f"Usuário {email} criado com sucesso!"), bgcolor=st.SUCCESS_GREEN))
                fechar_dialogo(e)
                carregar_usuarios()
            else:
                page.show_dialog(ft.SnackBar(
                    ft.Text("Erro ao criar usuário."), bgcolor=st.RED_ERROR))
            page.update()

        page.show_dialog(ft.AlertDialog(
            modal=True,
            title=ft.Text("Criar Novo Usuário"),
            content=ft.Column([txt_novo_nome, txt_novo_email,
                              txt_nova_senha, dd_nova_role]),
            actions=[
                ft.TextButton("Cancelar", on_click=fechar_dialogo),
                ft.ElevatedButton("Salvar", on_click=salvar_novo_usuario),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        ))

    def carregar_usuarios(search_term: str = ""):
        """Busca usuários no banco e monta os cards na interface."""
        lista_usuarios_ui.controls.clear()
        usuarios = Database.listar_usuarios()
        if search_term:
            search_term_lower = search_term.lower()
            usuarios = [
                user for user in usuarios if search_term_lower in user['nome'].lower() or search_term_lower in user['email'].lower()
            ]

        if not usuarios:
            lista_usuarios_ui.controls.append(
                ft.Text("Nenhum usuário encontrado.", color="grey"))

        # Ordena a lista de usuários para exibir administradores primeiro
        usuarios.sort(key=lambda x: (x['role'] != 'admin', x['nome'].lower()))
        for user in usuarios:
            email = user['email']
            role = user['role']

            # Card de Usuário
            lista_usuarios_ui.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon(
                            ft.Icons.PERSON, color=st.PRIMARY_BLUE if role == "admin" else "grey"),
                        ft.Column([
                            ft.Row([
                                ft.Text(user['nome'], weight="bold", size=14),
                                # Indicador de Sincronização (Nuvem cortada se offline)
                                ft.Icon(
                                    ft.Icons.CLOUD_OFF_OUTLINED,
                                    color=st.ACCENT_ORANGE,
                                    size=16,
                                    tooltip="Alteração local pendente de sincronia",
                                    visible=user.get('sincronizado', 1) == 0
                                )
                            ], spacing=5),
                            ft.Text(email, size=11, color="grey"),
                        ], expand=True),
                        ft.Dropdown(
                            value=role,
                            width=110,
                            text_size=12,
                            options=[
                                ft.dropdown.Option("user", text="Usuário"),
                                ft.dropdown.Option("admin", text="Admin"),
                            ],
                            on_select=lambda e, u=email: page.run_task(
                                alterar_role, u, e.control.value)
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINE,
                            icon_color=st.RED_ERROR,
                            tooltip="Excluir Usuário",
                            on_click=lambda e, u=email: abrir_dialogo_exclusao(u),
                            visible=email != page.user_data.get("email")
                        ),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=10,
                    bgcolor="#1E2126",
                    border_radius=10,
                    border=ft.border.all(1, "white10")
                )
            )
        page.update()

    carregar_usuarios()  # Carrega a lista inicial sem termo de busca

    return ft.View(
        route="/usuarios",
        bgcolor=st.BG_DARK,
        appbar=ft.AppBar(
            title=ft.Text("Gestão de Acessos"),
            bgcolor=st.PRIMARY_BLUE,
            leading=ft.IconButton(
                icon=ft.Icons.ARROW_BACK, on_click=lambda _: page.push_route("/menu"))
        ),
        controls=[
            ft.Container(
                padding=20,
                expand=True,
                content=ft.Column([
                    ft.Container(height=10),
                    txt_busca,
                    ft.Container(height=10),
                    ft.Text("CONTROLE DE CARGOS", size=12,
                            color="grey", weight="bold"),
                    lista_usuarios_ui,
                    ft.Container(height=10),
                    ft.ElevatedButton(
                        "CRIAR NOVO USUÁRIO",
                        icon="person_add",
                        on_click=criar_novo_usuario_dialog,
                        width=350,
                        height=50,
                        style=st.BTN_MAIN
                    ),
                    ft.Container(height=5),
                    ft.TextButton("Voltar ao Menu",
                                  on_click=lambda _: page.push_route("/menu"))
                ], expand=True)
            )
        ]
    )
