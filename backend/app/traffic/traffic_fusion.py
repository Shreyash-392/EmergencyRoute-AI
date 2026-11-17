from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional, Tuple

from app.traffic.traffic_validator import TrafficValidator
from app.traffic.traffic_weight_calculator import TrafficWeightCalculator

logger = logging.getLogger(__name__)


class TrafficFusionEngine:
    """
    Traffic Fusion Engine integrating Delhivery telematics, synthetic observations,
    and mock sensor feeds into a normalized, unified edge traffic state.
    
    Principles:
    - Stale observation detection and graceful deprecation.
    - Confidence-weighted selection without ungrounded cross-source averaging.
    - Explicit synthetic baseline fallback when commercial feeds lack edge-level resolution.
    - Never treats missing data as zero traffic.
    """

    def __init__(self, validator: Optional[TrafficValidator] = None):
        self.validator = validator or TrafficValidator(max_stale_seconds=1800)

    def fuse_observations(
        self,
        primary_observations: List[Dict[str, Any]],
        fallback_observations: List[Dict[str, Any]],
        current_time: Optional[datetime] = None
    ) -> Dict[Tuple[int, int, int], Dict[str, Any]]:
        """
        Fuses incoming primary traffic observations with synthetic fallback baseline.
        Returns a dictionary mapping (u, v, key) -> computed dynamic edge attributes.
        """
        now = current_time or datetime.now(timezone.utc)
        fused_state: Dict[Tuple[int, int, int], Dict[str, Any]] = {}

        # 1. Index and validate primary observations (e.g. live sensors / telematics)
        valid_primaries: Dict[Tuple[int, int, int], Dict[str, Any]] = {}

        for obs in primary_observations:
            val_res = self.validator.validate_observation(obs, current_time=now)
            if not val_res.is_valid:
                logger.debug(f"Discarding invalid traffic observation: {val_res.reason}")
                continue

            if val_res.is_stale:
                logger.debug(f"Discarding stale traffic observation: {val_res.reason}")
                continue

            edge_key = (int(obs["u"]), int(obs["v"]), int(obs.get("key", 0)))
            
            # Confidence-aware deduplication
            existing = valid_primaries.get(edge_key)
            if existing is None or float(obs.get("confidence", 0.5)) > float(existing.get("confidence", 0.5)):
                valid_primaries[edge_key] = obs

        # 2. Process synthetic fallback baseline
        for obs in fallback_observations:
            edge_key = (int(obs["u"]), int(obs["v"]), int(obs.get("key", 0)))

            # If a valid, fresh primary observation exists, use it
            chosen_obs = valid_primaries.get(edge_key, obs)

            length_m = float(chosen_obs.get("length_meters", chosen_obs.get("length", 10.0)))
            base_spd = float(chosen_obs.get("baseline_speed_kph", chosen_obs.get("speed_kph", 30.0)))
            curr_spd = float(chosen_obs.get("current_speed_kph", base_spd))
            src = str(chosen_obs.get("source", "synthetic_simulation"))

            weight_info = TrafficWeightCalculator.calculate_edge_weight(
                length_meters=length_m,
                base_speed_kph=base_spd,
                current_speed_kph=curr_spd,
                traffic_source=src
            )

            fused_state[edge_key] = weight_info

        return fused_state

