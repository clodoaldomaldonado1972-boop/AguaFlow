import flet as ft
import os

# Importação robusta do motor de QR Codes
try:
    from utils.gerador_qr import gerar_qr_codes
except ImportError:
    gerar_qr_codes = None

def montar_tela_qrcodes(page: ft.Page, voltar):
    txt_unidade = ft.TextField(
        label="Unidade específica",
        hint_text="Ex: 101 (Deixe vazio para todos)",
        width=300,
        border_radius=10,
        bgcolor="white10"
    )

    def disparar_geracao(tipo):
        if not gerar_qr_codes:
            page.snack_bar = ft.SnackBar(ft.Text("Erro: Motor não carregado"), bgcolor="red", open=True)
            page.update()
            return

        txt_unidade.disabled = True
        page.snack_bar = ft.SnackBar(ft.Text(f"Gerando etiquetas de {tipo}..."), bgcolor="blue", open=True)
        page.update()

        try:
            unid = txt_unidade.value.strip() if txt_unidade.value else None
            
            # O motor deve estar configurado para 40mm x 40mm no arquivo utils/gerador_qr.py
            caminho_pdf = gerar_qr_codes(filtro_tipo=tipo, unidade_alvo=unid)

            if caminho_pdf:
                page.snack_bar = ft.SnackBar(
                    ft.Text(f"Sucesso! Salvo em: {caminho_pdf}"), 
                    bgcolor="#2E7D32", 
                    open=True
                )
                # Tenta abrir o PDF automaticamente no Windows
                try:
                    os.startfile(caminho_pdf)
                except:
                    pass
            else:
                page.snack_bar = ft.SnackBar(ft.Text("Erro ao gerar PDF."), bgcolor="red", open=True)
        
        except RuntimeError as e:
            if "Event loop is closed" in str(e):
                return # Proteção contra fechamento da janela
        
        finally:
            try:
                txt_unidade.disabled = False
                page.update()
            except:
                pass

    return ft.View(
        route="/qrcodes",
        appbar=ft.AppBar(
            title=ft.Text("Gerador de Etiquetas (4x4)"),
            leading=ft.IconButton(ft.icons.ARROW_BACK, on_click=voltar),
            bgcolor="blue"
        ),
        vertical_alignment="center",
        horizontal_alignment="center",
        controls=[
            ft.Column([
                ft.Icon(ft.icons.QR_CODE_2, size=100, color="blue"),
                ft.Text("Vivere Prudente", size=25, weight="bold"),
                txt_unidade,
                ft.Row([
                    ft.ElevatedButton("ÁGUA", on_click=lambda _: disparar_geracao("Água")),
                    ft.ElevatedButton("GÁS", on_click=lambda _: disparar_geracao("Gás")),
                ], alignment="center"),
                ft.ElevatedButton(
                    "GERAR COMPLETO", 
                    width=300, 
                    bgcolor="green", 
                    color="white",
                    on_click=lambda _: disparar_geracao("AMBOS")
                )
            ], horizontal_alignment="center", spacing=20)
        ]
    )