import flet as ft
import os
import base64
import cv2 
import numpy as np
# Importação da automação de versão centralizada
from utils.updater import AppUpdater

def montar_tela_scanner(page: ft.Page):
    if not page.user_data:
        page.user_data = {}
        
    # Elementos de UI
    modo_atual = page.user_data.get("modo_leitura", "AGUA")
    img_preview = ft.Image(src="", visible=False, width=300)
    lbl_status = ft.Text(f"MODO: {modo_atual}", color="white", weight="bold")
    pr_envio = ft.ProgressBar(visible=False, color="blue")
    
    # CORREÇÃO: Removido prefix_icon_color e usado ft.Icon dentro de prefix_icon[cite: 1, 3]
    txt_unid = ft.TextField(
        label="Unidade", 
        prefix_icon=ft.Icon(ft.icons.HOME, color="blue"),
        border_radius=10
    )
    txt_val = ft.TextField(
        label="Valor da Leitura", 
        prefix_icon=ft.Icon(ft.icons.SPEED, color="blue"),
        border_radius=10
    )

    async def capturar_foto(e):
        try:
            pr_envio.visible = True
            page.update()

            cap = cv2.VideoCapture(0)
            ret, frame = cap.read()
            cap.release()

            if ret:
                # Otimização para o Supabase: 640px e 60% de qualidade[cite: 3, 6]
                nova_largura = 640
                altura, largura = frame.shape[:2]
                proporcao = nova_largura / float(largura)
                frame_redim = cv2.resize(frame, (nova_largura, int(altura * proporcao)))

                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 60]
                _, buffer = cv2.imencode('.jpg', frame_redim, encode_param)
                
                path_temp = os.path.join(os.getcwd(), "temp_leitura.jpg")
                with open(path_temp, "wb") as f:
                    f.write(buffer)
                
                img_preview.src_base64 = base64.b64encode(buffer).decode('utf-8')
                img_preview.visible = True
                lbl_status.value = "✅ Foto capturada! Processando..."
                page.user_data["path_foto_pendente"] = path_temp 
            
            pr_envio.visible = False
            page.update()
        except Exception as ex:
            lbl_status.value = f"Erro na captura: {str(ex)}"
            pr_envio.visible = False
            page.update()

    async def fechar_e_voltar(e):
        if not txt_val.value:
            page.snack_bar = ft.SnackBar(ft.Text("Por favor, insira o valor manualmente."))
            page.snack_bar.open = True
            page.update()
            return
            
        page.user_data["unidade_scanner"] = txt_unid.value
        page.user_data["valor_scanner"] = txt_val.value
        page.go("/medicao")

    return ft.View(
        route="/scanner",
        bgcolor="#121417", # Cor escura padrão para o Residencial Vivere[cite: 3, 5]
        appbar=ft.AppBar(
            title=ft.Text("Scanner AguaFlow"), 
            center_title=True,
            leading=ft.IconButton(ft.icons.ARROW_BACK, on_click=lambda _: page.go("/medicao"))
        ),
        controls=[
            ft.Column([
                ft.Container(
                    content=ft.Stack([
                        ft.Icon(ft.icons.CAMERA_REAR, size=120, color="grey"), 
                        ft.Icon(ft.icons.CROP_FREE, size=150, color="blue", opacity=0.3),
                    ]),
                    alignment=ft.alignment.center, # Alinhamento robusto
                    on_click=capturar_foto
                ),
                img_preview,
                pr_envio,
                ft.Text("Toque no ícone para capturar", size=14, color="grey"),
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
                        width=160,
                        height=50
                    ),
                    ft.TextButton(
                        "CANCELAR", 
                        on_click=lambda _: page.go("/medicao"),
                        style=ft.ButtonStyle(color="red") # Uso de string evita crash de modulo[cite: 3]
                    )
                ], alignment=ft.MainAxisAlignment.CENTER),
                
                # RODAPÉ DE VERSÃO AUTOMÁTICO
                # Adicione ao final da coluna principal de cada tela:
                ft.Divider(color="white10"),
                ft.Text(
                    AppUpdater.get_footer(), 
                    size=11, 
                    color="grey", 
                    italic=True
                )
            ], 
            horizontal_alignment=ft.CrossAxisAlignment.CENTER, 
            alignment=ft.MainAxisAlignment.CENTER, 
            scroll=ft.ScrollMode.ADAPTIVE)
        ]
    )