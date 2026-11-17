from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base directory for the EmergencyRoute-AI project
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Core metadata
    PROJECT_NAME: str = "EmergencyRoute AI"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Intelligent Emergency Vehicle Route Planning Platform - Phase 1"
    
    # Geographic scope: Phagwara, Punjab, India
    CITY: str = "Phagwara, Punjab, India"
    DEFAULT_LAT: float = 31.2231
    DEFAULT_LNG: float = 75.7708
    DEFAULT_SEARCH_RADIUS_METERS: int = 6000
    
    # Directory paths
    ROOT_DIR: Path = PROJECT_ROOT
    DATA_DIR: Path = PROJECT_ROOT / "data"
    OSM_CACHE_DIR: Path = PROJECT_ROOT / "data" / "raw" / "osm"
    PROCESSED_GRAPH_DIR: Path = PROJECT_ROOT / "data" / "processed" / "graph"
    PROCESSED_NODES_DIR: Path = PROJECT_ROOT / "data" / "processed" / "nodes"
    PROCESSED_EDGES_DIR: Path = PROJECT_ROOT / "data" / "processed" / "edges"
    TRAFFIC_DATA_DIR: Path = PROJECT_ROOT / "data" / "traffic"
    MAPS_OUTPUT_DIR: Path = PROJECT_ROOT / "maps"
    REPORTS_OUTPUT_DIR: Path = PROJECT_ROOT / "reports"
    LOGS_DIR: Path = PROJECT_ROOT / "logs"
    
    # Authoritative files
    GRAPHML_PATH: Path = PROJECT_ROOT / "data" / "processed" / "graph" / "phagwara_roads.graphml"
    
    # Delhivery Maps Integration
    DELHIVERY_API_KEY: Optional[str] = None
    DELHIVERY_BASE_URL: str = "https://maps.delhivery.com/api/v1"
    DELHIVERY_REQUEST_TIMEOUT_SECONDS: float = 10.0
    DELHIVERY_MAX_RETRIES: int = 3
    DELHIVERY_RETRY_BACKOFF_SECONDS: float = 1.0

    # OSRM (Open Source Routing Machine) Integration
    OSRM_BASE_URL: str = "https://router.project-osrm.org"
    OSRM_REQUEST_TIMEOUT_SECONDS: float = 8.0
    OSRM_USER_AGENT: str = "EmergencyRoute-AI/1.0 (academic SIH testing)"

    # TomTom Live Traffic & Maps Platform Integration
    TOMTOM_API_KEY: Optional[str] = None
    TOMTOM_BASE_URL: str = "https://api.tomtom.com"
    TOMTOM_REQUEST_TIMEOUT_SECONDS: float = 8.0
    
    # Traffic provider mode: 'synthetic', 'delhivery', or 'hybrid'
    TRAFFIC_PROVIDER_MODE: str = "synthetic"
    
    # API Server settings
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: str = "*"

settings = Settings()

