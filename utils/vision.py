"""
OCR de hidrômetros — compatível com Desktop e Android.

Desktop: cv2 (câmera + QR) + Tesseract (fallback offline)
Android: Pillow para leitura de imagem + Claude Vision (sem Tesseract)
"""
import base64
import os
import time
import logging

logger = logging.getLogger(__name__)

# ── imports condicionais ──────────────────────────────────────────────────────
try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    logger.info("cv2 não disponível — modo Android/sem câmera ativo.")

try:
    import pytesseract
    _TESSERACT_CMD = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    if os.path.exists(_TESSERACT_CMD):
        pytesseract.pytesseract.tesseract_cmd = _TESSERACT_CMD
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

try:
    from PIL import Image as _PILImage
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# Mude para True em desenvolvimento para pular câmera/OCR real
MODO_SIMULADOR = False


def processar_foto_hidrometro(caminho_foto: str, tipo: str = "água"):
    """
    Extrai a leitura de um hidrômetro a partir de uma foto.

    Estratégia:
      1. Claude Vision (API) — alta precisão para medidores mecânicos/analógicos
      2. Tesseract — fallback offline (somente desktop, se disponível)

    Retorna: (unidade_qr: str | None, valor_leitura: str | None, status: str)
      status: 'ok'          — leitura obtida
              'offline'     — sem internet; Tesseract tentado como fallback
              'sem_leitura' — OCR não reconheceu os dígitos
    """
    if MODO_SIMULADOR:
        logger.info("[SIMULADOR] Retornando dados fixos")
        time.sleep(0.8)
        return "Apto 101", "00542.30", "ok"

    # Detecta QR Code e lê imagem (cv2 disponível = desktop)
    unidade_qr = None
    img_redim = None

    if CV2_AVAILABLE:
        img = cv2.imread(caminho_foto)
        if img is not None:
            largura_alvo = 1280
            fator = largura_alvo / img.shape[1]
            img_redim = cv2.resize(img, (largura_alvo, int(img.shape[0] * fator)))

            detector = cv2.QRCodeDetector()
            dados_qr, _, _ = detector.detectAndDecode(img_redim)
            unidade_qr = dados_qr if dados_qr else None

    # OCR primário: Claude Vision
    valor, foi_offline = _ocr_claude(caminho_foto, tipo)

    # OCR fallback: Tesseract (somente desktop + disponível)
    if valor is None and TESSERACT_AVAILABLE and img_redim is not None:
        logger.info("Claude Vision indisponível — tentando Tesseract")
        valor = _ocr_tesseract(img_redim)
        status = "offline" if foi_offline else "sem_leitura"
    elif valor is None:
        status = "offline" if foi_offline else "sem_leitura"
    else:
        status = "ok"

    return unidade_qr, valor, status


# ── Pré-processamento de imagem ───────────────────────────────────────────────

def _preparar_imagem_bytes(caminho_foto: str) -> bytes:
    """
    Recorta e redimensiona a imagem antes de enviar ao Claude.
    Usa cv2 se disponível, senão usa Pillow.
    """
    if CV2_AVAILABLE:
        img = cv2.imread(caminho_foto)
        if img is not None:
            h, w = img.shape[:2]
            if h > w:  # portrait: foca na metade inferior (área do medidor)
                img = img[int(h * 0.45):int(h * 0.90), :]
            max_dim = 1024
            fator = min(max_dim / img.shape[1], max_dim / img.shape[0], 1.0)
            if fator < 1.0:
                img = cv2.resize(img, (int(img.shape[1] * fator), int(img.shape[0] * fator)),
                                 interpolation=cv2.INTER_AREA)
            _, buf = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 92])
            return buf.tobytes()

    if PIL_AVAILABLE:
        try:
            img = _PILImage.open(caminho_foto)
            w, h = img.size
            if h > w:
                img = img.crop((0, int(h * 0.45), w, int(h * 0.90)))
            img.thumbnail((1024, 1024))
            import io
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=92)
            return buf.getvalue()
        except Exception:
            pass

    with open(caminho_foto, "rb") as f:
        return f.read()


def _portrait_detect(caminho_foto: str) -> bool:
    """Retorna True se a imagem estiver em retrato."""
    if CV2_AVAILABLE:
        img = cv2.imread(caminho_foto)
        return img is not None and img.shape[0] > img.shape[1]
    if PIL_AVAILABLE:
        try:
            img = _PILImage.open(caminho_foto)
            w, h = img.size
            return h > w
        except Exception:
            pass
    return False


# ── Prompt OCR por tipo de medidor ────────────────────────────────────────────

def _prompt_ocr(tipo: str, is_portrait: bool = False) -> str:
    is_gas = "gás" in tipo.lower() or "gas" in tipo.lower()
    localizacao = (
        "A foto é uma screenshot de app de câmera: ignore a interface do celular no topo e fundo, "
        "e foque no medidor circular que aparece na metade INFERIOR da imagem. " if is_portrait else ""
    )
    if is_gas:
        return (
            f"Esta é uma foto de um medidor de GÁS. {localizacao}"
            "Localize o visor retangular com dígitos numéricos no medidor. "
            "O visor tem 8 posições: os 5 primeiros dígitos (fundo branco/preto) são a parte inteira, "
            "os 3 últimos (fundo VERMELHO) são as casas decimais. "
            "Leia cada dígito com cuidado. Use ponto decimal. "
            "Exemplos: '00327.833', '01584.480'. Retorne APENAS o número. Se não conseguir: null"
        )
    return (
        f"Esta é uma foto de um medidor de ÁGUA. {localizacao}"
        "Localize o visor retangular com dígitos numéricos no medidor. "
        "O visor tem 7 posições: os 5 primeiros dígitos (fundo branco/preto) são a parte inteira, "
        "os 2 últimos (fundo VERMELHO) são as casas decimais. "
        "Leia cada dígito com cuidado. Use ponto decimal. "
        "Exemplos: '00227.86', '02673.00'. Retorne APENAS o número. Se não conseguir: null"
    )


# ── OCR via Claude Vision ─────────────────────────────────────────────────────

def _ocr_claude(caminho_foto: str, tipo: str = "água") -> tuple:
    """
    Envia a imagem para Claude Haiku e extrai o valor do medidor.
    Retorna (valor, foi_offline).
    """
    try:
        from anthropic import Anthropic, APIConnectionError, APITimeoutError
        from dotenv import load_dotenv
        load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            logger.warning("ANTHROPIC_API_KEY não encontrada — pulando Claude Vision")
            return None, True

        is_portrait = _portrait_detect(caminho_foto)
        raw = _preparar_imagem_bytes(caminho_foto)
        img_b64 = base64.standard_b64encode(raw).decode()

        client = Anthropic(api_key=api_key)
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=50,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {
                        "type": "base64", "media_type": "image/jpeg", "data": img_b64,
                    }},
                    {"type": "text", "text": _prompt_ocr(tipo, is_portrait)},
                ],
            }],
        )

        texto = msg.content[0].text.strip()
        logger.info(f"Claude Vision OCR bruto: '{texto}'")

        if not texto or texto.lower() == "null":
            return None, False

        texto = texto.replace(",", ".")
        float(texto)  # valida numérico
        return texto, False

    except Exception as e:
        try:
            from anthropic import APIConnectionError, APITimeoutError
            if isinstance(e, (APIConnectionError, APITimeoutError)):
                logger.warning(f"Claude Vision sem internet: {e}")
                return None, True
        except ImportError:
            pass
        logger.warning(f"Claude Vision OCR erro: {e}")
        msg_lower = str(e).lower()
        is_offline = any(w in msg_lower for w in ("connect", "timeout", "network", "unreachable"))
        return None, is_offline


# ── OCR via Tesseract (fallback desktop) ──────────────────────────────────────

def _ocr_tesseract(img_redim) -> str | None:
    """Tenta extrair dígitos via Tesseract (somente desktop)."""
    if not TESSERACT_AVAILABLE or not CV2_AVAILABLE:
        return None
    try:
        cinza = cv2.cvtColor(img_redim, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        cinza = clahe.apply(cinza)

        candidatos = []
        _, bin1 = cv2.threshold(cinza, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        blur = cv2.medianBlur(cinza, 3)
        bin2 = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                     cv2.THRESH_BINARY, 15, 8)
        bin3 = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                     cv2.THRESH_BINARY_INV, 11, 2)

        for img_bin in [bin1, bin2, bin3]:
            for cfg in ['--psm 6 --oem 3 -c tessedit_char_whitelist=0123456789.',
                        '--psm 7 --oem 3 -c tessedit_char_whitelist=0123456789.']:
                try:
                    txt = pytesseract.image_to_string(img_bin, config=cfg).strip()
                    digits = ''.join(c for c in txt if c.isdigit() or c == '.').strip('.')
                    if len(digits) >= 4:
                        candidatos.append(digits)
                except Exception:
                    pass

        if not candidatos:
            return None
        melhor = max(candidatos, key=len)
        logger.info(f"Tesseract OCR melhor candidato: '{melhor}'")
        return melhor
    except Exception as e:
        logger.warning(f"Tesseract OCR erro: {e}")
        return None
