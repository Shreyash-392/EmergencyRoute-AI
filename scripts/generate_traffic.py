import json
import logging
from pathlib import Path
import sys

# Ensure backend package is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

import pandas as pd

from app.core.config import settings
from app.core.graph_loader import load_graph_from_graphml
from app.integrations.traffic.mock_traffic import MockTrafficProvider, SCENARIOS

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("generate_traffic")


def main():
    logger.info("Starting deterministic synthetic traffic generation for Phagwara road network...")
    settings.TRAFFIC_DATA_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Load Authoritative Graph
    graph = load_graph_from_graphml()
    logger.info(f"Loaded road network with {len(graph.nodes)} nodes and {len(graph.edges)} directed edges.")

    mock_provider = MockTrafficProvider(seed=42)

    # 2. Export Scenarios Metadata
    scenarios_json_path = settings.TRAFFIC_DATA_DIR / "traffic_scenarios.json"
    scenarios_data = [s.model_dump() for s in SCENARIOS]
    with open(scenarios_json_path, "w", encoding="utf-8") as f:
        json.dump(scenarios_data, f, indent=2)
    logger.info(f"Saved {len(scenarios_data)} scenarios to {scenarios_json_path}")

    # 3. Export Road Closures
    closures_csv_path = settings.TRAFFIC_DATA_DIR / "road_closures.csv"
    all_closures = []
    for s in SCENARIOS:
        closures = mock_provider.get_road_closures(scenario_id=s.scenario_id)
        for c in closures:
            row = c.model_dump()
            row["scenario_id"] = s.scenario_id
            all_closures.append(row)

    df_closures = pd.DataFrame(all_closures)
    df_closures.to_csv(closures_csv_path, index=False)
    logger.info(f"Saved road closures to {closures_csv_path} ({len(df_closures)} closure definitions)")

    # 4. Generate Traffic Observations across all edges for each scenario
    observations_records = []
    logger.info("Simulating edge conditions across all scenarios...")

    for scen in SCENARIOS:
        scen_id = scen.scenario_id
        for u, v, k, data in graph.edges(keys=True, data=True):
            length = float(data.get("length", 10.0))
            base_spd = float(data.get("speed_kph", 30.0))
            hwy = str(data.get("highway", "unclassified"))
            name = str(data.get("name", ""))

            obs = mock_provider.generate_observation_for_edge(
                u=u, v=v, key=k,
                length=length,
                baseline_speed_kph=base_spd,
                highway_class=hwy,
                name=name,
                scenario_id=scen_id
            )

            observations_records.append({
                "edge_id": obs.edge_id,
                "u": obs.u,
                "v": obs.v,
                "key": obs.key,
                "scenario_id": scen_id,
                "timestamp": obs.timestamp.isoformat(),
                "baseline_speed_kph": obs.baseline_speed_kph,
                "current_speed_kph": obs.current_speed_kph,
                "speed_ratio": obs.speed_ratio,
                "congestion_level": obs.congestion_level.value,
                "road_status": obs.road_status.value,
                "travel_time_seconds": obs.travel_time_seconds,
                "highway": hwy,
                "is_live": obs.is_live,
                "source": obs.source,
                "confidence": obs.confidence,
            })

    df_obs = pd.DataFrame(observations_records)
    obs_csv_path = settings.TRAFFIC_DATA_DIR / "traffic_observations.csv"
    logger.info(f"Saving {len(df_obs)} observations to {obs_csv_path}...")
    df_obs.to_csv(obs_csv_path, index=False)

    # 5. Generate Aggregate Traffic Profiles per Scenario and Highway Classification
    profiles_csv_path = settings.TRAFFIC_DATA_DIR / "traffic_profiles.csv"
    df_profiles = (
        df_obs.groupby(["scenario_id", "highway"])
        .agg(
            edge_count=("edge_id", "count"),
            avg_baseline_speed=("baseline_speed_kph", "mean"),
            avg_current_speed=("current_speed_kph", "mean"),
            avg_speed_ratio=("speed_ratio", "mean"),
            avg_travel_time_seconds=("travel_time_seconds", "mean"),
        )
        .reset_index()
    )
    df_profiles["avg_baseline_speed"] = df_profiles["avg_baseline_speed"].round(2)
    df_profiles["avg_current_speed"] = df_profiles["avg_current_speed"].round(2)
    df_profiles["avg_speed_ratio"] = df_profiles["avg_speed_ratio"].round(3)
    df_profiles["avg_travel_time_seconds"] = df_profiles["avg_travel_time_seconds"].round(2)
    df_profiles.to_csv(profiles_csv_path, index=False)
    logger.info(f"Saved aggregated traffic profiles to {profiles_csv_path}")

    print("\n" + "=" * 60)
    print("SYNTHETIC TRAFFIC DATASET SUMMARY")
    print("=" * 60)
    print(f"Scenarios Created:           {len(SCENARIOS)}")
    print(f"Total Observations Generated: {len(df_obs)}")
    print(f"Road Closures Recorded:      {len(df_closures)}")
    print(f"Observations CSV:            {obs_csv_path}")
    print(f"Profiles CSV:                {profiles_csv_path}")
    print(f"Scenarios JSON:              {scenarios_json_path}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()

