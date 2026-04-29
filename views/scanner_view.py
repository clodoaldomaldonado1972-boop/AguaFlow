import flet as ft
from views import styles as st

def montar_tela_scanner(page: ft.Page):
    # Recupera o modo da sessão (definido na tela de medição)
    modo_atual = page.session.get("modo_leitura") or "AGUA"
    
    lbl_status = ft.Text(f"MODO: {modo_atual}", color="white", size=16, weight="bold")
    
    # Campos que receberão os dados do OCR
    txt_unid = ft.TextField(
        label="Unidade Detectada", 
        read_only=True, 
        border_radius=12, 
        bgcolor="#1E2126",
        width=300
    )
    
    txt_val = ft.TextField(
        label="Valor da Leitura", 
        border_radius=12, 
        bgcolor="#1E2126",
        width=300,
        input_filter=ft.InputFilter(allow=True, regex_string=r"^[0-9]*[.]?[0-9]{0,3}$"),
        hint_text="000.000"
    )

    async def fechar_e_voltar(e):
        if not txt_val.value:
            page.snack_bar = ft.SnackBar(ft.Text("Nenhum valor detectado!"))
            page.snack_bar.open = True
            page.update()
            return
            
        page.session.set("unidade_scanner", txt_unid.value)
        page.session.set("valor_scanner", txt_val.value)
        page.go("/medicao")

    # --- RETORNO DA VIEW (ATENÇÃO AOS FECHAMENTOS ABAIXO) ---
    return ft.View(
        route="/scanner",
        bgcolor=st.BG_DARK,
        appbar=ft.AppBar(
            title=ft.Text("Scanner OCR"), 
            bgcolor=st.BG_DARK,
            center_title=True,
            leading=ft.IconButton(ft.icons.ARROW_BACK, on_click=lambda _: page.go("/medicao"))
        ),
        controls=[ # <--- LINHA 68: ABRE LISTA DE CONTROLS
            ft.Column([
                ft.Container(
                    content=ft.Stack([
                        ft.Icon(ft.icons.CAMERA_REAR, size=150, color="grey"),
                        ft.Icon(ft.icons.CROP_FREE, size=200, color="blue", opacity=0.5),
                    ]),
                    alignment=ft.alignment.center,
                    padding=20
                ),
                ft.Text("Aponte para o Hidrômetro", size=16, weight="bold", color="white"),
                lbl_status,
                ft.Container(height=10),
                txt_unid,
                txt_val,
                ft.Container(height=20),
                ft.Row([
                    ft.ElevatedButton(
                        "CONFIRMAR", 
                        icon=ft.icons.CHECK, 
                        on_click=fechar_e_voltar, 
                        style=st.BTN_SPECIAL if hasattr(st, "BTN_SPECIAL") else None,
                        width=160,
                        height=50
                    ),
                    ft.TextButton(
                        "CANCELAR", 
                        on_click=lambda _: page.go("/medicao"),
                        # O Flet exige 'style' para cores em botões de texto
                        style=ft.ButtonStyle(color=ft.colors.RED) 
                    )
                ], alignment=ft.MainAxisAlignment.CENTER),
            ], # Fecha Column
            horizontal_alignment=ft.CrossAxisAlignment.CENTER, 
            alignment=ft.MainAxisAlignment.CENTER, 
            expand=True) # Fecha Column
        ] # Fecha controls
    ) # Fecha View