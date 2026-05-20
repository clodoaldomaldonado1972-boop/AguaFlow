"""
AguaFlow Mobile — Motor de Visão Otimizado para APK.
Processamento local leve via Pillow + OCR Inteligente via Claude Vision na Nuvem.
"""
import base64
import os
import time
import logging
import io

logger = logging.getLogger(__name__)

# ── IMPORTS HOMOLOGADOS PARA MOBILE ──────────────────────────────────────────
# OpenCV, NumPy e Tesseract foram totalmente removidos para evitar falhas de análise estática no Buildozer.
try:
    from PIL import Image as _PILImage
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logger.error("⚠️ Biblioteca Pillow (PIL) não está disponível no ambiente móvel.")

# Flags de compatibilidade mantidas estritamente como False para não quebrar referências externas nas Views
CV2_AVAILABLE = False
TESSERACT_AVAILABLE = False

# Mude para True em ambiente de desenvolvimento para simular respostas sem consumir a API real
MODO_SIMULADOR = False


def processar_foto_hidrometro(caminho_foto: str, tipo: str = "água"):
    """
    Extrai a leitura de um hidrômetro/medidor de gás a partir de uma foto.

    Estratégia Mobile Otimizada:
      1. Compressão local assíncrona utilizando Pillow (Reduz consumo de banda e RAM).
      2. Envio do payload em Base64 para processamento na nuvem via Claude Vision.
    
    Retorna: (unidade_qr: None, valor_leitura: str | None, status: str)
    """
    if MODO_SIMULADOR:
        logger.info("🤖 [SIMULADOR] Retornando dados fixos de teste mobile.")
        time.sleep(0.8)
        return None, "00542.30", "ok"

    if not os.path.exists(caminho_foto):
        logger.error(f"❌ Arquivo de mídia não encontrado no cache: {caminho_foto}")
        return None, None, "sem_leitura"

    # OCR primário e único: Claude Vision na Nuvem
    valor, foi_offline = _ocr_claude(caminho_foto, tipo)

    if valor is None:
        status = "offline" if foi_offline else "sem_leitura"
    else:
        status = "ok"

    # Retorna sempre None para o QR Code local no ambiente mobile, delegando o vínculo 
    # de unidades para a lógica de metadados da View ou digitação assistida.
    return None, valor, status


# ── Pré-processamento de Imagem Leve (Pillow) ─────────────────────────────────

def _preparar_imagem_bytes(caminho_foto: str) -> bytes:
    """
    Recorta e redimensiona a imagem antes de enviar ao Claude utilizando apenas o Pillow.
    Evita estouro de memória no Android e otimiza o upload.
    """
    if PIL_AVAILABLE:
        try:
            img = _PILImage.open(caminho_foto)
            w, h = img.size
            
            # Se a foto estiver em modo retrato (comum em celulares), foca na metade inferior (área do medidor)
            if h > w:
                img = img.crop((0, int(h * 0.45), w, int(h * 0.90)))
            
            # Limita as dimensões máximas mantendo a proporção (recalculado de forma leve)
            img.thumbnail((1024, 1024))
            
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=88)  # 88 preserva legibilidade dos dígitos reduzindo peso
            return buf.getvalue()
        except Exception as ex:
            logger.warning(f"Falha ao processar imagem com Pillow: {ex}")

    # Fallback de segurança: lê os bytes brutos se o Pillow falhar
    with open(caminho_foto, "rb") as f:
        return f.read()


def _portrait_detect(caminho_foto: str) -> bool:
    """Retorna True se a imagem capturada estiver em orientação Retrato (Portrait)."""
    if PIL_AVAILABLE:
        try:
            img = _PILImage.open(caminho_foto)
            w, h = img.size
            return h > w
        except Exception:
            pass
    return False


# ── Prompt OCR Otimizado por Tipo de Medidor ─────────────────────────────────

def _prompt_ocr(tipo: str, is_portrait: bool = False) -> str:
    is_gas = "gás" in tipo.lower() or "gas" in tipo.lower()
    localizacao = (
        "A foto é uma captura de aplicativo móvel: ignore elementos de interface do smartphone nas extremidades, "
        "e foque estritamente no medidor circular/retangular centralizado na imagem. " if is_portrait else ""
    )
    if is_gas:
        return (
            f"Esta é uma foto de um medidor de GÁS. {localizacao}"
            "Localize o visor retangular com dígitos numéricos no medidor. "
            "O visor tem 8 posições: os 5 primeiros dígitos (fundo branco ou preto) são a parte inteira, "
            "os 3 últimos (fundo VERMELHO) são as casas decimais. "
            "Leia cada dógrafo com extrema atenção. Use ponto como separador decimal. "
            "Exemplos de saída esperada: '00327.833', '01584.480'. Retorne APENAS a string numérica limpa. Se não conseguir ler com clareza, retorne: null"
        )
    return (
        f"Esta é uma foto de um medidor de ÁGUA (Hidrômetro). {localizacao}"
        "Localize o visor retangular com dígitos numéricos no medidor. "
        "O visor tem 7 posições: os 5 primeiros dígitos (fundo branco ou preto) são a parte inteira, "
        "os 2 últimos (fundo VERMELHO) são as casas decimais. "
        "Leia cada dígito com atenção. Use ponto como separador decimal. "
        "Exemplos de saída esperada: '00227.86', '02673.00'. Retorne APENAS a string numérica limpa. Se não conseguir ler com clareza, retorne: null"
    )


# ── OCR via Claude Vision API ─────────────────────────────────────────────────

def _ocr_claude(caminho_foto: str, tipo: str = "água") -> tuple:
    """
    Envia a imagem otimizada para o Claude Haiku e extrai os valores do mostrador.
    Retorna uma tupla: (valor, foi_offline)
    """
    try:
        from anthropic import Anthropic
        from dotenv import load_dotenv
        
        # Carrega as variáveis de ambiente locais do arquivo .env corporativo
        load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            logger.warning("⚠️ ANTHROPIC_API_KEY não localizada nas variáveis de ambiente — pulando Claude Vision.")
            return None, True

        is_portrait = _portrait_detect(caminho_foto)
        raw_bytes = _preparar_imagem_bytes(caminho_foto)
        img_b64 = base64.b64encode(raw_bytes).decode("utf-8")

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
                        }
                    },
                    {
                        "type": "text",
                        "text": _prompt_ocr(tipo, is_portrait)
                    },
                ],
            }],
        )

        texto = msg.content[0].text.strip()
        logger.info(f"📡 Resposta bruta do Claude Vision: '{texto}'")

        if not texto or texto.lower() == "null":
            return None, False

        # Sanitização básica da resposta da IA
        texto = texto.replace(",", ".")
        try:
            float(texto)  # Validação de consistência numérica
            return texto, False
        except ValueError:
            logger.warning(f"⚠️ Resposta da IA não seguiu o padrão estritamente numérico: '{texto}'")
            return None, False

    except Exception as e:
        # Tratamento resiliente de conectividade móvel (Redes 3G/4G/5G oscilantes)
        try:
            from anthropic import APIConnectionError, APITimeoutError
            if isinstance(e, (APIConnectionError, APITimeoutError)):
                logger.warning(f"📶 Falha de comunicação de rede com os servidores Anthropic: {e}")
                return None, True
        except ImportError:
            pass
            
        logger.warning(f"⚠️ Erro operacional no módulo Claude Vision: {e}")
        msg_lower = str(e).lower()
        is_offline = any(keyword in msg_lower for keyword in ("connect", "timeout", "network", "unreachable", "dns"))
        return None, is_offline