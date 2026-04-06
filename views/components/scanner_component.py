import flet as ft
from .. import leitor_ocr


class ScannerComponent:
    def __init__(self, page, ao_detectar_valor):
        self.page = page
        self.ao_detectar_valor = ao_detectar_valor
        # O FilePicker atua como a ponte para a câmera nativa (Modo Scanner)
        self.picker = ft.FilePicker(on_result=self._processar_resultado)
        self.page.overlay.append(self.picker)

    async def abrir_scanner(self):
        # Abre a interface de captura do dispositivo
        await self.picker.pick_files(allow_multiple=False)

    async def _processar_resultado(self, e: ft.FilePickerResultEvent):
        if e.files:
            caminho_foto = e.files[0].path
            # Apenas extrai os dados, não salva a imagem permanentemente
            status, valor = leitor_ocr.extrair_dados_fluxo(caminho_foto)

            if status == "Identificado":
                # Retorna o valor limpo (limitado a 7 dígitos por segurança)
                await self.ao_detectar_valor(str(valor)[:7])
            else:
                self.page.snack_bar = ft.SnackBar(
                    ft.Text("❌ Não foi possível ler os números. Tente novamente."),
                    bgcolor="orange"
                )
                self.page.snack_bar.open = True
                self.page.update()
