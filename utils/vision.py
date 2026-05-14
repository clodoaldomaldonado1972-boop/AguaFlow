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

    Retorna: (unidade_qr: str | None, valor_leitura: str | None, status: str)
      status: 'ok'          — leitura obtida (Claude Vision ou Tesseract)
              'offline'     — sem internet; Tesseract tentado como fallback
              'sem_leitura' — online mas OCR não reconheceu os dígitos
    """
    if MODO_SIMULADOR:
        logger.info("[SIMULADOR] Retornando dados fixos")
        time.sleep(0.8)
        return "Apto 101", "00542.30", "ok"

    img = cv2.imread(caminho_foto)
    if img is None:
        logger.error(f"Não foi possível ler a imagem: {caminho_foto}")
        return None, None, "sem_leitura"

    # --- QR Code ---
    largura_alvo = 1280
    fator = largura_alvo / img.shape[1]
    img_redim = cv2.resize(img, (largura_alvo, int(img.shape[0] * fator)))

    detector = cv2.QRCodeDetector()
    dados_qr, _, _ = detector.detectAndDecode(img_redim)
    unidade_qr = dados_qr if dados_qr else None

    # --- OCR: Claude Vision (primário) ---
    valor, foi_offline = _ocr_claude(caminho_foto, tipo)

    # --- OCR: Tesseract (fallback offline) ---
    if valor is None:
        logger.info("Claude Vision indisponível — tentando Tesseract")
        valor = _ocr_tesseract(img_redim)
        if valor:
            status = "offline" if foi_offline else "sem_leitura"
        else:
            status = "offline" if foi_offline else "sem_leitura"
    else:
        status = "ok"

    return unidade_qr, valor, status


# ─── Pré-processamento de imagem ─────────────────────────────────────────────

def _preparar_imagem_bytes(caminho_foto: str) -> bytes:
    """
    Recorta a imagem para focar na área do medidor antes de enviar ao Claude.

    - Foto em retrato (h > w): provavelmente screenshot de app de câmera.
      O medidor fica na metade inferior → recorta 45%–90% da altura.
    - Foto em paisagem (w >= h): close-up direto → envia como está.
    """
    img = cv2.imread(caminho_foto)
    if img is None:
        with open(caminho_foto, "rb") as f:
            return f.read()

    h, w = img.shape[:2]

    if h > w:  # portrait = screenshot do celular
        y_ini = int(h * 0.45)
        y_fim = int(h * 0.90)
        img = img[y_ini:y_fim, :]

    # Redimensiona para max 1024px mantendo aspecto (menos tokens, mais nítido)
    max_dim = 1024
    fator = min(max_dim / img.shape[1], max_dim / img.shape[0], 1.0)
    if fator < 1.0:
        img = cv2.resize(img, (int(img.shape[1] * fator), int(img.shape[0] * fator)),
                         interpolation=cv2.INTER_AREA)

    _, buf = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 92])
    return buf.tobytes()


# ─── Prompt OCR por tipo de medidor ─────────────────────────────────────────

def _prompt_ocr(tipo: str, is_portrait: bool = False) -> str:
    """
    Retorna o prompt específico para cada tipo de medidor.

    Medidor de ÁGUA (Renova/Atalaia): display com 7 dígitos — 5 inteiros + 2 decimais.
      Os 2 últimos dígitos têm fundo vermelho.  Ex: 0227|86 → 00227.86

    Medidor de GÁS (LAO/Itron): display com 8 dígitos — 5 inteiros + 3 decimais.
      Os 3 últimos dígitos têm fundo vermelho.  Ex: 00327|833 → 00327.833
    """
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
            "Leia cada dígito com cuidado — não confunda 8 com 6, nem 3 com 8. "
            "Use ponto decimal. Exemplos corretos: '00327.833', '01584.480', '00214.835'. "
            "Retorne APENAS o número. Se não conseguir ler, retorne: null"
        )
    else:
        return (
            f"Esta é uma foto de um medidor de ÁGUA. {localizacao}"
            "Localize o visor retangular com dígitos numéricos no medidor. "
            "O visor tem 7 posições: os 5 primeiros dígitos (fundo branco/preto) são a parte inteira, "
            "os 2 últimos (fundo VERMELHO) são as casas decimais. "
            "Leia cada dígito com cuidado — não confunda 2 com 3, nem 6 com 0 ou 7. "
            "Use ponto decimal. Exemplos corretos: '00227.86', '02673.00', '02308.70'. "
            "Retorne APENAS o número. Se não conseguir ler, retorne: null"
        )


# ─── OCR via Claude Vision ────────────────────────────────────────────────────

def _ocr_claude(caminho_foto: str, tipo: str = "água") -> tuple[str | None, bool]:
    """
    Envia a imagem para Claude Haiku e extrai o valor do medidor.
    Retorna (valor, foi_offline) onde foi_offline=True indica falha de rede.
    """
    try:
        from anthropic import Anthropic, APIConnectionError, APITimeoutError
        from dotenv import load_dotenv
        load_dotenv(os.path.join(os.path.dirname(
            os.path.dirname(__file__)), '.env'))

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            logger.warning(
                "ANTHROPIC_API_KEY não encontrada — pulando Claude Vision")
            return None, True  # sem chave = tratar como offline

        # Detect portrait orientation (phone screenshot) before preprocessing
        _tmp = cv2.imread(caminho_foto)
        is_portrait = _tmp is not None and _tmp.shape[0] > _tmp.shape[1]

        # Crop portrait images to meter area; landscape sent as-is
        raw = _preparar_imagem_bytes(caminho_foto)
        img_b64 = base64.standard_b64encode(raw).decode()

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
                            "media_type": "image/jpeg",
                            "data": img_b64,
                        },
                    },
                    {
                        "type": "text",
                        "text": _prompt_ocr(tipo, is_portrait),
                    },
                ],
            }],
        )

        texto = msg.content[0].text.strip()
        logger.info(f"Claude Vision OCR bruto: '{texto}'")

        if not texto or texto.lower() == "null":
            return None, False  # online, mas não reconheceu

        texto = texto.replace(",", ".")
        float(texto)  # valida numérico
        return texto, False

    except (APIConnectionError, APITimeoutError) as e:
        logger.warning(f"Claude Vision sem internet: {e}")
        return None, True  # offline confirmado
    except Exception as e:
        logger.warning(f"Claude Vision OCR erro: {e}")
        # Tentativa de detectar erro de rede por mensagem
        msg_lower = str(e).lower()
        is_offline = any(w in msg_lower for w in (
            "connect", "timeout", "network", "unreachable"))
        return None, is_offline


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
        _, bin1 = cv2.threshold(
            cinza, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

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
                    txt = pytesseract.image_to_string(
                        img_bin, config=cfg).strip()
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
