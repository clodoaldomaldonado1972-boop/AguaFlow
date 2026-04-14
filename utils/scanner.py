import flet as ft
import asyncio
from utils.leitor_ocr import processar_leitura_completa

class ScannerAguaFlow:
    def __init__(self, page: ft.Page, ao_detectar_leitura):
        self.page = page
        self.ao_detectar_leitura = ao_detectar_leitura
        
        # Criamos o seletor de arquivos
        self.picker = ft.FilePicker(on_result=self._processar_resultado)
        
        # Garantimos que o overlay receba o objeto para ele não ser None
        if self.picker not in self.page.overlay:
            self.page.overlay.append(self.picker)
        
        self.page.update() 
        self.tipo_leitura = "Água"

    async def iniciar_scan(self, tipo="Água"):
        self.tipo_leitura = tipo
        
        # Garante que o picker está no overlay e a página está atualizada
        if self.picker not in self.page.overlay:
            self.page.overlay.append(self.picker)
            self.page.update()
            await asyncio.sleep(0.2) # Tempo para o Flet processar o componente

        try:
            # Só tenta abrir se o picker estiver vinculado a uma página
            if self.picker.page:
                await self.picker.pick_files(allow_multiple=False)
            else:
                # Se ainda não estiver vinculado, força um update e tenta novamente
                self.page.update()
                await asyncio.sleep(0.3)
                await self.picker.pick_files(allow_multiple=False)
        except Exception as e:
            print(f"Erro ao abrir câmara: {e}")

    async def _processar_resultado(self, e: ft.FilePickerResultEvent):
        if not e.files:
            return

        caminho_arquivo = e.files[0].path
        
        try:
            # Timeout de segurança para o OCR não travar a UI
            resultado = await asyncio.wait_for(
                self._executar_ocr(caminho_arquivo), 
                timeout=10.0
            )
            await self._tratar_retorno_ocr(resultado)
        except Exception as ex:
            print(f"Erro no processamento: {ex}")
            await self.ao_detectar_leitura(None, "", False)

    async def _executar_ocr(self, caminho):
        return processar_leitura_completa(caminho)

    async def _tratar_retorno_ocr(self, resultado):
        status = resultado.get("status")
        unidade = resultado.get("unidade")
        valor = resultado.get("valor")

        if status == "Sucesso":
            await self.ao_detectar_leitura(unidade, valor, True)
            self._notificar(f"✅ {self.tipo_leitura} lida com sucesso!", "green")
        else:
            # Se falhar ou for parcial, preenche a unidade e abre para manual
            await self.ao_detectar_leitura(unidade, "", False)
            self._notificar("📍 OCR inconclusivo. Insira o valor manualmente.", "blue")

    def _notificar(self, texto, cor):
        self.page.snack_bar = ft.SnackBar(ft.Text(texto), bgcolor=cor)
        self.page.snack_bar.open = True
        self.page.update()