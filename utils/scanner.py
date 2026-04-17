import flet as ft
import asyncio
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
            await self.picker.pick_files(
                allow_multiple=False,
                file_type=ft.FilePickerFileType.IMAGE
            )
        except Exception as e:
            print(f"Erro ao abrir câmera: {e}")

    async def _processar_resultado(self, e: ft.FilePickerResultEvent):
        if not e.files or e.files[0].path is None:
            # Se o usuário cancelar a câmera, habilita manual
            await self.ao_detectar_leitura(None, "", False)
            return

        caminho_arquivo = e.files[0].path
        
        try:
            # --- LÓGICA DOS 10 SEGUNDOS ---
            # Se o OCR demorar mais de 10s, ele lança uma exceção e cai no except
            resultado = await asyncio.wait_for(
                asyncio.to_thread(processar_leitura_completa, caminho_arquivo), 
                timeout=10.0
            )
            
            unidade = resultado.get("unidade")
            valor = resultado.get("valor")
            sucesso = resultado.get("status") == "Sucesso"

            await self.ao_detectar_leitura(unidade, valor, sucesso)
            
        except asyncio.TimeoutError:
            print("OCR Timeout: 10 segundos esgotados.")
            # Notifica falha e libera para manual
            await self.ao_detectar_leitura(None, "", False)
        except Exception as ex:
            print(f"Erro no processamento: {ex}")
            await self.ao_detectar_leitura(None, "", False)