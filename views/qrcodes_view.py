import flet as ft
from database.database import Database

# Tenta importar o gerador, se falhar, define como None para não travar a tela
try:
    from utils.gerador_qr import gerar_qr_codes
except ImportError:
    gerar_qr_codes = None


def montar_tela_qrcodes(page: ft.Page):
    txt_unidade = ft.TextField(
        label="Unidade (ex: 101)",
        hint_text="Vazio = Condomínio Inteiro",
        width=300,
        border_radius=10
    )

    def disparar_geracao(tipo):
        if not gerar_qr_codes:
            page.snack_bar = ft.SnackBar(
                ft.Text("Erro: Gerador não encontrado"), bgcolor="red", open=True)
            page.update()
            return

        txt_unidade.disabled = True
        page.update()

        unid = txt_unidade.value.strip() if txt_unidade.value else None
        caminho = gerar_qr_codes(filtro_tipo=tipo, unidade_alvo=unid)

        if caminho:
            page.snack_bar = ft.SnackBar(
                ft.Text("PDF Gerado com sucesso!"), bgcolor="#2E7D32", open=True)

        txt_unidade.disabled = False
        page.update()

    return ft.View(
        route="/qrcodes",
        # Adicione alinhamento para garantir que apareça no centro
        vertical_alignment="center",
        horizontal_alignment="center",
        controls=[  # NOMEIE EXPLICITAMENTE O PARÂMETRO
            ft.AppBar(
                title=ft.Text("Gerador de Etiquetas"),
                center_title=True,
                bgcolor="blue"
            ),
            ft.Column(
                controls=[  # NOMEIE EXPLICITAMENTE AQUI TAMBÉM
                    ft.Icon("qr_code", size=60, color="blue"),
                    ft.Text("Emissão de Etiquetas", size=20, weight="bold"),
                    txt_unidade,
                    ft.Row(
                        controls=[
                            ft.ElevatedButton(
                                "ÁGUA", icon="water_drop", on_click=lambda _: disparar_geracao("AGUA")),
                            ft.ElevatedButton(
                                "GÁS", icon="local_fire_department", on_click=lambda _: disparar_geracao("GAS"))
                        ],
                        alignment="center"
                    ),
                    ft.ElevatedButton("GERAR AMBOS", icon="all_inbox", width=250,
                                      on_click=lambda _: disparar_geracao("AMBOS")),
                    ft.TextButton("Voltar ao Menu", icon="arrow_back",
                                  on_click=lambda _: page.go("/menu"))
                ],
                horizontal_alignment="center",
                spacing=15
            )
        ]
    )
