import flet as ft
import os
import base64
import logging
import asyncio
import traceback
from datetime import datetime
from database.database import Database
import views.styles as st
from utils.updater import AppUpdater
from utils.vision import processar_foto_hidrometro
from utils.platform_utils import get_temp_dir
from utils.logger_config import enviar_report_erro

logger = logging.getLogger(__name__)


def montar_tela_scanner(page: ft.Page):
    try:
        if not hasattr(page, "user_data") or page.user_data is None:
            page.user_data = {}

        user_data = page.user_data
        modo = user_data.get("modo_leitura", "AGUA")
        pasta_temp = get_temp_dir()

        # --- UI ---
        mira_visual = st.criar_mira_scanner(page)

        img_preview = ft.Image(
            src="", visible=False, width=300, height=200,
            fit="contain", border_radius=10
        )

        lbl_unidade = ft.Text(
            "Unidade: —",
            size=13, color="grey70", weight="bold",
            text_align=ft.TextAlign.CENTER,
        )
        lbl_instrucao = ft.Text(
            "1. Escaneie o código da unidade   2. Fotografe o medidor",
            size=12, color="grey", text_align=ft.TextAlign.CENTER
        )
        lbl_status = ft.Text(
            "", color="white", weight="bold", size=15,
            text_align=ft.TextAlign.CENTER
        )
        pr_captura = ft.ProgressRing(visible=False, color=st.PRIMARY_BLUE)

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

        # Serviços inicializados no startup (main.py)
        file_picker = getattr(page, 'file_picker', None)
        if file_picker is None:
            file_picker = ft.FilePicker()
            page.services = list(page.services) + [file_picker]
            page.update()

        # CameraService e BarcodeScannerService — disponíveis após build com Flutter extensions
        camera_service = getattr(page, 'camera', None)
        barcode_service = getattr(page, 'barcode', None)
        if camera_service is None:
            logger.warning("⚠️ CameraService não encontrado.")
        if barcode_service is None:
            logger.warning("⚠️ BarcodeScannerService não encontrado.")

        # Flash visual de captura — overlay branco que aparece e some em 300ms
        flash_overlay = ft.Container(
            width=300, height=240,
            bgcolor="white",
            opacity=0,
            animate_opacity=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
            border_radius=20,
        )

        async def _processar_foto(path: str):
            """Processa de forma leve a imagem retornada pela câmera nativa do Android."""
            import socket
            state["foto_path"] = path
            existe = os.path.exists(path) if path else False
            tamanho = os.path.getsize(path) if existe else 0
            logger.info(f"📷 Foto recebida: path={path} | existe={existe} | tamanho={tamanho}B")

            # Flash visual não-bloqueante (não suspende o handler)
            async def _restaurar_flash():
                await asyncio.sleep(0.3)
                try:
                    flash_overlay.opacity = 0
                    page.update()
                except Exception:
                    pass
            flash_overlay.opacity = 0.85
            page.update()
            asyncio.create_task(_restaurar_flash())

            # Atualização do Preview local em base64
            try:
                with open(path, "rb") as f:
                    img_preview.src_base64 = base64.b64encode(f.read()).decode()
                img_preview.visible = True
            except Exception as ex:
                logger.error(f"Erro ao gerar preview base64: {ex}")
                img_preview.visible = False

            lbl_status.value = "Verificando conexão..."
            lbl_status.color = "orange"
            page.update()

            # Verificação rápida de conectividade (2 s) — evita aguardar 25 s de timeout
            def _tem_internet() -> bool:
                try:
                    socket.create_connection(("8.8.8.8", 53), timeout=2).close()
                    return True
                except Exception:
                    return False

            tem_internet = await asyncio.to_thread(_tem_internet)

            valor_ocr = None
            ocr_status = "offline"

            if not tem_internet:
                logger.info("📶 Sem internet — OCR ignorado.")
                lbl_status.value = "📶 Sem conexão — insira o valor manualmente."
                lbl_status.color = "red"
                page.update()
            else:
                lbl_status.value = "Imagem obtida! Processando análise inteligente..."
                lbl_status.color = "orange"
                page.update()

                tipo_str = "gás" if modo == "GAS" else "água"
                try:
                    _, valor_ocr, ocr_status = await asyncio.wait_for(
                        asyncio.to_thread(processar_foto_hidrometro, path, tipo_str),
                        timeout=25.0
                    )
                except asyncio.TimeoutError:
                    logger.warning("⏱️ OCR timeout (25s) — zona de sombra ou API lenta.")
                    ocr_status = "offline"
                except Exception as ex:
                    logger.error(f"Erro no OCR: {ex}")
                    ocr_status = "erro"

            # Normaliza nome da unidade para pasta no Storage
            # "AGUAFLOW|163/164-GAS" → "163-164" | "AGUAFLOW|161-AGUA" → "161"
            unidade_raw = state.get("unidade") or "DESCONHECIDA"
            if '|' in unidade_raw:
                unidade_raw = unidade_raw.split('|', 1)[1]
            if '-' in unidade_raw and unidade_raw.rsplit('-', 1)[1].upper() in ('AGUA', 'GAS'):
                unidade_raw = unidade_raw.rsplit('-', 1)[0]
            unidade_upload = unidade_raw.replace('/', '-')
            asyncio.create_task(_upload_background(path, unidade_upload, modo))

            pr_captura.visible = False

            if valor_ocr:
                lbl_status.value = f"✅ OCR detectou: {valor_ocr} — voltando..."
                lbl_status.color = "green"
            elif ocr_status == "offline":
                lbl_status.value = "📶 Sem conexão — insira o valor manualmente."
                lbl_status.color = "red"
            else:
                lbl_status.value = "⚠️ OCR sem resultado — insira o valor manualmente."
                lbl_status.color = "orange"

            # Passa valores e status para medicao, navega imediatamente
            page.user_data["valor_scanner"] = valor_ocr or ""
            page.user_data["unidade_scanner"] = state.get("unidade") or ""
            page.user_data["ocr_status_scanner"] = ocr_status
            logger.info(f"📋 Scanner → medição: unidade={state.get('unidade')} valor={valor_ocr} status={ocr_status}")
            page.update()
            page.go("/medicao")


        async def _capturar_com_camera():
            """Abre a câmera nativa via CameraService (Flutter extension)."""
            path = await camera_service.pick_image_from_camera()
            return path

        async def _capturar_da_galeria():
            """Abre a galeria via CameraService ou FilePicker como fallback."""
            if camera_service:
                return await camera_service.pick_image_from_gallery()
            files = await file_picker.pick_files(
                dialog_title="Selecione a foto do medidor",
                file_type=ft.FilePickerFileType.IMAGE,
                allow_multiple=False,
            )
            return files[0].path if files and files[0].path else None

        async def _iniciar_captura(source: str = "camera", e=None):
            lbl_status.value = "A abrir câmera..." if source == "camera" else "A abrir galeria..."
            lbl_status.color = "white"
            pr_captura.visible = True
            img_preview.visible = False
            btn_recapturar.visible = False
            page.update()

            try:
                if source == "camera" and camera_service:
                    path = await _capturar_com_camera()
                elif source == "camera" and not camera_service:
                    # CameraService não disponível: desce para galeria automaticamente
                    logger.warning("CameraService ausente — abrindo galeria como fallback.")
                    lbl_status.value = "Câmera nativa indisponível. Abrindo galeria..."
                    page.update()
                    path = await _capturar_da_galeria()
                else:
                    path = await _capturar_da_galeria()

                if path:
                    await _processar_foto(path)
                else:
                    logger.info(f"Captura retornou None (source={source}) — câmera fechada ou permissão negada.")
                    lbl_status.value = "Captura cancelada."
                    pr_captura.visible = False
                    page.update()
            except RuntimeError as ex:
                # Erro retornado pelo Dart (ex: permissão negada, câmera indisponível)
                logger.error(f"Erro na câmera (Dart): {ex}")
                enviar_report_erro(f"Erro câmera Dart:\n{ex}", unidade=f"SCANNER-{modo}")
                lbl_status.value = f"Erro câmera: {ex}"
                lbl_status.color = "red"
                pr_captura.visible = False
                page.update()
            except Exception as ex:
                logger.error(f"Erro ao capturar imagem: {ex}", exc_info=True)
                enviar_report_erro(traceback.format_exc(), unidade=f"SCANNER-{modo}")
                lbl_status.value = f"Erro ao abrir câmera: {type(ex).__name__}"
                lbl_status.color = "red"
                pr_captura.visible = False
                page.update()

        async def _escanear_unidade(e=None):
            """Abre o scanner de QR/barcode para identificar a unidade."""
            if not barcode_service:
                lbl_unidade.value = "Scanner de código indisponível neste build."
                lbl_unidade.color = "red"
                page.update()
                return
            lbl_status.value = "Abrindo scanner de código..."
            lbl_status.color = "white"
            page.update()
            try:
                codigo = await barcode_service.scan_barcode()
                if codigo:
                    state["unidade"] = codigo
                    # Normaliza o display: "AGUAFLOW|161-AGUA" → "161"
                    display = codigo
                    if '|' in display:
                        display = display.split('|', 1)[1]
                    if '-' in display:
                        display = display.rsplit('-', 1)[0]
                    lbl_unidade.value = f"Unidade: {display}"
                    lbl_unidade.color = "green"
                    lbl_status.value = "Código detectado! Agora fotografe o medidor."
                    lbl_status.color = "white70"
                else:
                    lbl_status.value = "Escaneamento cancelado."
                    lbl_status.color = "grey"
            except RuntimeError as ex:
                logger.error(f"Erro no barcode (Dart): {ex}")
                lbl_status.value = f"Erro scanner: {ex}"
                lbl_status.color = "red"
            except Exception as ex:
                logger.error(f"Erro ao escanear barcode: {ex}", exc_info=True)
                lbl_status.value = "Erro ao abrir scanner de código."
                lbl_status.color = "red"
            page.update()

        async def _upload_background(path: str, unidade: str, modo: str):
            upload_ok = False
            try:
                url = await asyncio.to_thread(
                    Database.upload_foto_hidrometro_sync, path, unidade, modo
                )
                if url:
                    logger.info(f"📸 Upload concluído: {url}")
                    page.user_data["foto_url_scanner"] = url
                    upload_ok = True
                    # Notifica o usuário — task em background, usuário já em /medicao
                    try:
                        page.snack_bar = ft.SnackBar(
                            content=ft.Row([
                                ft.Icon(ft.Icons.CHECK_CIRCLE, color="white", size=18),
                                ft.Text("  Foto gravada com sucesso!", color="white", size=14),
                            ]),
                            bgcolor="#2e7d32",
                            duration=3000,
                        )
                        page.snack_bar.open = True
                        page.update()
                    except Exception:
                        pass
                else:
                    logger.warning("📸 Upload retornou URL vazia — foto não gravada no Storage.")
                    try:
                        page.snack_bar = ft.SnackBar(
                            content=ft.Text("Falha ao enviar foto. Tente novamente.", color="white", size=14),
                            bgcolor="#b71c1c",
                            duration=4000,
                        )
                        page.snack_bar.open = True
                        page.update()
                    except Exception:
                        pass
            except Exception as ex:
                logger.error(f"Erro no upload em background: {ex}", exc_info=True)
                enviar_report_erro(traceback.format_exc(), unidade=f"UPLOAD-FOTO-{modo}")
            finally:
                # Só deleta o arquivo local se o upload foi bem-sucedido.
                # Se falhou, mantém o arquivo para retentativa futura.
                if upload_ok:
                    try:
                        if os.path.exists(path):
                            os.remove(path)
                    except Exception:
                        pass

        container_mira = ft.Container(
            content=ft.Stack([
                mira_visual,
                # Ícone centralizado sobre o box de 220px
                ft.Container(
                    content=ft.Icon(ft.Icons.PHOTO_CAMERA, color="white54", size=36),
                    alignment=ft.alignment.Alignment(0, 0),
                    width=300, height=240,
                ),
                flash_overlay,
            ]),
            alignment=ft.alignment.Alignment(0, 0),
            width=300, height=240,
        )

        btn_camera = ft.ElevatedButton(
            "Fotografar Medidor",
            icon=ft.Icons.PHOTO_CAMERA,
            width=300,
            height=55,
            style=ft.ButtonStyle(
                bgcolor=st.PRIMARY_BLUE if modo == "AGUA" else "orange",
                color="white",
                shape=ft.RoundedRectangleBorder(radius=10),
            ),
            on_click=lambda e: page.run_task(_iniciar_captura, "camera"),
        )
        btn_galeria = ft.TextButton(
            "Escolher da galeria",
            icon=ft.Icons.PHOTO_LIBRARY_OUTLINED,
            on_click=lambda e: page.run_task(_iniciar_captura, "galeria"),
        )

        btn_scan_unidade = ft.ElevatedButton(
            "Escanear Código da Unidade",
            icon=ft.Icons.QR_CODE_SCANNER,
            width=300,
            height=48,
            style=ft.ButtonStyle(
                bgcolor="#2E3440",
                color="white",
                shape=ft.RoundedRectangleBorder(radius=10),
            ),
            on_click=lambda e: page.run_task(_escanear_unidade),
            visible=barcode_service is not None,
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
                    lbl_unidade,
                    btn_scan_unidade,
                    ft.Divider(color="white10", height=1),
                    btn_camera,
                    btn_galeria,
                    pr_captura,
                    lbl_instrucao,
                    lbl_status,
                    ft.Container(height=8),
                    img_preview,
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