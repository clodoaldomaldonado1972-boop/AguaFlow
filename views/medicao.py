import flet as ft
import asyncio
from database.database import Database

# --- IMPORT CORRIGIDO PARA A NOVA PASTA UTILS NA RAIZ ---
from utils import camera_utils


def montar_tela_medicao(page: ft.Page):
    # Recupera o filtro de leitura (Água ou Gás) da sessão da página
    filtro = getattr(page, "filtro_leitura", "Água")

    # Busca no banco o próximo registro que ainda não foi medido
    registro = Database.buscar_proximo_pendente(filtro)

    # 1. ESTADO: TUDO CONCLUÍDO
    if not registro:
        return ft.View(
            route="/medicao",
            bgcolor="#121417",
            vertical_alignment="center",
            horizontal_alignment="center",
            controls=[
                ft.Icon(ft.Icons.CHECK_CIRCLE, color="green", size=80),
                ft.Text("Leituras Concluídas!", size=28,
                        weight="bold", color="white"),
                ft.Text(
                    f"Todas as medições de {filtro} foram registradas.", color="grey"),
                ft.Container(height=20),
                ft.ElevatedButton(
                    "VOLTAR AO MENU",
                    icon=ft.Icons.HOME,
                    on_click=lambda _: page.go("/menu"),
                    style=ft.ButtonStyle(color="white", bgcolor="blue")
                )
            ]
        )

    # Desempacota os dados do registro (ID, Unidade, Tipo)
    _, unidade, tipo = registro

    # --- COMPONENTES DA INTERFACE ---
    lbl_unidade = ft.Text(
        f"UNIDADE: {unidade}", size=32, weight="bold", color="white")
    lbl_tipo = ft.Text(f"Medindo agora: {tipo}", color="blue", size=18)

    txt_leitura = ft.TextField(
        label=f"Valor para {tipo}",
        width=300,
        text_align="center",
        read_only=True,
        border_radius=10,
        focused_border_color="blue"
    )

    progress_ring = ft.ProgressRing(visible=False, color="blue")

    # --- FUNÇÕES DE LÓGICA ---

    async def salvar_leitura_click(e):
        """Registra o valor capturado no banco de dados SQLite."""
        if txt_leitura.value:
            res = Database.registrar_leitura(unidade, txt_leitura.value, tipo)
            if res.get('sucesso'):
                page.snack_bar = ft.SnackBar(
                    ft.Text(f"Leitura da Unidade {unidade} salva!"),
                    bgcolor="green"
                )
                page.snack_bar.open = True
                # Recarrega a tela para buscar o próximo pendente
                page.go("/medicao")
            page.update()

    async def capturar_click(e):
        """Ativa o motor de OCR da pasta utils."""
        progress_ring.visible = True
        page.update()

        try:
            def ao_concluir_ocr(resultado):
                progress_ring.visible = False
                if resultado.get('valor'):
                    txt_leitura.value = resultado.get('valor')
                    txt_leitura.read_only = False  # Permite correção manual se necessário
                page.update()

            # Chama o utilitário agora localizado em utils/camera_utils.py
            await camera_utils.inicializar_camera(page, ao_concluir_ocr)

        except Exception as ex:
            print(f"Erro na captura: {ex}")
            progress_ring.visible = False
            txt_leitura.read_only = False  # Em caso de falha, libera para digitação
            page.update()

    # --- CONSTRUÇÃO DA VIEW ---
    return ft.View(
        route="/medicao",
        bgcolor="#121417",
        appbar=ft.AppBar(
            title=ft.Text(f"Medição {filtro}"),
            bgcolor="#1e1e1e",
            leading=ft.IconButton(ft.Icons.ARROW_BACK,
                                  on_click=lambda _: page.go("/menu"))
        ),
        controls=[
            ft.Container(
                padding=30,
                content=ft.Column([
                    lbl_unidade,
                    lbl_tipo,
                    ft.Divider(height=20, color="transparent"),
                    progress_ring,
                    txt_leitura,
                    ft.ElevatedButton(
                        "ABRIR CÂMERA (OCR)",
                        icon=ft.Icons.CAMERA_ALT,
                        on_click=capturar_click,
                        width=300,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=10))
                    ),
                    ft.ElevatedButton(
                        "SALVAR NO BANCO",
                        icon=ft.Icons.SAVE,
                        on_click=salvar_leitura_click,
                        width=300,
                        bgcolor="green",
                        color="white",
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=10))
                    )
                ], horizontal_alignment="center", spacing=15)
            )
        ]
    )
