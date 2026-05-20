import flet as ft
import os
import base64
import logging
import asyncio
from datetime import datetime
from database.database import Database
import views.styles as st
from utils.updater import AppUpdater
from utils.vision import processar_foto_hidrometro
from utils.platform_utils import get_temp_dir

logger = logging.getLogger(__name__)


def montar_tela_scanner(page: ft.Page):
    try:
        if not hasattr(page, "user_data") or page.user_data is None:
            page.user_data = {}

        user_data = page.user_data
        modo = user_data.get("modo_leitura", "AGUA")
        pasta_temp = get_temp_dir()

        # --- UI ---
        mira_visual = st.criar_mira_scanner()

        img_preview = ft.Image(
            src="", visible=False, width=300, height=200,
            fit="contain", border_radius=10
        )
        lbl_instrucao = ft.Text(
            "Toque para abrir a câmera ou galeria do dispositivo",
            size=13, color="grey", text_align=ft.TextAlign.CENTER
        )
        lbl_status = ft.Text(
            "", color="white", weight="bold", size=15,
            text_align=ft.TextAlign.CENTER
        )
        pr_captura = ft.ProgressRing(visible=False, color=st.PRIMARY_BLUE)

        txt_unid = ft.TextField(
            label="Unidade detectada",
            prefix_icon="qr_code_scanner",
            border_radius=10,
            read_only=True,
            bgcolor="#1E2126",
            width=300
        )
        txt_valor_ocr = ft.TextField(
            label="Leitura OCR (confirme ou corrija)",
            prefix_icon="straighten",
            border_radius=10,
            bgcolor="#1E2126",
            width=300,
            visible=False,
            hint_text="ex: 00542.30",
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        lbl_ocr_status = ft.Text("", size=11, color="grey", italic=True)

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
            on_click=lambda e: page.run_task(_iniciar_captura)
        )
        btn_manual = ft.TextButton(
            "Pular scanner e inserir manual",
            icon="keyboard",
            on_click=lambda _: page.go("/medicao")
        )

        state = {"foto_path": None, "unidade": None}

        # FilePicker funciona em Android e Desktop no Flet 0.82.2 (retorna arquivos via await)
        file_picker = next((s for s in page.services if isinstance(s, ft.FilePicker)), None)
        if file_picker is None:
            file_picker = ft.FilePicker()
            page.services = list(page.services) + [file_picker]
            page.update()

        # Beep de captura
        audio_beep = None
        try:
            if hasattr(ft, 'Audio'):
                audio_beep = ft.Audio(src="assets/beep.mp3", autoplay=False)
                page.overlay.append(audio_beep)
                page.update()
        except Exception as ex:
            logger.warning(f"Áudio de beep não disponível: {ex}")

        async def _processar_foto(path: str):
            """Processa de forma leve a imagem retornada pela câmera nativa do Android."""
            state["foto_path"] = path

            if audio_beep:
                try:
                    audio_beep.play()
                except Exception:
                    pass

            # Atualização do Preview local em base64
            try:
                with open(path, "rb") as f:
                    img_preview.src_base64 = base64.b64encode(f.read()).decode()
                img_preview.visible = True
            except Exception as ex:
                logger.error(f"Erro ao gerar preview base64: {ex}")
                img_preview.visible = False

            state["unidade"] = None
            txt_unid.value = ""
            lbl_status.value = "Imagem obtida! Processando análise inteligente..."
            lbl_status.color = "orange"
            page.update()

            # OCR com timeout estrito — evita travamento em zonas de sombra (4.C)
            tipo_str = "gás" if modo == "GAS" else "água"
            valor_ocr = None
            ocr_status = "offline"
            try:
                _, valor_ocr, ocr_status = await asyncio.wait_for(
                    asyncio.to_thread(processar_foto_hidrometro, path, tipo_str),
                    timeout=25.0
                )
            except asyncio.TimeoutError:
                logger.warning("⏱️ OCR timeout (25s) — zona de sombra ou API lenta.")
            except Exception as ex:
                logger.error(f"Erro no OCR: {ex}")

            txt_valor_ocr.visible = True
            if valor_ocr:
                txt_valor_ocr.value = valor_ocr
                txt_valor_ocr.helper_text = None
                lbl_ocr_status.value = f"OCR Inteligente detectou: {valor_ocr}"
                lbl_ocr_status.color = "green600"
            else:
                # Fallback manual obrigatório (5.2) — abre teclado e orienta o operador
                txt_valor_ocr.value = ""
                txt_valor_ocr.helper_text = "Sem sinal ou falha no OCR. Insira o valor manualmente."
                lbl_ocr_status.value = "⚠️ Insira o valor do medidor no campo acima."
                lbl_ocr_status.color = "orange"
                txt_valor_ocr.focus()

            lbl_status.value = "Análise concluída. Por favor, valide os campos."
            lbl_status.color = "white"

            # Envia o upload assíncrono para o Supabase
            asyncio.create_task(_upload_background(path, "DESCONHECIDA", modo))
            
            btn_confirmar.visible = True
            btn_recapturar.visible = True
            pr_captura.visible = False
            page.update()


        async def _iniciar_captura(e=None):
            lbl_status.value = "A abrir câmera/galeria..."
            lbl_status.color = "white"
            pr_captura.visible = True
            img_preview.visible = False
            btn_confirmar.visible = False
            btn_recapturar.visible = False
            txt_unid.value = ""
            txt_valor_ocr.value = ""
            txt_valor_ocr.visible = False
            lbl_ocr_status.value = ""
            page.update()

            try:
                # Flet 0.82.2: pick_files é async e retorna a lista de arquivos diretamente
                files = await file_picker.pick_files(
                    dialog_title="Fotografe o medidor",
                    file_type=ft.FilePickerFileType.IMAGE,
                    allow_multiple=False,
                )
                if files and files[0].path:
                    await _processar_foto(files[0].path)
                else:
                    lbl_status.value = "Captura cancelada."
                    pr_captura.visible = False
                    page.update()
            except Exception as ex:
                logger.error(f"Erro ao abrir FilePicker: {ex}")
                lbl_status.value = "Erro ao abrir câmera. Tente novamente."
                pr_captura.visible = False
                page.update()

        async def _upload_background(path: str, unidade: str, modo: str):
            try:
                url = await asyncio.to_thread(
                    Database.upload_foto_hidrometro_sync, path, unidade, modo
                )
                if url:
                    logger.info(f"📸 Sincronização concluída: {url}")
                    page.user_data["foto_url_scanner"] = url
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
            page.user_data["valor_scanner"] = txt_valor_ocr.value or ""
            await page.push_route("/medicao")

        container_mira = ft.Container(
            content=ft.Stack([
                mira_visual,
                ft.Container(
                    content=ft.Icon(ft.Icons.PHOTO_CAMERA, color="white54", size=36),
                    alignment=ft.alignment.Alignment(0, 0),
                    width=300, height=300
                )
            ]),
            alignment=ft.alignment.Alignment(0, 0),
            width=300, height=300,
            on_click=lambda e: page.run_task(_iniciar_captura),
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
                leading=ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    on_click=lambda _: page.go("/medicao")
                )
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
                    txt_valor_ocr,
                    lbl_ocr_status,
                    ft.Container(height=10),
                    btn_confirmar,
                    btn_recapturar,
                    ft.Divider(color="white10"),
                    btn_manual,
                    ft.Text(AppUpdater.get_footer(), size=10, color="grey40", italic=True)
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                scroll=ft.ScrollMode.AUTO,
                spacing=8,
                expand=True)
            ]
        )

    except Exception as e:
        logger.error(f"Erro ao montar scanner: {e}", exc_info=True)
        return ft.View(
            route="/scanner",
            controls=[ft.Text(f"Erro Crítico no Scanner: {e}", color="red")]
        )