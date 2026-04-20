import flet as ft
import os
from views import styles as st

# Importação robusta do motor de QR Codes (localizado em utils/gerador_qr.py)
try:
    from utils.gerador_qr import gerar_qr_codes
except ImportError:
    try:
        from gerador_qr import gerar_qr_codes
    except ImportError:
        gerar_qr_codes = None

def montar_tela_qrcodes(page: ft.Page, voltar):
    """
    Interface para geração de etiquetas QR Code.
    Sincronizada com o motor de PDF do Edifício Vivere.
    """
    
    txt_unidade = ft.TextField(
        label="Unidade específica",
        hint_text="Ex: 101 (Deixe vazio para todos)",
        width=300,
        border_radius=10,
        bgcolor=ft.colors.with_opacity(0.1, st.WHITE),
        color=st.WHITE,
        focused_border_color=st.PRIMARY_BLUE
    )

    def disparar_geracao(tipo):
        if not gerar_qr_codes:
            page.snack_bar = ft.SnackBar(ft.Text("❌ Erro: Motor gerador_qr não localizado."), bgcolor=st.ERROR_COLOR)
            page.snack_bar.open = True
            page.update()
            return

        txt_unidade.disabled = True
        page.snack_bar = ft.SnackBar(ft.Text(f"⏳ Gerando etiquetas de {tipo}..."), bgcolor=st.PRIMARY_BLUE)
        page.snack_bar.open = True
        page.update()

        try:
            unid = txt_unidade.value.strip() if txt_unidade.value else None
            
            # Chama o motor que gera o PDF em C:/AguaFlow/storage
            caminho_pdf = gerar_qr_codes(filtro_tipo=tipo, unidade_alvo=unid)

            if caminho_pdf:
                page.snack_bar = ft.SnackBar(ft.Text(f"✅ Sucesso! PDF salvo em: {caminho_pdf}"), bgcolor=st.SUCCESS_GREEN)
            else:
                page.snack_bar = ft.SnackBar(ft.Text("⚠️ Nenhum medidor encontrado para este filtro."), bgcolor=st.ACCENT_ORANGE)
        
        except Exception as e:
            print(f"Erro na geração: {e}")
            page.snack_bar = ft.SnackBar(ft.Text(f"❌ Erro ao gerar PDF: {str(e)}"), bgcolor=st.ERROR_COLOR)
        
        finally:
            try:
                txt_unidade.disabled = False
                page.snack_bar.open = True
                page.update()
            except RuntimeError:
                pass # Proteção contra 'Event loop is closed'

    # --- DEFINIÇÃO DA VIEW ---
    return ft.View(
        route="/qrcodes",
        bgcolor=st.BG_DARK,
        appbar=ft.AppBar(
            title=ft.Text("Gerador de Etiquetas (4x4)", color=st.WHITE),
            leading=ft.IconButton(ft.icons.ARROW_BACK, icon_color=st.WHITE, on_click=voltar),
            bgcolor=ft.colors.SURFACE_VARIANT,
            center_title=True
        ),
        vertical_alignment="center",
        horizontal_alignment="center",
        controls=[
            ft.Column([
                ft.Icon(ft.icons.QR_CODE_2, size=100, color=st.PRIMARY_BLUE),
                ft.Text("Vivere Prudente", size=25, weight="bold", color=st.WHITE),
                ft.Text("Identificação Física de Hidrómetros", color=st.GREY),
                
                ft.Container(height=20),
                txt_unidade,
                ft.Container(height=10),
                
                ft.Row([
                    ft.ElevatedButton(
                        "APENAS ÁGUA", 
                        icon=ft.icons.WATER_DROP,
                        on_click=lambda _: disparar_geracao("Água"),
                        style=ft.ButtonStyle(color=st.WHITE, bgcolor=ft.colors.BLUE_800)
                    ),
                    ft.ElevatedButton(
                        "APENAS GÁS", 
                        icon=ft.icons.LOCAL_GAS_STATION,
                        on_click=lambda _: disparar_geracao("Gás"),
                        style=ft.ButtonStyle(color=st.WHITE, bgcolor=ft.colors.ORANGE_800)
                    ),
                ], alignment="center"),
                
                ft.Container(height=10),
                
                ft.ElevatedButton(
                    "GERAR PDF COMPLETO", 
                    width=300, 
                    height=50,
                    icon=ft.icons.PICTURE_AS_PDF,
                    bgcolor=st.SUCCESS_GREEN, 
                    color=st.WHITE,
                    on_click=lambda _: disparar_geracao("AMBOS")
                ),
                
                ft.Container(height=20),
                ft.Text("Os ficheiros serão salvos na pasta /storage", size=10, color=st.GREY)
            ], horizontal_alignment="center")
        ]
    )