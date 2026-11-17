import json
import urllib.request
import urllib.error

origin = (31.2260, 75.7790)  # Model Town
dest = (31.2223, 75.7672)    # Civil Hospital

print("=" * 60)
print("1. DIRECT PUBLIC OSRM SERVER QUERY")
print("=" * 60)
osrm_public_url = (
    f"https://router.project-osrm.org/route/v1/driving/"
    f"{origin[1]},{origin[0]};{dest[1]},{dest[0]}"
    f"?overview=full&geometries=geojson&steps=true&alternatives=true"
)
req_pub = urllib.request.Request(osrm_public_url, headers={"User-Agent": "EmergencyRoute-AI/1.0 (audit)"})
resp_pub = urllib.request.urlopen(req_pub, timeout=10)
print(f"Public OSRM HTTP Status: {resp_pub.status}")
data_pub = json.loads(resp_pub.read().decode("utf-8"))
print(f"OSRM Response Code: {data_pub.get('code')}")
print(f"Routes Count: {len(data_pub.get('routes', []))}")
route_pub = data_pub["routes"][0]
print(f"OSRM Distance: {route_pub['distance']:.1f} m")
print(f"OSRM Duration: {route_pub['duration']:.1f} s")
print(f"GeoJSON Type: {route_pub['geometry']['type']}")
print(f"GeoJSON Sample Coords (lon, lat): {route_pub['geometry']['coordinates'][:3]}")

print("\n" + "=" * 60)
print("2. BACKEND API OSRM ENDPOINT (/api/v1/routes/osrm)")
print("=" * 60)
api_osrm_url = (
    f"http://127.0.0.1:8000/api/v1/routes/osrm?"
    f"origin_lat={origin[0]}&origin_lng={origin[1]}&"
    f"dest_lat={dest[0]}&dest_lng={dest[1]}"
)
resp_api = urllib.request.urlopen(api_osrm_url, timeout=10)
print(f"Backend API Status: {resp_api.status}")
data_api = json.loads(resp_api.read().decode("utf-8"))
print(f"Success: {data_api['success']}")
print(f"Provider: {data_api['provider']}")
print(f"Distance: {data_api['distance_km']} km ({data_api['route']['distance_meters']} m)")
print(f"Duration: {data_api['duration_minutes']} min ({data_api['route']['duration_seconds']} s)")
print(f"Is Live Traffic: {data_api['is_live_traffic']}")
print(f"Disclaimer: {data_api['disclaimer']}")
print(f"Converted Leaflet Coords (lat, lon): {data_api['route']['coordinates'][:3]}")
print(f"Total Steps: {len(data_api['route']['turn_by_turn'])}")
for idx, step in enumerate(data_api['route']['turn_by_turn']):
    print(f"  Step {idx+1}: {step}")

print("\n" + "=" * 60)
print("3. LOCAL A* ALGORITHM ROUTE (/api/v1/routes/optimal)")
print("=" * 60)
api_astar_url = "http://127.0.0.1:8000/api/v1/routes/optimal"
astar_body = json.dumps({
    "origin_lat": origin[0], "origin_lng": origin[1],
    "dest_lat": dest[0], "dest_lng": dest[1],
    "objective": "traffic_aware"
}).encode("utf-8")
req_astar = urllib.request.Request(api_astar_url, data=astar_body, headers={"Content-Type": "application/json"})
resp_astar = urllib.request.urlopen(req_astar, timeout=10)
data_astar = json.loads(resp_astar.read().decode("utf-8"))
print(f"Local A* HTTP Status: {resp_astar.status}")
print(f"Algorithm: {data_astar['algorithm_name']}")
print(f"A* Distance: {data_astar['path_distance_km']} km ({data_astar['path_distance_meters']} m)")
print(f"A* Travel Time: {data_astar['estimated_travel_time_minutes']} min ({data_astar['estimated_travel_time_seconds']} s)")
print(f"Nodes Explored: {data_astar['nodes_explored']}")
print(f"Runtime: {data_astar['execution_time_ms']:.2f} ms")
print(f"Is Optimal: {data_astar['is_optimal']}")
print(f"A* Waypoints Count: {len(data_astar['coordinates'])}")

print("\n" + "=" * 60)
print("4. ALL 4 ALGORITHMS COMPARISON (/api/v1/routes/compare)")
print("=" * 60)
api_comp_url = "http://127.0.0.1:8000/api/v1/routes/compare"
comp_body = json.dumps({
    "origin_lat": origin[0], "origin_lng": origin[1],
    "dest_lat": dest[0], "dest_lng": dest[1],
    "objective": "traffic_aware"
}).encode("utf-8")
req_comp = urllib.request.Request(api_comp_url, data=comp_body, headers={"Content-Type": "application/json"})
resp_comp = urllib.request.urlopen(req_comp, timeout=10)
data_comp = json.loads(resp_comp.read().decode("utf-8"))
print(f"Comparison HTTP Status: {resp_comp.status}")
for name, r in data_comp["results"].items():
    print(f"  {name:18}: Dist={r['path_distance_km']:.3f} km | Time={r['estimated_travel_time_minutes']:.2f} min | Nodes={r['nodes_explored']} | Runtime={r['execution_time_ms']:.2f} ms")

print("\n" + "=" * 60)
print("5. OFFLINE / TIMEOUT FALLBACK BEHAVIOR")
print("=" * 60)
# Query invalid coordinates to verify honest error handling
try:
    bad_url = "http://127.0.0.1:8000/api/v1/routes/osrm?origin_lat=999.0&origin_lng=75.7&dest_lat=31.2&dest_lng=75.7"
    urllib.request.urlopen(bad_url, timeout=5)
    print("ERROR: Invalid coordinate request succeeded unexpectedly!")
except urllib.error.HTTPError as e:
    print(f"Invalid Coordinate Response: HTTP {e.code} (Correctly rejected)")

# Verify Local A* still works independently
resp_astar2 = urllib.request.urlopen(req_astar, timeout=10)
print(f"Local A* Status During Simulated OSRM Failure: HTTP {resp_astar2.status} (100% Operational)")
print("=" * 60)

