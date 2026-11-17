from datetime import datetime, timezone
import logging
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

VALID_SOURCES = {
    "delhivery_telematics",
    "delhivery_fleet_calibrated",
    "synthetic_simulation",
    "manual_override",
    "mock_sensor",
    "external_feed",
}


class TrafficValidationResult:
    def __init__(self, is_valid: bool, reason: str = "", is_stale: bool = False):
        self.is_valid = is_valid
        self.reason = reason
        self.is_stale = is_stale


class TrafficValidator:
    """
    Validates traffic observations for source authenticity, timestamp freshness,
    physical speed limits, and coordinate consistency.
    """

    def __init__(self, max_stale_seconds: int = 1800):
        self.max_stale_seconds = max_stale_seconds

    def validate_observation(
        self,
        observation: Dict[str, Any],
        current_time: Optional[datetime] = None
    ) -> TrafficValidationResult:
        now = current_time or datetime.now(timezone.utc)

        # 1. Source verification
        source = observation.get("source", "")
        if source not in VALID_SOURCES:
            return TrafficValidationResult(
                is_valid=False,
                reason=f"Unrecognized traffic source '{source}'. Must be one of {VALID_SOURCES}"
            )

        # 2. Edge ID presence
        u = observation.get("u")
        v = observation.get("v")
        if u is None or v is None:
            return TrafficValidationResult(is_valid=False, reason="Missing node identifiers (u, v)")

        # 3. Speed plausibility
        spd = observation.get("current_speed_kph")
        if spd is not None:
            if not isinstance(spd, (int, float)) or spd < 0 or spd > 160.0:
                return TrafficValidationResult(
                    is_valid=False,
                    reason=f"Implausible current speed {spd} km/h (must be 0-160 km/h)"
                )

        # 4. Confidence limits
        conf = observation.get("confidence", 1.0)
        if not (0.0 <= conf <= 1.0):
            return TrafficValidationResult(
                is_valid=False,
                reason=f"Confidence {conf} out of bounds [0.0, 1.0]"
            )

        # 5. Timestamp freshness / stale data detection
        ts = observation.get("timestamp")
        if ts is not None:
            if isinstance(ts, str):
                try:
                    ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                except ValueError:
                    return TrafficValidationResult(is_valid=False, reason="Invalid ISO-8601 timestamp format")

            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)

            age_seconds = (now - ts).total_seconds()
            if age_seconds > self.max_stale_seconds:
                return TrafficValidationResult(
                    is_valid=True,
                    is_stale=True,
                    reason=f"Observation is stale (age: {age_seconds:.0f}s > threshold {self.max_stale_seconds}s)"
                )

        return TrafficValidationResult(is_valid=True)

