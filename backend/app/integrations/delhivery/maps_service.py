import logging
from typing import Optional
from app.integrations.delhivery.client import DelhiveryClient
from app.integrations.delhivery.schemas import MapTileConfig

logger = logging.getLogger(__name__)


class DelhiveryMapsService:
    """
    Manages map tile configuration and basemap metadata for Leaflet / React UI.
    """

    def __init__(self, client: Optional[DelhiveryClient] = None):
        self.client = client or DelhiveryClient()

    def get_tile_configuration(self) -> MapTileConfig:
        """
        Returns tile server configuration for frontend Leaflet rendering.
        If Delhivery API key is present, provides commercial Delhivery raster tile endpoint.
        Otherwise provides standard OpenStreetMap / CartoDB tiles.
        """
        if self.client.is_configured and self.client.api_key:
            return MapTileConfig(
                provider="delhivery",
                tile_url_template=f"{self.client.base_url}/tiles/{{z}}/{{x}}/{{y}}.webp?key={self.client.api_key}",
                attribution="&copy; <a href='https://www.delhivery.com/'>Delhivery Maps</a> | EmergencyRoute AI",
                max_zoom=19,
                min_zoom=1,
                subdomains=[],
                is_commercial=True,
            )

        return MapTileConfig(
            provider="openstreetmap",
            tile_url_template="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
            attribution="&copy; <a href='https://www.openstreetmap.org/copyright'>OpenStreetMap</a> contributors | EmergencyRoute AI",
            max_zoom=19,
            min_zoom=1,
            subdomains=["a", "b", "c"],
            is_commercial=False,
        )

