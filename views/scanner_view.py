import flet as ft
import os
import base64
import logging
import asyncio
from datetime import datetime
import cv2
from database.database import Database
import views.styles as st
from utils.updater import AppUpdater

logger = logging.getLogger(__name__)

PASTA_TEMP = os.path.join(os.path.dirname(os.path.dirname(__file__)), "temp")


def montar_tela_scanner(page: ft.Page):
    try:
        if not hasattr(page, "user_data") or page.user_data is None:
            page.user_data = {}

        user_data = page.user_data
        modo = user_data.get("modo_leitura", "AGUA")
        os.makedirs(PASTA_TEMP, exist_ok=True)

        # --- UI ---
        mira_visual = st.criar_mira_scanner()

        img_preview = ft.Image(
            src="", visible=False, width=300, height=200,
            fit="contain", border_radius=10
        )
        lbl_instrucao = ft.Text(
            "Enquadre o QR Code + hidrômetro e toque para capturar",
            size=13, color="grey", text_align=ft.TextAlign.CENTER
        )
        lbl_status = ft.Text(
            "", color="white", weight="bold", size=15,
            text_align=ft.TextAlign.CENTER
        )
        pr_captura = ft.ProgressBar(visible=False, color=st.PRIMARY_BLUE)

        txt_unid = ft.TextField(
            label="Unidade detectada",
            prefix_icon="qr_code_scanner",
            border_radius=10,
            read_only=True,
            bgcolor="#1E2126",
            width=300
        )

        btn_confirmar = ft.ElevatedButton(
            "CONFIRMAR E INSERIR MANUAL",
            icon="edit_note",
            width=300,
            height=55,
            style=st.BTN_MAIN,
            visible=False,
            on_click=lambda e: page.run_task(_confirmar_e_voltar)
        )
        btn_recapturar = ft.TextButton(
            "Capturar novamente",
            icon="replay",
            visible=False,
            on_click=lambda e: page.run_task(_capturar)
        )
        btn_manual = ft.TextButton(
            "Pular scanner e inserir manual",
            icon="keyboard",
            on_click=lambda _: page.go("/medicao")
        )

        state = {"foto_path": None, "unidade": None}

        async def _capturar(e=None):
            lbl_status.value = "Capturando..."
            lbl_status.color = "white"
            pr_captura.visible = True
            img_preview.visible = False
            btn_confirmar.visible = False
            btn_recapturar.visible = False
            txt_unid.value = ""
            page.update()

            try:
                frame = await asyncio.to_thread(_capturar_frame)

                if frame is None:
                    lbl_status.value = "❌ Câmera não disponível. Use o botão manual."
                    lbl_status.color = "red"
                    pr_captura.visible = False
                    page.update()
                    return

                # Salva foto temporária
                ts = datetime.now().strftime('%H%M%S')
                path = os.path.join(PASTA_TEMP, f"scan_{ts}.jpg")
                _, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                with open(path, 'wb') as f:
                    f.write(buf.tobytes())
                state["foto_path"] = path

                # Preview em base64
                img_preview.src_base64 = base64.b64encode(buf.tobytes()).decode()
                img_preview.visible = True

                # Detecta QR na foto
                unidade = _detectar_qr(frame)
                state["unidade"] = unidade

                if unidade:
                    txt_unid.value = unidade
                    lbl_status.value = f"✅ Unidade: {unidade}"
                    lbl_status.color = "green"
                else:
                    txt_unid.value = ""
                    lbl_status.value = "⚠️ QR não detectado — confirme a unidade no próximo passo."
                    lbl_status.color = "orange"

                # Upload para Supabase em background — não bloqueia a UI
                asyncio.create_task(
                    _upload_background(path, unidade or "DESCONHECIDA", modo)
                )

                btn_confirmar.visible = True
                btn_recapturar.visible = True

            except Exception as ex:
                logger.error(f"Erro na captura: {ex}", exc_info=True)
                lbl_status.value = f"❌ Erro: {ex}"
                lbl_status.color = "red"

            pr_captura.visible = False
            page.update()

        async def _upload_background(path: str, unidade: str, modo: str):
            """Envia a foto ao Supabase Storage sem bloquear a UI."""
            try:
                url = await asyncio.to_thread(
                    Database.upload_foto_hidrometro_sync, path, unidade, modo
                )
                if url:
                    logger.info(f"📸 Upload concluído: {url}")
                else:
                    logger.warning("⚠️ Upload da foto não retornou URL.")
            except Exception as ex:
                logger.error(f"Erro no upload em background: {ex}")
            finally:
                try:
                    if os.path.exists(path):
                        os.remove(path)
                except Exception:
                    pass

        async def _confirmar_e_voltar():
            page.user_data["unidade_scanner"] = state.get("unidade") or ""
            page.user_data["valor_scanner"] = ""
            page.go("/medicao")

        container_mira = ft.Container(
            content=ft.Stack([
                mira_visual,
                ft.Container(
                    content=ft.Icon("camera_alt", color="white54", size=36),
                    alignment=ft.alignment.Alignment(0, 0)
                )
            ]),
            alignment=ft.alignment.Alignment(0, 0),
            on_click=lambda e: page.run_task(_capturar),
            ink=True
        )

        cor_appbar = st.PRIMARY_BLUE if modo == "AGUA" else "orange"

        return ft.View(
            route="/scanner",
            bgcolor="#121417",
            appbar=ft.AppBar(
                title=ft.Text(f"Scanner — {'ÁGUA' if modo == 'AGUA' else 'GÁS'}"),
                center_title=True,
                bgcolor=cor_appbar,
                leading=ft.IconButton("arrow_back", on_click=lambda _: page.go("/medicao"))
            ),
            controls=[
                ft.Column([
                    container_mira,
                    pr_captura,
                    lbl_instrucao,
                    lbl_status,
                    ft.Container(height=8),
                    img_preview,
                    txt_unid,
                    ft.Container(height=10),
                    btn_confirmar,
                    btn_recapturar,
                    ft.Divider(color="white10"),
                    btn_manual,
                    ft.Text(AppUpdater.get_footer(), size=10, color="grey40", italic=True)
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                scroll=ft.ScrollMode.ADAPTIVE,
                spacing=8)
            ]
        )

    except Exception as e:
        logger.error(f"Erro ao montar scanner: {e}", exc_info=True)
        return ft.View(
            route="/scanner",
            controls=[ft.Text(f"Erro Crítico no Scanner: {e}", color="red")]
        )


def _capturar_frame():
    """Captura um frame da câmera. Retorna None se câmera não disponível."""
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return None
    for _ in range(5):
        cap.read()
    ret, frame = cap.read()
    cap.release()
    return frame if ret else None


def _detectar_qr(frame) -> str | None:
    """Detecta e decodifica QR Code num frame cv2. Retorna a string ou None."""
    detector = cv2.QRCodeDetector()
    valor, _, _ = detector.detectAndDecode(frame)
    return valor if valor else None
