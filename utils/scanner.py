import flet as ft
import asyncio
from utils.leitor_ocr import processar_leitura_completa

class ScannerAguaFlow:
    def __init__(self, page, ao_detectar_leitura):
        self.page = page
        # Função da interface que receberá os dados (unidade, valor, sucesso)
        self.ao_detectar_leitura = ao_detectar_leitura
        self.picker = ft.FilePicker(on_result=self._processar_resultado)
        self.page.overlay.append(self.picker)
        self.tipo_leitura = "Água" # Padrão

    async def iniciar_scan(self, tipo="Água"):
        """Abre a câmara definindo se a leitura é Água ou Gás."""
        self.tipo_leitura = tipo
        await self.picker.pick_files(allow_multiple=False)

    async def _processar_resultado(self, e: ft.FilePickerResultEvent):
        if not e.files:
            return

        caminho_arquivo = e.files[0].path
        
        # --- LÓGICA DE TIMEOUT DE 10 SEGUNDOS ---
        try:
            # Tenta processar o OCR dentro do limite de tempo
            # Usamos o asyncio.wait_for para garantir o timeout planeado
            resultado = await asyncio.wait_for(
                self._executar_ocr(caminho_arquivo), 
                timeout=10.0
            )
            
            await self._tratar_retorno_ocr(resultado)

        except asyncio.TimeoutError:
            # Se demorar mais de 10s, interrompe e muda para modo manual
            await self.ao_detectar_leitura(None, "", False)
            self._notificar("⏱️ Timeout: OCR demorou muito. Insira manualmente.", "orange")

    async def _executar_ocr(self, caminho):
        """Chama o motor de OCR (leitor_ocr.py)"""
        # Passamos o caminho para o processamento de imagem
        return processar_leitura_completa(caminho)

    async def _tratar_retorno_ocr(self, resultado):
        """Analisa o dicionário vindo do leitor_ocr e envia para a UI."""
        status = resultado.get("status")
        unidade = resultado.get("unidade")
        valor = resultado.get("valor")

        if status == "Sucesso":
            # Detectou tudo. Enviamos para a UI validar e o utilizador confirmar.
            await self.ao_detectar_leitura(unidade, valor, True)
            self._notificar(f"✅ {self.tipo_leitura} lida com sucesso!", "green")
            
        elif status in ["Manual", "OCR_Falhou"]:
            # Identificou a unidade (QR), mas não o valor. Preenche a unidade e foca no manual.
            await self.ao_detectar_leitura(unidade, "", False)
            self._notificar("📍 Unidade identificada. Digite o valor manualmente.", "blue")
            
        else:
            self._notificar("❌ Não foi possível ler o hidrómetro. Tente outra foto.", "red")

    def _notificar(self, texto, cor):
        self.page.snack_bar = ft.SnackBar(ft.Text(texto), bgcolor=cor)
        self.page.snack_bar.open = True
        self.page.update()