import flet as ft
import asyncio
import urllib.parse
import views.styles as st
from utils.logger_config import enviar_report_erro


# ---------------------------------------------------------------------------
# Helpers de layout para o tutorial (IHC: consistência visual)
# ---------------------------------------------------------------------------

def _passo(numero: int, titulo: str, descricao: str, icone=None) -> ft.Container:
    """Bloco de passo numerado — padrão IHC de instrução sequencial."""
    return ft.Container(
        content=ft.Row(
            [
                ft.Container(
                    content=ft.Text(str(numero), size=16, weight="bold", color="white"),
                    width=36, height=36,
                    bgcolor=st.PRIMARY_BLUE,
                    border_radius=18,
                    alignment=ft.alignment.Alignment(0, 0),
                ),
                ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Icon(icone, size=16, color=st.ACCENT_ORANGE) if icone else ft.Container(width=0),
                                ft.Text(titulo, size=14, weight="bold", color="white"),
                            ],
                            spacing=4,
                        ),
                        ft.Text(descricao, size=12, color=st.GREY_TEXT),
                    ],
                    spacing=2,
                    expand=True,
                ),
            ],
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.START,
        ),
        padding=ft.Padding.symmetric(vertical=8, horizontal=4),
    )


def _aviso(texto: str, cor=None) -> ft.Container:
    """Caixa de destaque para alertas ou dicas."""
    cor = cor or st.ACCENT_ORANGE
    return ft.Container(
        content=ft.Row(
            [
                ft.Icon(ft.Icons.INFO_OUTLINE, color=cor, size=16),
                ft.Text(texto, size=12, color="white", expand=True),
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.START,
        ),
        bgcolor="#1E2126",
        border=ft.border.all(1, cor),
        border_radius=8,
        padding=10,
    )


def _secao(titulo: str, icone, controles: list) -> ft.ExpansionTile:
    """Seção retrátil — IHC: progressive disclosure, evita sobrecarga cognitiva."""
    return ft.ExpansionTile(
        leading=ft.Icon(icone, color=st.PRIMARY_BLUE),
        title=ft.Text(titulo, size=15, weight="bold", color="white"),
        icon_color="white54",
        collapsed_icon_color="white54",
        controls=[
            ft.Container(
                content=ft.Column(controles, spacing=4),
                padding=ft.Padding.only(left=12, right=4, bottom=8),
            )
        ],
    )


# ---------------------------------------------------------------------------
# View principal
# ---------------------------------------------------------------------------

def montar_tela_ajuda(page: ft.Page, on_back):
    user_data = getattr(page, "user_data", {}) or {}
    nome_leiturista = (
        user_data.get("nome")
        or user_data.get("email", "").split("@")[0].capitalize()
        or "Não identificado"
    )

    corpo_mensagem = (
        "Olá! Suporte AguaFlow. Estou no Condomínio Vivere Prudente e preciso de auxílio técnico.\n"
        f"Leiturista: {nome_leiturista}\n"
        "Aparelho: Android - AguaFlow v1.2.0\n"
        f"Contexto: {page.route}"
    )
    url_suporte = f"https://wa.me/5518981337316?text={urllib.parse.quote(corpo_mensagem)}"

    async def disparar_teste_erro(e):
        e.control.disabled = True
        e.control.text = "ENVIANDO TESTE..."
        page.update()
        try:
            erro_simulado = "SimulatedConnectionError: [TESTE] Falha ao alcançar o servidor Supabase (Timeout 30s)."
            await asyncio.to_thread(
                enviar_report_erro,
                mensagem_erro=erro_simulado,
                unidade="DEBUG-HALL",
                leiturista=nome_leiturista,
            )
            page.show_dialog(ft.SnackBar(
                ft.Text("✅ E-mail de teste enviado! Verifique o destinatário."),
                bgcolor=st.SUCCESS_GREEN,
            ))
        except Exception as ex:
            page.show_dialog(ft.SnackBar(
                ft.Text(f"❌ Erro no envio do teste: {ex}"),
                bgcolor=st.RED_ERROR,
            ))
        e.control.disabled = False
        e.control.text = "TESTE DE RELATÓRIO"
        page.update()

    # ------------------------------------------------------------------
    # Conteúdo das abas
    # ------------------------------------------------------------------

    aba_tutorial = ft.Column(
        [
            ft.Container(height=8),

            # Cabeçalho do tutorial
            ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(ft.Icons.SCHOOL_OUTLINED, size=48, color=st.PRIMARY_BLUE),
                        ft.Text("Tutorial do Sistema", size=20, weight="bold", color="white"),
                        ft.Text(
                            "Toque em cada seção para expandir o conteúdo.",
                            size=12, color=st.GREY_TEXT, text_align=ft.TextAlign.CENTER,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=6,
                ),
                padding=ft.Padding.symmetric(vertical=12, horizontal=16),
            ),

            ft.Divider(color="white10"),

            # ── SEÇÃO 1: PRIMEIROS PASSOS ──────────────────────────────
            _secao(
                "1. Primeiros Passos",
                ft.Icons.PLAY_CIRCLE_OUTLINE,
                [
                    _passo(1, "Faça o login",
                           "Insira seu e-mail e senha cadastrados. Ao entrar, o sistema salva sua sessão — na próxima abertura você já entra direto.",
                           ft.Icons.LOGIN),
                    _passo(2, "Menu principal",
                           "O menu central dá acesso a todas as funções. Use os botões grandes para navegar.",
                           ft.Icons.GRID_VIEW),
                    _passo(3, "Modo offline",
                           "Sem internet? O ícone ☁️✕ aparece no topo. Você pode medir normalmente — os dados ficam salvos no aparelho e sobem quando a conexão voltar.",
                           ft.Icons.CLOUD_OFF),
                ],
            ),

            # ── SEÇÃO 2: REALIZANDO UMA MEDIÇÃO ───────────────────────
            _secao(
                "2. Realizando uma Medição",
                ft.Icons.SPEED,
                [
                    _aviso(
                        "Esta é a função principal do sistema. Siga os passos na ordem.",
                        st.PRIMARY_BLUE,
                    ),
                    _passo(1, "Abra 'Medição'",
                           "No menu, toque em Medição. O sistema já seleciona a primeira unidade pendente do mês.",
                           ft.Icons.TOUCH_APP),
                    _passo(2, "Escolha o modo da ronda",
                           "Três opções aparecem ao entrar: ÁGUA (lê só hidrômetros), GÁS (lê só medidores de gás) ou MISTO (lê os dois). Após escolher, as outras opções somem — toque em 'trocar' para mudar.",
                           ft.Icons.SWAP_HORIZ),
                    _passo(3, "Selecione a unidade",
                           "O campo 'Unidade' mostra a sugestão automática. Você pode alterar tocando no campo.",
                           ft.Icons.APARTMENT),
                    _passo(4, "Digite a leitura",
                           "Informe o valor do hidrômetro (ex: 123,45). Apenas números são aceitos.",
                           ft.Icons.EDIT),
                    _passo(5, "Toque em SALVAR",
                           "O sistema confirma e avança para a próxima unidade pendente automaticamente.",
                           ft.Icons.SAVE),
                    _passo(6, "Fim de andar — barreira de segurança",
                           "Ao terminar o último apartamento de um andar, o sistema verifica se todos foram lidos. Se faltar algum, um aviso aparece: 'Voltar e medir' ou 'Seguir (salvar como nulo)'.",
                           ft.Icons.MEETING_ROOM),
                    _aviso(
                        "Modo MISTO — ordem de leitura por andar:\n"
                        "1) Lê TODOS os hidrômetros de água do andar (ex: 166→165→163/164→162→161)\n"
                        "2) Retorna ao primeiro e lê TODOS os medidores de gás do mesmo andar\n"
                        "3) Avança para o próximo andar e repete\n"
                        "4) Finaliza no TERREO GERAL ÁGUA (somente água)",
                        st.PRIMARY_BLUE,
                    ),
                    _aviso(
                        "Dica: se errar um valor, vá ao Histórico, localize a leitura e corrija antes de sincronizar.",
                    ),
                ],
            ),

            # ── SEÇÃO 3: USANDO O SCANNER ─────────────────────────────
            _secao(
                "3. Usando o Scanner QR Code",
                ft.Icons.QR_CODE_SCANNER,
                [
                    _passo(1, "Acesse 'Scanner'",
                           "No menu, toque em Scanner. Permita o acesso à câmera se solicitado.",
                           ft.Icons.CAMERA_ALT),
                    _passo(2, "Aponte para o QR Code",
                           "Enquadre o código QR da unidade na moldura azul. A leitura é automática.",
                           ft.Icons.CENTER_FOCUS_STRONG),
                    _passo(3, "Confirme a unidade",
                           "O sistema lê o código e redireciona para a tela de Medição com a unidade já preenchida.",
                           ft.Icons.CHECK_CIRCLE_OUTLINE),
                    _aviso(
                        "Ambiente escuro? Ative a lanterna do celular — o scanner funciona melhor com boa iluminação.",
                    ),
                ],
            ),

            # ── SEÇÃO 4: SINCRONIZAÇÃO ────────────────────────────────
            _secao(
                "4. Sincronizando os Dados",
                ft.Icons.CLOUD_UPLOAD,
                [
                    _passo(1, "Quando sincronizar?",
                           "Sincronize ao final de cada dia de medição ou quando o ícone de pendente aparecer.",
                           ft.Icons.SCHEDULE),
                    _passo(2, "Abra 'Sincronizar Dados'",
                           "No menu, toque em Sincronizar Dados. O sistema mostrará quantos registros aguardam envio.",
                           ft.Icons.SYNC),
                    _passo(3, "Aguarde a confirmação",
                           "A barra de progresso indica o envio. Aguarde a mensagem de sucesso antes de fechar.",
                           ft.Icons.HOURGLASS_BOTTOM),
                    _aviso(
                        "Importante: nunca feche o app durante a sincronização. Se perder conexão, tente novamente quando a internet voltar.",
                        st.RED_ERROR,
                    ),
                ],
            ),

            # ── SEÇÃO 5: HISTÓRICO E CORREÇÕES ───────────────────────
            _secao(
                "5. Histórico e Correções",
                ft.Icons.HISTORY,
                [
                    _passo(1, "Consulte o Histórico",
                           "No menu, toque em Histórico para ver todas as leituras registradas neste aparelho.",
                           ft.Icons.LIST_ALT),
                    _passo(2, "Filtre por unidade ou mês",
                           "Use os campos de filtro para localizar rapidamente uma leitura específica.",
                           ft.Icons.FILTER_LIST),
                    _passo(3, "Corrija antes de sincronizar",
                           "Leituras ainda não enviadas podem ser corrigidas. Após sincronizar, entre em contato com o administrador.",
                           ft.Icons.EDIT_NOTE),
                ],
            ),

            # ── SEÇÃO 6: DICAS E BOAS PRÁTICAS ───────────────────────
            _secao(
                "6. Dicas e Boas Práticas",
                ft.Icons.LIGHTBULB_OUTLINE,
                [
                    _aviso("Carregue o aparelho antes de sair para a ronda — medições consomem bateria."),
                    _aviso("Mantenha o celular com dados móveis ou Wi-Fi para sincronização em tempo real."),
                    _aviso("Ao terminar o mês, confirme com o administrador que todas as unidades foram lidas antes de fechar o ciclo."),
                    _aviso("Em caso de hidrômetro danificado ou sem acesso, registre 0 (zero) e informe ao administrador."),
                    _aviso(
                        "Faça logout ao passar o aparelho para outro leiturista, para que a sessão seja iniciada com as credenciais corretas.",
                        st.RED_ERROR,
                    ),
                ],
            ),

            ft.Container(height=16),
        ],
        spacing=4,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )

    aba_suporte = ft.Column(
        [
            ft.Container(height=20),
            ft.Icon(ft.Icons.HELP_CENTER_OUTLINED, size=80, color=st.PRIMARY_BLUE),
            ft.Text("Suporte Técnico", size=24, weight="bold", color="white"),
            ft.Container(height=8),
            ft.Text(
                "Não conseguiu resolver pelo tutorial?\nFale diretamente com o suporte.",
                size=13, color=st.GREY_TEXT, text_align=ft.TextAlign.CENTER,
            ),
            ft.Container(height=8),
            ft.Container(
                content=ft.Row(
                    [
                        ft.Icon(ft.Icons.PERSON_OUTLINE, color=st.PRIMARY_BLUE, size=16),
                        ft.Text(f"Leiturista: {nome_leiturista}", size=13, color="white"),
                    ],
                    spacing=6,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                bgcolor="#1E2126",
                border_radius=8,
                padding=ft.Padding.symmetric(vertical=8, horizontal=16),
            ),
            ft.Container(height=8),
            ft.ElevatedButton(
                "CHAMAR SUPORTE NO WHATSAPP",
                icon="whatsapp",
                style=st.BTN_SPECIAL,
                url=url_suporte,
                width=320, height=60,
            ),
            ft.ElevatedButton(
                "TESTE DE RELATÓRIO",
                icon="email_outlined",
                on_click=disparar_teste_erro,
                width=320, height=60,
            ),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=12,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )

    return ft.View(
        route="/ajuda",
        bgcolor=st.BG_DARK,
        appbar=ft.AppBar(
            title=ft.Text("Ajuda"),
            bgcolor=st.PRIMARY_BLUE,
            leading=ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=on_back),
        ),
        controls=[
            ft.Tabs(
                content=ft.Column(
                    [
                        ft.TabBar(
                            tabs=[
                                ft.Tab(label="Tutorial", icon=ft.Icons.SCHOOL_OUTLINED),
                                ft.Tab(label="Suporte", icon=ft.Icons.SUPPORT_AGENT),
                            ],
                        ),
                        ft.TabBarView(
                            controls=[aba_tutorial, aba_suporte],
                            expand=True,
                        ),
                    ],
                    expand=True,
                    spacing=0,
                ),
                length=2,
                selected_index=0,
                expand=True,
            )
        ],
        padding=0,
    )
