from typing import Dict

# Standard Punjab/Indian urban baseline speeds (km/h) by OSM highway classification
BASE_HIGHWAY_SPEEDS: Dict[str, float] = {
    "motorway": 90.0,
    "trunk": 70.0,
    "primary": 50.0,
    "secondary": 40.0,
    "tertiary": 30.0,
    "residential": 25.0,
    "unclassified": 25.0,
    "living_street": 15.0,
    "service": 15.0,
}

# Congestion speed ratio thresholds (current_speed / baseline_speed)
CONGESTION_THRESHOLDS = {
    "free_flow": 0.85,   # >= 85% of base speed
    "low": 0.65,         # 65% - 85%
    "moderate": 0.45,    # 45% - 65%
    "heavy": 0.30,       # 30% - 45%
    "severe": 0.0,       # < 30%
}

