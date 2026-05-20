from typing import Optional
from flet.controls.base_control import control
from flet.controls.services.service import Service

__all__ = ["BarcodeScannerService"]


@control("BarcodeScannerService")
class BarcodeScannerService(Service):
    """Serviço de escaneamento QR/barcode via mobile_scanner (Flutter extension)."""

    async def scan_barcode(self) -> Optional[str]:
        """Abre tela de escaneamento e retorna o código detectado (None = cancelado)."""
        result = await self._invoke_method(
            "scan_barcode",
            {},
            timeout=60,
        )
        if isinstance(result, str) and result.startswith("ERROR:"):
            raise RuntimeError(result[6:])
        return result
