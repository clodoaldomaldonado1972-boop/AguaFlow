import flet as ft
import asyncio
import os
from utils.leitor_ocr import processar_leitura_completa

class ScannerAguaFlow:
    def __init__(self, page: ft.Page, ao_detectar_leitura):
        self.page = page
        self.ao_detectar_leitura = ao_detectar_leitura
        # O modo será definido no momento do clique (ÁGUA ou GÁS)
        self.modo_atual = "AGUA" 
        
        self.picker = ft.FilePicker(on_result=self._processar_resultado)
        
        if self.picker not in self.page.overlay:
            self.page.overlay.append(self.picker)
        
        self.page.update()

    async def iniciar_scan(self):
        # Pega o modo que está salvo na sessão da página (definido na medicao.py)
        self.modo_atual = self.page.session.get("modo_leitura") or "AGUA"
        
        try:
            # pick_files abre a câmera nativa do Android
            self.picker.take_photo() 
        except Exception as e:
            print(f"Erro ao abrir câmera: {e}")

    async def _processar_resultado(self, e: ft.FilePickerResultEvent):
        if not e.files or e.files[0].path is None:
            if self.ao_detectar_leitura:
                await self.ao_detectar_leitura(None, None, False)
            return

        caminho_arquivo = e.files[0].path
        try:
            # Processamento em thread separada com o MODO correto (Água ou Gás)
            # Passamos o self.modo_atual para o leitor_ocr respeitar as casas decimais
            resultado = await asyncio.wait_for(
                asyncio.to_thread(processar_leitura_completa, caminho_arquivo, self.modo_atual), 
                timeout=12.0
            )
            
            unidade = resultado.get("unidade")
            valor = resultado.get("consumo") # Mudamos para 'consumo' para alinhar com leitor_ocr.py
            sucesso = resultado.get("status") == "Sucesso"

            if self.ao_detectar_leitura:
                await self.ao_detectar_leitura(unidade, valor, sucesso)
                
            # Limpa a foto da memória do celular após o uso
            if os.path.exists(caminho_arquivo):
                os.remove(caminho_arquivo)
                
        except Exception as err:
            print(f"Erro no OCR ou Timeout: {err}")
            if self.ao_detectar_leitura:
                await self.ao_detectar_leitura(None, None, False)