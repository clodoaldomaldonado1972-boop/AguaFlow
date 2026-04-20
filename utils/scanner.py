import flet as ft
import asyncio
import os
from utils.leitor_ocr import processar_leitura_completa

class ScannerAguaFlow:
    def __init__(self, page: ft.Page, ao_detectar_leitura):
        self.page = page
        self.ao_detectar_leitura = ao_detectar_leitura
        self.tipo_leitura = "Água"
        self.picker = ft.FilePicker(on_result=self._processar_resultado)
        
        if self.picker not in self.page.overlay:
            self.page.overlay.append(self.picker)
        
        self.page.update()

    async def iniciar_scan(self, tipo="Água"):
        self.tipo_leitura = tipo
        try:
            # CORREÇÃO: pick_files não deve ser awaitado aqui para evitar crash
            self.picker.pick_files(
                allow_multiple=False,
                file_type=ft.FilePickerFileType.IMAGE
            )
        except Exception as e:
            print(f"Erro na interface de captura: {e}")

    async def _processar_resultado(self, e: ft.FilePickerResultEvent):
        if not e.files or e.files[0].path is None:
            if self.ao_detectar_leitura:
                await self.ao_detectar_leitura(None, None, False)
            return

        caminho_arquivo = e.files[0].path
        try:
            resultado = await asyncio.wait_for(
                asyncio.to_thread(processar_leitura_completa, caminho_arquivo), 
                timeout=12.0
            )
            unidade = resultado.get("unidade")
            valor = resultado.get("valor")
            sucesso = resultado.get("status") == "Sucesso"

            await self.ao_detectar_leitura(unidade, valor, sucesso)
            self.limpar_cache_captura(caminho_arquivo)
        except Exception as err:
            print(f"Erro no OCR: {err}")
            await self.ao_detectar_leitura(None, f"ERRO_{str(err)}", False)

    @staticmethod
    def limpar_cache_captura(caminho):
        try:
            if caminho and os.path.exists(caminho):
                os.remove(caminho)
        except: pass