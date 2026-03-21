import flet as ft
import database.database as db
import re
from datetime import datetime
import asyncio


async def montar_tela(page, voltar_ao_menu, status_icon=None, status_text=None, on_next=None):
    """
    Tela de medição com validação completa, feedback visual e tratamento de erros.

    Esta é a "VITRINE" do AguaFlow - onde o zelador do Vivere Prudente insere as leituras
    sequencialmente, com validação em tempo real e feedback visual amigável.
    """

    # Inicia a verificação de conexão com a nuvem
    if status_icon is not None:
        status_icon.color = 'gray'
        status_icon.update()
    if status_text is not None:
        status_text.value = 'Sincronizando... 🟡'
        status_text.color = 'orange'
        status_text.update()

    cloud_icon = ft.Icon(ft.icons.Icons.CLOUD_QUEUE, color="gray", size=24)
    try:
        sync_result = db.Database.sync_to_supabase()
        # Se sincronização funcionou
        if sync_result.get('sucesso'):
            status_icon.color = 'green' if status_icon is not None else None
            status_text.value = f"Sincronizado 🟢 ({sync_result.get('sincronizados', 0)} sincs)"
            status_text.color = 'green'
            cloud_icon.color = 'green'
        else:
            status_icon.color = 'red' if status_icon is not None else None
            status_text.value = f"Aguardando Conexão 🔴  (Erro: {sync_result.get('mensagem')})"
            status_text.color = 'red'
            cloud_icon.color = 'orange'
    except Exception as e:
        # Falha de rede fica no modo offline aguardando reconexão
        if status_icon is not None:
            status_icon.color = 'red'
        if status_text is not None:
            status_text.value = f"Aguardando Conexão 🔴 (Falha de rede: {e})"
            status_text.color = 'red'
        cloud_icon.color = 'orange'

    if status_icon is not None:
        status_icon.update()
    if status_text is not None:
        status_text.update()

    # cloud_icon será adicionado na UI mais abaixo e atualizado pelo framework
    registro = db.Database.buscar_proximo_pendente()

    if not registro:
        # Tela de conclusão
        dlg_conclusao = ft.AlertDialog(
            title=ft.Text("✓ LEITURAS CONCLUÍDAS!", size=24,
                          weight="bold", color="green"),
            content=ft.Text(
                "Todas as unidades foram medidas com sucesso!", size=14),
            actions=[
                ft.TextButton("VOLTAR AO MENU",
                              on_click=lambda _: voltar_ao_menu())
            ]
        )
        page.dialog = dlg_conclusao
        dlg_conclusao.open = True
        page.update()
        return ft.Container()

    id_db, unidade, anterior, tipo = registro

    # Estado do formulário
    estado_ui = {
        'salvando': False,
        'mensagem_erro': '',
    }

    # Componentes da UI
    txt_valor = ft.TextField(
        label=f"Valor {tipo}",
        keyboard_type=ft.KeyboardType.NUMBER,
        autofocus=True,
        max_length=10,
        hint_text="Exemplo: 123.45",
        border_color="blue",
        focused_border_color="darkblue",
        on_focus=lambda e: txt_valor.update() if e.control.value else None
    )

    texto_anterior = ft.Text(
        f"Leitura anterior: {anterior} m³",
        size=12,
        color="gray"
    )

    btn_salvar = ft.FilledButton(
        content=ft.Text("💾 SALVAR E PRÓXIMO",
                        style=ft.TextStyle(size=16, weight="bold")),
        width=300,
        height=50
    )

    loading_spinner = ft.ProgressRing(
        width=40,
        height=40,
        visible=False,
        color="blue"
    )

    mensagem_feedback = ft.Text(
        "",
        size=12,
        color="red",
        text_align=ft.TextAlign.CENTER
    )

    # ========== HANDLERS ==========

    async def salvar(e):
        """Handler para botão SALVAR com feedback visual completo."""

        # Validação de entrada usando o database.py unificado
        validacao = db.Database.validar_numero(txt_valor.value)
        if not validacao['valido']:
            mensagem_feedback.value = validacao['mensagem']
            txt_valor.error_text = validacao['mensagem']
            mensagem_feedback.update()
            txt_valor.update()
            await txt_valor.focus()
            return

        # Estado: entrando em modo "salvando"
        estado_ui['salvando'] = True
        btn_salvar.disabled = True
        loading_spinner.visible = True
        mensagem_feedback.value = ""
        mensagem_feedback.update()
        btn_salvar.update()
        loading_spinner.update()

        try:
            valor = validacao['valor']

            # Salva no banco usando o database.py unificado
            resultado = db.Database.registrar_leitura(id_db, valor)

            # Correção: recebe apenas 3 valores em vez de 4
        id_db, unidade, anterior = registro
# Define tipo como padrão já que não está sendo retornado pela função
        if resultado.get('supabase_sync'):
                    cloud_icon.color = 'green'
                else:
                    cloud_icon.color = 'gray'
                cloud_icon.update()

                # Sucesso! Feedback visual
                mensagem_feedback.value = resultado['mensagem']
                mensagem_feedback.style = ft.TextStyle(
                    color="green", size=14, weight="bold")
                mensagem_feedback.update()

                # Pequeno delay para o usuário ver o sucesso
                await asyncio.sleep(1)
                # Carrega próximo (callback injetado a partir do main)
                if on_next:
                    await on_next()
                    return

                # Fallback: recarrega localmente
                nova_tela = await montar_tela(page, voltar_ao_menu)
                page.clean()
                if nova_tela:
                    page.add(nova_tela)
                page.update()
            else:
                # Erro retornado pelo database
                mensagem_feedback.value = resultado['mensagem']
                mensagem_feedback.style = ft.TextStyle(
                    color="red", size=12, weight="bold")
                mensagem_feedback.update()

                # Reseta botão
                estado_ui['salvando'] = False
                btn_salvar.disabled = False
                loading_spinner.visible = False
                btn_salvar.update()
                loading_spinner.update()
                await txt_valor.focus()

        except Exception as error:
            # Erro inesperado
            mensagem_feedback.value = f"❌ Erro inesperado: {str(error)}"
            mensagem_feedback.style = ft.TextStyle(
                color="red", size=12, weight="bold")
            mensagem_feedback.update()

            # Reseta botão
            estado_ui['salvando'] = False
            btn_salvar.disabled = False
            loading_spinner.visible = False
            btn_salvar.update()
            loading_spinner.update()
            await txt_valor.focus()

    async def pular(e):
        """Permite pular esta unidade e ir para a próxima (com confirmação)."""

        dlg_confirma = ft.AlertDialog(
            title=ft.Text("Pular unidade?"),
            content=ft.Text(f"Deseja pular a unidade {unidade}?"),
            actions=[
                ft.TextButton("NÃO", on_click=lambda _: fechar_dialogo()),
                ft.FilledButton(
                    content=ft.Text("SIM, PULAR"), on_click=lambda _: confirma_pular()),
            ]
        )

        def fechar_dialogo():
            dlg_confirma.open = False
            page.dialog = None
            page.update()

        async def confirma_pular():
            dlg_confirma.open = False
            page.dialog = None
            nova_tela = await montar_tela(page, voltar_ao_menu)
            page.clean()
            if nova_tela:
                page.add(nova_tela)
            page.update()

        page.dialog = dlg_confirma
        dlg_confirma.open = True
        page.update()

    # Vincula handler ao botão
    btn_salvar.on_click = salvar

    # Valida entrada EM TEMPO REAL ao digitar
    def validar_tempo_real(e):
        """Red/green feedback enquanto digita."""
        if txt_valor.value:
            validacao = db.Database.validar_numero(txt_valor.value)
            if validacao['valido']:
                txt_valor.border_color = "green"
                txt_valor.error_text = ""
            else:
                txt_valor.border_color = "red"
                txt_valor.error_text = validacao['mensagem']
        else:
            txt_valor.border_color = "blue"
            txt_valor.error_text = ""
        txt_valor.update()

    txt_valor.on_change = validar_tempo_real

    # ========== LAYOUT ==========

    return ft.Container(
        padding=20,
        content=ft.Column([
            # Cabeçalho
            ft.Row([
                ft.Text(f"APTO: {unidade}", size=32,
                        weight="bold", color="darkblue"),
                ft.Container(content=cloud_icon,
                             alignment=ft.alignment.Alignment.CENTER_RIGHT)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Text(f"Medidor: {tipo}", size=14, color="blue", weight="bold"),
            ft.Divider(height=10, color="lightgray"),

            # Informação anterior
            texto_anterior,
            ft.Container(height=20),

            # Campo de entrada
            txt_valor,
            ft.Container(height=5),

            # Feedback de validação
            mensagem_feedback,
            ft.Container(height=20),

            # Spinner + Botão
            ft.Row(
                [loading_spinner, btn_salvar],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=15
            ),

            ft.Container(height=20),

            # Botão pular (opcional)
            ft.TextButton(
                "⏭️ Pular esta unidade",
                on_click=pular,
                style=ft.ButtonStyle(color="orange")
            ),

        ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10
        )
    )
def process_registro(registro):
    try:
        id_db, unidade, anterior = registro
    except ValueError:
        id_db = None
        unidade = None
        anterior = None
        print("Erro: Registro não possui valores suficientes")

    # Resto do código que usa as variáveis id_db, unidade e anterior

# Exemplo de uso
registro = db.Database.buscar_proximo_pendente()
process_registro(registro)