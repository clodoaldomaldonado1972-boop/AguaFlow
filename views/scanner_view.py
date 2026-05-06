import flet as ft
import os
import base64
import cv2
import numpy as np
import asyncio
from database.database import Database
# Importa a mira e cores do seu styles.py[cite: 5, 6]
import views.styles as st
from utils.updater import AppUpdater


def montar_tela_scanner(page: ft.Page):
    try:
        user_data = getattr(page, "user_data", {}) or {}
        if not hasattr(page, "user_data") or page.user_data is None:
            page.user_data = {}

        # --- 1. CONFIGURAÇÃO DE ÁUDIO (BEEP) - Conforme solicitado ---
        audio_beep = ft.Audio(src="audio/beep.mp3", autoplay=False)
        if audio_beep not in page.overlay:
            page.overlay.append(audio_beep)

        # Elementos de UI
        modo_atual = user_data.get("modo_leitura", "AGUA")
        img_preview = ft.Image(src="", visible=False, width=300)
        lbl_status = ft.Text(
            f"MODO: {modo_atual}", color="white", weight="bold")
        pr_envio = ft.ProgressBar(visible=False, color="blue")

        # --- 2. INTEGRAÇÃO DA MIRA DO STYLES.PY ---
        mira_visual = st.criar_mira_scanner()

        txt_unid = ft.TextField(
            label="Unidade",
            prefix_icon=ft.icons.HOME,
            border_radius=10
        )
        txt_val = ft.TextField(
            label="Valor da Leitura",
            prefix_icon=ft.icons.SPEED,
            border_radius=10
        )

        # Botão de Reportar Problema (inicialmente invisível)
        btn_reportar_problema = ft.ElevatedButton(
            "REPORTAR PROBLEMA",
            icon=ft.icons.BUG_REPORT,
            visible=False,
            width=320,
            style=st.BTN_SPECIAL
        )

        async def capturar_foto(e):
            try:
                # GATILHO SONORO: Executa o beep ao iniciar a captura
                audio_beep.play()
                page.update()
                pr_envio.visible = True
                page.update()

                cap = cv2.VideoCapture(0)
                ret, frame = cap.read()
                cap.release()

                if ret:
                    nova_largura = 640
                    altura, largura = frame.shape[:2]
                    proporcao = nova_largura / float(largura)
                    frame_redim = cv2.resize(
                        frame, (nova_largura, int(altura * proporcao)))

                    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 60]
                    _, buffer = cv2.imencode('.jpg', frame_redim, encode_param)

                    # Caminho temporário multiplataforma
                    temp_dir = page.client_storage.get("temp_path") if hasattr(page, "client_storage") else os.getcwd()
                    if not temp_dir: temp_dir = os.getcwd()
                    
                    path_temp = os.path.join(temp_dir, "temp_leitura.jpg")
                    with open(path_temp, "wb") as f:
                        f.write(buffer)

                    img_preview.src_base64 = base64.b64encode(
                        buffer).decode('utf-8')
                    img_preview.visible = True
                    btn_reportar_problema.visible = False  # Esconde se a captura for bem-sucedida
                    lbl_status.value = "✅ Capturado com sucesso!"
                    page.user_data["path_foto_pendente"] = path_temp

                else:
                    # Erro silencioso: Hardware da câmera não entregou imagem
                    msg_erro = "Câmera ativa mas retornou frame vazio (ret=False)"
                    await Database.registrar_log_erro(
                        erro=msg_erro,
                        contexto="Scanner - Falha cap.read()",
                        usuario=user_data.get("email")
                    )
                    # Configura o botão de reportar problema
                    lbl_status.value = "❌ Erro: Hardware da câmera falhou."
                    btn_reportar_problema.visible = True
                    btn_reportar_problema.on_click = lambda ev: page.run_task(
                        reportar_problema_clique, msg_erro, "Scanner - Falha cap.read()"
                    )

                pr_envio.visible = False
                page.update()
            except Exception as ex:
                # Captura qualquer exceção de software e envia log
                # Podemos capturar uma screenshot da UI do Flet mesmo que o cv2 não tenha conseguido um frame.
                await Database.registrar_log_erro(
                    erro=ex,
                    contexto="Scanner - Exception Crítica",
                    usuario=user_data.get("email")
                )
                # Configura o botão de reportar problema
                lbl_status.value = f"Erro na captura: {str(ex)}"
                btn_reportar_problema.visible = True
                btn_reportar_problema.on_click = lambda ev: page.run_task(
                    reportar_problema_clique, str(
                        ex), "Scanner - Exception Crítica"
                )

                # Garante que o botão esteja visível e a página atualizada
                lbl_status.value = f"Erro na captura: {str(ex)}"
                pr_envio.visible = False
                page.update()

        async def reportar_problema_clique(erro_msg, contexto):
            """Handler para o botão 'Reportar Problema'."""
            btn_reportar_problema.disabled = True
            btn_reportar_problema.text = "ENVIANDO..."
            page.update()

            screenshot_url = None
            try:
                # Captura a screenshot da UI atual do Flet
                screenshot_bytes = await page.export_image_async()
                if screenshot_bytes:
                    screenshot_url = await Database.upload_screenshot_to_storage(
                        screenshot_bytes, f"scanner_error_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg", user_data.get(
                            "email")
                    )
            except Exception as e:
                logger.error(
                    f"Falha ao capturar ou fazer upload da screenshot: {e}")

            await Database.registrar_log_erro(erro_msg, contexto, user_data.get("email"), screenshot_url)

            page.snack_bar = ft.SnackBar(
                ft.Text("✅ Problema reportado com sucesso!"),
                bgcolor=st.SUCCESS_GREEN
            )
            page.snack_bar.open = True
            btn_reportar_problema.visible = False  # Esconde após reportar
            btn_reportar_problema.disabled = False
            btn_reportar_problema.text = "REPORTAR PROBLEMA"
            page.update()

        async def ir_para_manual(e):
            """Redireciona para medição limpando dados temporários do scanner para entrada manual."""
            user_data = getattr(page, "user_data", {})
            user_data.pop("unidade_scanner", None)
            user_data.pop("valor_scanner", None)
            page.go("/medicao")

        async def fechar_e_voltar(e):
            if not txt_val.value:
                page.snack_bar = ft.SnackBar(
                    ft.Text("Por favor, insira o valor manualmente."))
                page.snack_bar.open = True
                page.update()
                return

            page.user_data["unidade_scanner"] = txt_unid.value
            page.user_data["valor_scanner"] = txt_val.value
            page.go("/medicao")

        return ft.View(
            route="/scanner",
            bgcolor="#121417",
            appbar=ft.AppBar(
                title=ft.Text("Scanner AguaFlow"),
                center_title=True,
                leading=ft.IconButton(ft.icons.ARROW_BACK,
                                      on_click=lambda _: page.go("/medicao"))),
            controls=[
                ft.Column([
                    ft.Container(
                        content=mira_visual,
                        alignment=ft.alignment.center,
                        on_click=capturar_foto
                    ),
                    img_preview,
                    pr_envio,
                    ft.Text("Toque na mira para capturar",
                            size=14, color="grey"),
                    lbl_status,
                    ft.Container(height=10),
                    txt_unid,
                    txt_val,
                    ft.Container(height=20),
                    ft.Row([
                        btn_reportar_problema,  # Adiciona o botão de reportar
                        ft.ElevatedButton(
                            "CONFIRMAR",
                            icon=ft.icons.CHECK,
                            on_click=fechar_e_voltar,
                            width=160,
                            height=50
                        ),
                        ft.ElevatedButton(
                            "MANUAL",
                            icon=ft.icons.KEYBOARD,
                            on_click=ir_para_manual,
                            width=140,
                            height=50,
                            style=ft.ButtonStyle(
                                color="white", bgcolor="orange")
                        )
                    ], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Divider(color="white10"),
                    ft.Text(AppUpdater.get_footer(), size=11,
                            color="grey", italic=True)
                ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    scroll=ft.ScrollMode.ADAPTIVE)
            ]
        )
    except Exception as e:
        return ft.View("/scanner", [ft.Text(f"Erro Crítico no Scanner: {e}", color="red")])
