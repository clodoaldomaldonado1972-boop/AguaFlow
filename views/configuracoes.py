import flet as ft
import asyncio
from utils.preferencias_leitura import PreferenciasLeitura
from utils.diagnostico import DiagnosticoSistema

def montar_tela_configs(page: ft.Page, voltar):
    # Recupera o e-mail da sessão para exibir no perfil
    user_email_logado = getattr(page, "user_email", "Visitante")

    # --- FUNÇÃO: TESTE DE SISTEMA ---
    # Rota Lógica: Aciona a classe DiagnosticoSistema para verificar DB e Nuvem
    async def realizar_teste_sistema(e):
        btn_teste.disabled = True
        status_icon.color = "orange"
        status_text.value = "Verificando componentes..."
        page.update()

        sucesso, mensagem = await DiagnosticoSistema.executar_checkup_completo()

        status_icon.color = "green" if sucesso else "red"
        status_text.value = mensagem
        status_text.color = "green" if sucesso else "red"
        btn_teste.disabled = False
        page.update()

    # --- FUNÇÃO: SALVAR E-MAIL ---
    # Rota Lógica: Valida e armazena o e-mail de destino dos alertas
    def salvar_email_notificacao(e):
        email = txt_email_notif.value
        if "@" in email and "." in email:
            page.snack_bar = ft.SnackBar(ft.Text(f"E-mail {email} salvo!"), bgcolor="green")
        else:
            page.snack_bar = ft.SnackBar(ft.Text("E-mail inválido!"), bgcolor="red")
        page.snack_bar.open = True
        page.update()

    # --- FUNÇÃO: LOGOUT ---
    # Rota Lógica: Limpa a sessão e redireciona para a tela de Login
    def acao_sair(e):
        page.user_email = None
        page.go("/login")

    # Componentes de Interface (UI)
    txt_email_notif = ft.TextField(label="E-mail para Alertas", value=user_email_logado, expand=True)
    status_icon = ft.Icon(ft.icons.DASHBOARD_RENAME_KEYBOARD, color="grey")
    status_text = ft.Text("Sistema não testado", color="grey")
    btn_teste = ft.ElevatedButton("TESTAR CONEXÃO", on_click=realizar_teste_sistema)

    return ft.View(
        route="/configuracoes",
        appbar=ft.AppBar(
            title=ft.Text("Configurações"),
            leading=ft.IconButton(ft.icons.ARROW_BACK, on_click=voltar) # Rota de volta ao Menu
        ),
        controls=[
            ft.Column([
                ft.Text("CONTA E PERFIL", size=16, weight="bold"),
                ft.ListTile(leading=ft.Icon(ft.icons.PERSON), title=ft.Text("Usuário"), subtitle=ft.Text(user_email_logado)),
                
                ft.Divider(),
                ft.Text("ALERTAS POR E-MAIL", size=16, weight="bold"),
                ft.Row([txt_email_notif, ft.IconButton(ft.icons.SAVE, on_click=salvar_email_notificacao)]),
                
                ft.Divider(),
                ft.Text("CONFIGURAÇÕES TÉCNICAS", size=16, weight="bold"),
                ft.Switch(
                    label="Modo OCR (Leitura por Câmera)", 
                    value=PreferenciasLeitura.get_modo_ocr(),
                    on_change=lambda e: PreferenciasLeitura.set_modo_ocr(e.control.value)
                ),
                
                ft.Container(
                    bgcolor="#1e1e1e", padding=15, border_radius=10,
                    content=ft.Column([
                        ft.Row([status_icon, status_text]),
                        ft.Row([btn_teste, ft.TextButton("VER SAÚDE", on_click=lambda _: page.go("/dashboard_saude"))])
                    ])
                ),
                
                ft.ElevatedButton("SAIR DO APP", bgcolor="red", color="white", on_click=acao_sair)
            ], scroll=ft.ScrollMode.ADAPTIVE, spacing=20, padding=20)
        ]
    )