from typing import Optional
from flet.controls.base_control import control
from flet.controls.services.service import Service

__all__ = ["CameraService"]


@control("CameraService")
class CameraService(Service):
    """Serviço nativo de câmera via image_picker (Flutter extension)."""

    async def pick_image_from_camera(self) -> Optional[str]:
        """Abre a câmera nativa e retorna o caminho do arquivo capturado."""
        result = await self._invoke_method(
            "pick_image_from_camera",
            {},
            timeout=120,
        )
        if isinstance(result, str) and result.startswith("ERROR:"):
            raise RuntimeError(result[6:])
        return result

    async def pick_image_from_gallery(self) -> Optional[str]:
        """Abre a galeria e retorna o caminho da foto selecionada."""
        result = await self._invoke_method(
            "pick_image_from_gallery",
            {},
            timeout=120,
        )
        if isinstance(result, str) and result.startswith("ERROR:"):
            raise RuntimeError(result[6:])
        return result
