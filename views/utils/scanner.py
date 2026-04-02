import flet as ft
from database.database import Database
from views import leitor_ocr

# from database import Database


class ScannerAguaFlow:
    def __init__(self, page, ao_detectar_leitura):
        self.page = page
        # 'ao_detectar_leitura' será a função da interface que atualiza os campos na tela
        self.ao_detectar_leitura = ao_detectar_leitura
        self.picker = ft.FilePicker(on_result=self._processar_resultado)
        self.page.overlay.append(self.picker)

    async def iniciar_scan(self):
        # Abre a câmera ou seletor de arquivos
        await self.picker.pick_files_async(allow_multiple=False)

    async def _processar_resultado(self, e: ft.FilePickerResultEvent):
        if e.files:
            resultado = leitor_ocr.processar_leitura_completa(e.files[0].path)

            if resultado["status"] == "Sucesso":
                # Busca o ID numérico para o SQLite
                id_db = Database.buscar_por_unidade(resultado["unidade"])
                if id_db:
                    Database.registrar_leitura(id_db, resultado["valor"])
                    await self.ao_detectar_leitura(resultado["unidade"], resultado["valor"], True)

            elif resultado["status"] == "Manual":
                # Preenche a unidade e foca no campo de valor para o zelador digitar
                await self.ao_detectar_leitura(resultado["unidade"], "", False)

                self.page.snack_bar = ft.SnackBar(
                    ft.Text(
                        "📍 Unidade identificada! Por favor, insira o valor manualmente."),
                    bgcolor="blue"
                )

            else:
                # Falha total (nem QR nem OCR)
                self.page.snack_bar = ft.SnackBar(
                    ft.Text(
                        "❌ Não foi possível identificar o QR Code. Tente aproximar mais."),
                    bgcolor="orange"
                )

            self.page.snack_bar.open = True
            self.page.update()
