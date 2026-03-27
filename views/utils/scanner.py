import flet as ft
from .. import leitor_ocr

class ScannerAguaFlow:
    def __init__(self, page, ao_detectar_valor):
        self.page = page
        self.ao_detectar_valor = ao_detectar_valor
        # O FilePicker age como a ponte para a câmara nativa
        self.picker = ft.FilePicker(on_result=self._processar_resultado)
        self.page.overlay.append(self.picker)

    async def iniciar_scan(self):
        # Abre a câmara do telemóvel
        await self.picker.pick_files_async(allow_multiple=False)

    async def _processar_resultado(self, e: ft.FilePickerResultEvent):
        if e.files:
            caminho_foto = e.files[0].path
            # O OCR processa o ficheiro temporário
            status, valor = leitor_ocr.extrair_dados_fluxo(caminho_foto)
            
            if status == "Identificado":
                # Devolve o valor para quem chamou o scanner
                await self.ao_detectar_valor(str(valor)[:7])
            else:
                self.page.snack_bar = ft.SnackBar(
                    ft.Text("❌ Falha na leitura. Tente focar melhor."),
                    bgcolor="orange"
                )
                self.page.snack_bar.open = True
                self.page.update()