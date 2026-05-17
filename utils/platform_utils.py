"""
Utilitários de detecção de plataforma e caminhos de storage seguros para Android/Desktop.
"""
import os


def is_android() -> bool:
    return os.environ.get("FLET_PLATFORM") == "android"


def is_mobile() -> bool:
    return os.environ.get("FLET_PLATFORM") in ("android", "ios")


def get_storage_dir(subdir: str = "") -> str:
    """
    Retorna o diretório de armazenamento correto por plataforma.

    Android : $FLET_APP_STORAGE_DATA (diretório privado do app, sem permissão extra)
    Desktop : <raiz_projeto>/exports  (comportamento atual)
    """
    if is_android():
        # Flet define esta variável automaticamente no Android
        base = os.environ.get(
            "FLET_APP_STORAGE_DATA",
            os.path.join(os.getcwd(), "storage")
        )
    else:
        base = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "exports"
        )

    path = os.path.join(base, subdir) if subdir else base
    os.makedirs(path, exist_ok=True)
    return path


def get_relatorios_dir() -> str:
    """Diretório de relatórios PDF/CSV."""
    if is_android():
        base = os.environ.get("FLET_APP_STORAGE_DATA", os.path.join(os.getcwd(), "storage"))
        path = os.path.join(base, "relatorios")
    else:
        path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "relatorios"
        )
    os.makedirs(path, exist_ok=True)
    return path


def get_temp_dir() -> str:
    """Diretório temporário para fotos do scanner."""
    if is_android():
        base = os.environ.get("FLET_APP_STORAGE_TEMP", os.path.join(os.getcwd(), "temp"))
    else:
        base = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "temp"
        )
    os.makedirs(base, exist_ok=True)
    return base
