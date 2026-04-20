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
            # pick_files não deve ser awaitado aqui para evitar bloqueios de thread
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
            # PROTEÇÃO: Timeout de 12 segundos para o processamento OCR
            resultado = await asyncio.wait_for(
                asyncio.to_thread(processar_leitura_completa, caminho_arquivo), 
                timeout=12.0
            )
            
            unidade = resultado.get("unidade")
            valor = resultado.get("valor")
            sucesso = resultado.get("status") == "Sucesso"

            if self.ao_detectar_leitura:
                await self.ao_detectar_leitura(unidade, valor, sucesso)
                
        except Exception as err:
            print(f"Erro no OCR ou Timeout (12s excedidos): {err}")
            # Em caso de falha ou tempo excedido, o sucesso=False liberta o modo manual
            if self.ao_detectar_leitura:
                await self.ao_detectar_leitura(None, None, False)

    def limpar_cache_captura(self, caminho):
        """Remove ficheiros temporários para poupar espaço no dispositivo."""
        if os.path.exists(caminho) and "temp" in caminho:
            try: os.remove(caminho)
            except: pass