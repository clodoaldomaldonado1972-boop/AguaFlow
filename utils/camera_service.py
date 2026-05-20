from typing import Optional
from flet.controls.base_control import control
from flet.controls.services.service import Service

__all__ = ["CameraService"]


@control("CameraService")
class CameraService(Service):
    """Serviço nativo de câmera via image_picker (Flutter extension)."""

    async def pick_image_from_camera(self) -> Optional[str]:
        """Abre a câmera nativa e retorna o caminho do arquivo capturado."""
        return await self._invoke_method(
            "pick_image_from_camera",
            {},
            timeout=120,
        )

    async def pick_image_from_gallery(self) -> Optional[str]:
        """Abre a galeria e retorna o caminho da foto selecionada."""
        return await self._invoke_method(
            "pick_image_from_gallery",
            {},
            timeout=120,
        )
