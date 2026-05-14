import cv2
import pytesseract
import numpy as np
import base64
import os
import time
import logging

logger = logging.getLogger(__name__)

# Mude para True em desenvolvimento para pular câmera/OCR real
MODO_SIMULADOR = False

TESSERACT_CMD = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
if os.path.exists(TESSERACT_CMD):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD


def processar_foto_hidrometro(caminho_foto: str, tipo: str = "água"):
    """
    Extrai a leitura de um hidrômetro a partir de uma foto.

    Estratégia:
      1. Claude Vision (API local) — alta precisão para medidores mecânicos/analógicos
      2. Tesseract — fallback offline com pré-processamento adaptativo

    Retorna: (unidade_qr: str | None, valor_leitura: str | None)
    """
    if MODO_SIMULADOR:
        logger.info("[SIMULADOR] Retornando dados fixos")
        time.sleep(0.8)
        return "Apto 101", "00542.30"

    img = cv2.imread(caminho_foto)
    if img is None:
        logger.error(f"Não foi possível ler a imagem: {caminho_foto}")
        return None, None

    # --- QR Code (igual ao código original) ---
    largura_alvo = 1280
    fator = largura_alvo / img.shape[1]
    img_redim = cv2.resize(img, (largura_alvo, int(img.shape[0] * fator)))

    detector = cv2.QRCodeDetector()
    dados_qr, _, _ = detector.detectAndDecode(img_redim)
    unidade_qr = dados_qr if dados_qr else None

    # --- OCR: Claude Vision (primário) ---
    valor = _ocr_claude(caminho_foto, tipo)

    # --- OCR: Tesseract (fallback offline) ---
    if valor is None:
        logger.info("Claude Vision falhou ou offline — tentando Tesseract")
        valor = _ocr_tesseract(img_redim)

    return unidade_qr, valor


# ─── OCR via Claude Vision ────────────────────────────────────────────────────

def _ocr_claude(caminho_foto: str, tipo: str = "água") -> str | None:
    """Envia a imagem para Claude Haiku e extrai o valor do medidor."""
    try:
        from anthropic import Anthropic
        from dotenv import load_dotenv
        load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            logger.warning("ANTHROPIC_API_KEY não encontrada — pulando Claude Vision")
            return None

        with open(caminho_foto, "rb") as f:
            img_b64 = base64.standard_b64encode(f.read()).decode()

        # Detecta media type pela extensão
        ext = os.path.splitext(caminho_foto)[1].lower()
        media_type = "image/jpeg" if ext in (".jpg", ".jpeg") else "image/png"

        client = Anthropic(api_key=api_key)
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=50,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": img_b64,
                        },
                    },
                    {
                        "type": "text",
                        "text": (
                            f"Esta é uma foto de um hidrômetro de {tipo}. "
                            "Leia o número exibido no mostrador/visor do medidor. "
                            "Os dígitos em vermelho (ou em cor diferente dos demais) representam as casas decimais — "
                            "inclua-os após o ponto decimal. "
                            "Retorne APENAS o número com até 3 casas decimais usando ponto como separador decimal, ex: 328.936. "
                            "Não inclua vírgula, texto, unidade ou explicação. "
                            "Se não conseguir ler claramente, retorne: null"
                        ),
                    },
                ],
            }],
        )

        texto = msg.content[0].text.strip()
        logger.info(f"Claude Vision OCR bruto: '{texto}'")

        if not texto or texto.lower() == "null":
            return None

        # Normaliza decimal e valida
        texto = texto.replace(",", ".")
        float(texto)  # valida que é numérico
        return texto

    except Exception as e:
        logger.warning(f"Claude Vision OCR erro: {e}")
        return None


# ─── OCR via Tesseract (fallback) ────────────────────────────────────────────

def _ocr_tesseract(img_redim) -> str | None:
    """
    Tenta extrair dígitos usando Tesseract com múltiplas estratégias de pré-processamento.
    Retorna o melhor resultado (string mais longa que parece uma leitura válida).
    """
    try:
        cinza = cv2.cvtColor(img_redim, cv2.COLOR_BGR2GRAY)

        # CLAHE para melhorar contraste em fotos escuras/sujas
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        cinza = clahe.apply(cinza)

        candidatos = []

        # Estratégia 1: Otsu global
        _, bin1 = cv2.threshold(cinza, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Estratégia 2: Adaptativa gaussiana
        blur = cv2.medianBlur(cinza, 3)
        bin2 = cv2.adaptiveThreshold(
            blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 8
        )

        # Estratégia 3: Adaptativa invertida
        bin3 = cv2.adaptiveThreshold(
            blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
        )

        config6 = '--psm 6 --oem 3 -c tessedit_char_whitelist=0123456789.'
        config7 = '--psm 7 --oem 3 -c tessedit_char_whitelist=0123456789.'

        for img_bin in [bin1, bin2, bin3]:
            for cfg in [config6, config7]:
                try:
                    txt = pytesseract.image_to_string(img_bin, config=cfg).strip()
                    digits = ''.join(c for c in txt if c.isdigit() or c == '.')
                    digits = digits.strip('.')
                    if len(digits) >= 4:  # leitura mínima plausível
                        candidatos.append(digits)
                except Exception:
                    pass

        if not candidatos:
            return None

        # Prefere o candidato mais longo (mais dígitos = mais informação)
        melhor = max(candidatos, key=len)
        logger.info(f"Tesseract OCR melhor candidato: '{melhor}'")
        return melhor

    except Exception as e:
        logger.warning(f"Tesseract OCR erro: {e}")
        return None
