import React, { useEffect, useState } from 'react';
import {
  Activity,
  AlertTriangle,
  ArrowRightLeft,
  BarChart2,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Clock,
  Compass,
  Crosshair,
  Layers,
  MapPin,
  Navigation,
  Play,
  RotateCcw,
  ShieldCheck,
  Sparkles,
  Zap,
} from 'lucide-react';
import { PhagwaraMap } from '../components/maps/PhagwaraMap';
import { api } from '../services/api';
import { tomtomService } from '../services/tomtom';
import {
  AlgorithmComparisonSummary,
  AlgorithmResult,
  EmergencyIncident,
  OSRMRouteResponse,
  SystemHealth,
} from '../types';

interface PresetLandmark {
  name: string;
  coords: [number, number];
  category: string;
}

const PRESET_DESTINATIONS: PresetLandmark[] = [
  { name: 'Civil Hospital (Emergency)', coords: [31.2223, 75.7672], category: 'Hospital' },
  { name: 'Guru Nanak Hospital', coords: [31.2201, 75.7820], category: 'Healthcare' },
  { name: 'Phagwara Junction Station', coords: [31.2185, 75.7725], category: 'Transit' },
  { name: 'Central Bus Stand', coords: [31.2215, 75.7738], category: 'Transit' },
  { name: 'LPU Main Gate', coords: [31.2536, 75.7037], category: 'Campus' },
];

const PRESET_ORIGINS: PresetLandmark[] = [
  { name: 'Model Town Phagwara', coords: [31.2260, 75.7790], category: 'Residential' },
  { name: 'Hanumangarh Chowk', coords: [31.2241, 75.7695], category: 'Intersection' },
  { name: 'Hadiabad Chowk', coords: [31.2140, 75.7480], category: 'Commercial' },
  { name: 'GT Road Bypass', coords: [31.2310, 75.7850], category: 'Highway' },
];

interface DashboardProps {
  onNavigateTab: (tab: string) => void;
}

export const Dashboard: React.FC<DashboardProps> = ({ onNavigateTab }) => {
  // Waypoint State
  const [originCoords, setOriginCoords] = useState<[number, number]>([31.2260, 75.7790]);
  const [originName, setOriginName] = useState('Model Town Phagwara');
  const [destCoords, setDestCoords] = useState<[number, number]>([31.2223, 75.7672]);
  const [destName, setDestName] = useState('Civil Hospital (Emergency)');

  // Map Click Picking Mode ('none' | 'origin' | 'destination')
  const [pickMode, setPickMode] = useState<'none' | 'origin' | 'destination'>('none');

  // Automatic Multi-Algorithm Routing State
  const [comparisonSummary, setComparisonSummary] = useState<AlgorithmComparisonSummary | null>(null);
  const [osrmRoute, setOsrmRoute] = useState<OSRMRouteResponse | null>(null);
  const [activeAlgorithmKey, setActiveAlgorithmKey] = useState<string>('A_Star');
  const [calculating, setCalculating] = useState(false);
  const [showBenchmarkTable, setShowBenchmarkTable] = useState(false);

  // Background Telemetry
  const [isTomTomActive, setIsTomTomActive] = useState(tomtomService.isConfigured());

  // Function to automatically run ALL algorithms in parallel
  const calculateAllAlgorithms = async (orig = originCoords, dest = destCoords) => {
    setCalculating(true);
    try {
      const [compRes, osrmRes] = await Promise.all([
        api.compareRoutes({
          origin_lat: orig[0],
          origin_lng: orig[1],
          dest_lat: dest[0],
          dest_lng: dest[1],
          objective: 'traffic_aware',
        }).catch((err) => {
          console.warn('compareRoutes failed:', err);
          return null;
        }),
        api.getOSRMRoute(orig[0], orig[1], dest[0], dest[1]).catch((err) => {
          console.warn('getOSRMRoute failed:', err);
          return null;
        }),
      ]);

      if (compRes && compRes.results) {
        setComparisonSummary(compRes);
        setActiveAlgorithmKey('A_Star');
      }
      if (osrmRes) {
        setOsrmRoute(osrmRes);
      }
    } catch (err) {
      console.error('Multi-algorithm calculation error:', err);
    } finally {
      setCalculating(false);
    }
  };

  // On mount: trigger initial multi-algorithm route calculation immediately
  useEffect(() => {
    tomtomService.fetchStatus().then(setIsTomTomActive).catch(() => false);
    calculateAllAlgorithms(originCoords, destCoords);
  }, []);

  const handleSwapPoints = () => {
    const tempCoords = originCoords;
    const tempName = originName;
    setOriginCoords(destCoords);
    setOriginName(destName);
    setDestCoords(tempCoords);
    setDestName(tempName);
    calculateAllAlgorithms(destCoords, tempCoords);
  };

  const handleSelectDestination = (landmark: PresetLandmark) => {
    setDestCoords(landmark.coords);
    setDestName(landmark.name);
    calculateAllAlgorithms(originCoords, landmark.coords);
  };

  const handleSelectOrigin = (landmark: PresetLandmark) => {
    setOriginCoords(landmark.coords);
    setOriginName(landmark.name);
    calculateAllAlgorithms(landmark.coords, destCoords);
  };

  const aStarResult = comparisonSummary?.results?.['A_Star'];
  const greedyResult = comparisonSummary?.results?.['Greedy_Best_First'];
  const bfsResult = comparisonSummary?.results?.['BFS'];
  const dfsResult = comparisonSummary?.results?.['DFS'];

  // Primary active route for spotlight on map
  const currentActiveRoute =
    activeAlgorithmKey === 'OSRM'
      ? null
      : comparisonSummary?.results?.[activeAlgorithmKey] || aStarResult || null;

  // Selected route stats
  const activeTravelTime =
    activeAlgorithmKey === 'OSRM'
      ? osrmRoute?.route?.duration_minutes
      : currentActiveRoute?.estimated_travel_time_minutes ?? aStarResult?.estimated_travel_time_minutes;

  const activeDistance =
    activeAlgorithmKey === 'OSRM'
      ? osrmRoute?.route?.distance_km
      : currentActiveRoute?.path_distance_km ?? aStarResult?.path_distance_km;

  return (
    <div className="relative w-full h-full min-h-[calc(100vh-80px)] flex flex-col bg-[#1E1E1C] overflow-hidden select-none font-sans">
      {/* ============================================================ */}
      {/* 1. TOP FLOATING SEARCH & ROUTE CAPSULE (Clean, Human Design) */}
      {/* ============================================================ */}
      <div className="absolute top-4 left-1/2 -translate-x-1/2 z-30 w-[94%] max-w-4xl pointer-events-none">
        <div className="pointer-events-auto bg-[#1E1E1C]/92 backdrop-blur-xl border border-[#D8CBB3]/30 rounded-2xl p-3 sm:p-3.5 shadow-2xl text-[#D8CBB3] flex flex-col gap-2.5">
          {/* Main Route Inputs */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-2">
            {/* Origin & Destination Inputs */}
            <div className="flex items-center gap-2 w-full sm:flex-1">
              {/* Start Location */}
              <div className="relative flex-1">
                <div className="flex items-center gap-2 bg-[#282826] border border-[#D8CBB3]/20 rounded-xl px-3 py-2 text-xs">
                  <span className="w-2 h-2 rounded-full bg-[#2B6BFF] shrink-0" />
                  <select
                    value={originName}
                    onChange={(e) => {
                      const found = PRESET_ORIGINS.find((o) => o.name === e.target.value);
                      if (found) handleSelectOrigin(found);
                    }}
                    className="bg-transparent text-[#D8CBB3] font-medium text-xs focus:outline-none cursor-pointer w-full truncate"
                  >
                    {PRESET_ORIGINS.map((o) => (
                      <option key={o.name} value={o.name} className="bg-[#1E1E1C] text-[#D8CBB3]">
                        {o.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Swap Button */}
              <button
                onClick={handleSwapPoints}
                title="Swap Start and Destination"
                className="w-8 h-8 rounded-full bg-[#282826] hover:bg-[#383834] border border-[#D8CBB3]/30 flex items-center justify-center text-[#D8CBB3]/80 hover:text-white shrink-0 transition-transform active:rotate-180 cursor-pointer"
              >
                <ArrowRightLeft className="w-3.5 h-3.5" />
              </button>

              {/* Destination */}
              <div className="relative flex-1">
                <div className="flex items-center gap-2 bg-[#282826] border border-[#D8CBB3]/20 rounded-xl px-3 py-2 text-xs">
                  <span className="w-2 h-2 rounded-full bg-rose-500 shrink-0" />
                  <select
                    value={destName}
                    onChange={(e) => {
                      const found = PRESET_DESTINATIONS.find((d) => d.name === e.target.value);
                      if (found) handleSelectDestination(found);
                    }}
                    className="bg-transparent text-[#D8CBB3] font-medium text-xs focus:outline-none cursor-pointer w-full truncate"
                  >
                    {PRESET_DESTINATIONS.map((d) => (
                      <option key={d.name} value={d.name} className="bg-[#1E1E1C] text-[#D8CBB3]">
                        {d.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>

            {/* Action Buttons: Pick On Map & Refresh */}
            <div className="flex items-center gap-2 w-full sm:w-auto shrink-0 justify-end">
              <button
                onClick={() => setPickMode(pickMode === 'none' ? 'origin' : 'none')}
                className={`px-3 py-2 rounded-xl text-xs font-medium border transition-all cursor-pointer flex items-center gap-1.5 ${
                  pickMode !== 'none'
                    ? 'bg-[#2B6BFF] text-white border-[#2B6BFF] shadow-sm'
                    : 'bg-[#282826] hover:bg-[#383834] text-[#D8CBB3]/90 border-[#D8CBB3]/20'
                }`}
              >
                <Crosshair className="w-3.5 h-3.5" />
                <span>
                  {pickMode === 'origin'
                    ? 'Click Start on Map'
                    : pickMode === 'destination'
                    ? 'Click Destination'
                    : 'Pick on Map'}
                </span>
              </button>

              <button
                onClick={() => calculateAllAlgorithms(originCoords, destCoords)}
                disabled={calculating}
                className="px-4 py-2 bg-[#2B6BFF] hover:bg-[#1A55E0] text-white font-medium text-xs rounded-xl shadow-md transition-all active:scale-95 cursor-pointer flex items-center gap-1.5"
              >
                {calculating ? (
                  <>
                    <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    <span>Routing...</span>
                  </>
                ) : (
                  <>
                    <Navigation className="w-3.5 h-3.5 fill-white" />
                    <span>Find Route</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Quick Target Chips */}
          <div className="flex items-center gap-1.5 overflow-x-auto text-xs no-scrollbar">
            <span className="text-[#D8CBB3]/50 text-[11px] shrink-0 font-medium">
              Quick Destination:
            </span>
            {PRESET_DESTINATIONS.map((dest) => (
              <button
                key={dest.name}
                onClick={() => handleSelectDestination(dest)}
                className={`px-2.5 py-1 rounded-lg whitespace-nowrap transition-all cursor-pointer border text-[11px] ${
                  destName === dest.name
                    ? 'bg-[#2B6BFF]/20 text-[#2B6BFF] border-[#2B6BFF] font-semibold'
                    : 'bg-[#282826]/70 hover:bg-[#282826] text-[#D8CBB3]/80 border-[#D8CBB3]/15'
                }`}
              >
                {dest.name}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* ============================================================ */}
      {/* 2. THE MAP: CENTERPIECE (Clean, High-Tech, Uncluttered)       */}
      {/* ============================================================ */}
      <div className="w-full h-full relative z-0">
        <PhagwaraMap
          selectedOrigin={originCoords}
          selectedDestination={destCoords}
          onOriginChange={(lat, lng) => {
            setOriginCoords([lat, lng]);
            calculateAllAlgorithms([lat, lng], destCoords);
          }}
          onDestinationChange={(lat, lng) => {
            setDestCoords([lat, lng]);
            calculateAllAlgorithms(originCoords, [lat, lng]);
          }}
          onSelectCoordinate={(lat, lng) => {
            if (pickMode === 'origin') {
              setOriginCoords([lat, lng]);
              setPickMode('destination');
              calculateAllAlgorithms([lat, lng], destCoords);
            } else if (pickMode === 'destination') {
              setDestCoords([lat, lng]);
              setPickMode('none');
              calculateAllAlgorithms(originCoords, [lat, lng]);
            }
          }}
          pickMode={pickMode}
          activeRoute={currentActiveRoute}
          comparisonRoutes={comparisonSummary?.results || null}
          osrmRoute={osrmRoute}
          routeMode={activeAlgorithmKey === 'OSRM' ? 'osrm' : 'compare_both'}
        />
      </div>

      {/* ============================================================ */}
      {/* 3. HUMAN NAVIGATION CARD & BENCHMARK AUDIT (Bottom Center)    */}
      {/* ============================================================ */}
      <div className="absolute bottom-4 left-1/2 -translate-x-1/2 z-30 w-[94%] max-w-4xl pointer-events-none">
        <div className="pointer-events-auto bg-[#1E1E1C]/95 backdrop-blur-2xl border border-[#D8CBB3]/30 rounded-2xl p-4 shadow-2xl text-[#D8CBB3] flex flex-col gap-3 transition-all">
          {/* Main Route Summary Banner */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="w-11 h-11 rounded-xl bg-[#2B6BFF]/15 border border-[#2B6BFF]/30 flex items-center justify-center text-[#2B6BFF] shrink-0">
                <Navigation className="w-5 h-5 fill-[#2B6BFF]" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xl font-bold text-white tracking-tight">
                    {activeTravelTime ? `${activeTravelTime} min` : '-- min'}
                  </span>
                  <span className="text-xs text-[#D8CBB3]/60 font-medium">
                    ({activeDistance ? `${activeDistance} km` : '-- km'})
                  </span>
                  <span className="px-2 py-0.5 text-[10px] font-semibold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 rounded-full">
                    Fastest Route
                  </span>
                </div>
                <p className="text-xs text-[#D8CBB3]/70 mt-0.5">
                  Direct emergency corridor via Phagwara arterial &bull; Dynamic traffic &amp; closure avoidance
                </p>
              </div>
            </div>

            {/* Toggle Benchmark Data */}
            <div className="flex items-center gap-2 self-end sm:self-center">
              <button
                onClick={() => setShowBenchmarkTable(!showBenchmarkTable)}
                className="px-3 py-1.5 bg-[#282826] hover:bg-[#333330] border border-[#D8CBB3]/25 text-xs text-[#D8CBB3] font-medium rounded-xl transition-all cursor-pointer flex items-center gap-1.5 shadow-sm"
              >
                <BarChart2 className="w-3.5 h-3.5 text-[#2B6BFF]" />
                <span>Algorithm Audit (5 Engines)</span>
                {showBenchmarkTable ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronUp className="w-3.5 h-3.5" />}
              </button>
            </div>
          </div>

          {/* Practical Route Choices (Google / Apple Maps Style) */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-1 border-t border-[#D8CBB3]/15">
            {/* Route 1: A* Optimal AI */}
            <button
              onClick={() => setActiveAlgorithmKey('A_Star')}
              className={`p-2.5 rounded-xl text-left border transition-all cursor-pointer flex items-center justify-between ${
                activeAlgorithmKey === 'A_Star'
                  ? 'bg-[#2B6BFF]/20 border-[#2B6BFF] shadow-xs'
                  : 'bg-[#282826]/70 hover:bg-[#282826] border-[#D8CBB3]/15 text-[#D8CBB3]/80'
              }`}
            >
              <div>
                <div className="flex items-center gap-1.5 text-xs font-bold text-white">
                  <span>A* Emergency AI</span>
                  <span className="px-1.5 py-0.2 text-[9px] bg-[#2B6BFF] text-white rounded font-medium">Optimal</span>
                </div>
                <span className="text-[11px] text-[#D8CBB3]/60">Heuristic traffic-aware</span>
              </div>
              <div className="text-right">
                <span className="text-sm font-bold text-white block">
                  {aStarResult?.estimated_travel_time_minutes ?? '--'} min
                </span>
                <span className="text-[10px] text-[#D8CBB3]/60">
                  {aStarResult?.path_distance_km ?? '--'} km
                </span>
              </div>
            </button>

            {/* Route 2: OSRM Baseline */}
            <button
              onClick={() => setActiveAlgorithmKey('OSRM')}
              className={`p-2.5 rounded-xl text-left border transition-all cursor-pointer flex items-center justify-between ${
                activeAlgorithmKey === 'OSRM'
                  ? 'bg-[#2B6BFF]/20 border-[#2B6BFF] shadow-xs'
                  : 'bg-[#282826]/70 hover:bg-[#282826] border-[#D8CBB3]/15 text-[#D8CBB3]/80'
              }`}
            >
              <div>
                <div className="text-xs font-bold text-white">OSRM Standard</div>
                <span className="text-[11px] text-[#D8CBB3]/60">Public baseline</span>
              </div>
              <div className="text-right">
                <span className="text-sm font-bold text-white block">
                  {osrmRoute?.route?.duration_minutes ?? '--'} min
                </span>
                <span className="text-[10px] text-[#D8CBB3]/60">
                  {osrmRoute?.route?.distance_km ?? '--'} km
                </span>
              </div>
            </button>

            {/* Route 3: Greedy Heuristic Bypass */}
            <button
              onClick={() => setActiveAlgorithmKey('Greedy_Best_First')}
              className={`p-2.5 rounded-xl text-left border transition-all cursor-pointer flex items-center justify-between ${
                activeAlgorithmKey === 'Greedy_Best_First'
                  ? 'bg-[#2B6BFF]/20 border-[#2B6BFF] shadow-xs'
                  : 'bg-[#282826]/70 hover:bg-[#282826] border-[#D8CBB3]/15 text-[#D8CBB3]/80'
              }`}
            >
              <div>
                <div className="text-xs font-bold text-white">Greedy Heuristic</div>
                <span className="text-[11px] text-[#D8CBB3]/60">Alternative bypass</span>
              </div>
              <div className="text-right">
                <span className="text-sm font-bold text-white block">
                  {greedyResult?.estimated_travel_time_minutes ?? '--'} min
                </span>
                <span className="text-[10px] text-[#D8CBB3]/60">
                  {greedyResult?.path_distance_km ?? '--'} km
                </span>
              </div>
            </button>
          </div>

          {/* Professional Engineering Algorithm Benchmark Table (Collapsible) */}
          {showBenchmarkTable && (
            <div className="pt-2 border-t border-[#D8CBB3]/15 flex flex-col gap-2 animate-in fade-in slide-in-from-bottom-2">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="text-[#D8CBB3]/60 border-b border-[#D8CBB3]/15 text-[11px]">
                      <th className="py-1.5 font-medium">Routing Engine</th>
                      <th className="py-1.5 font-medium">Type</th>
                      <th className="py-1.5 font-medium">Travel Time</th>
                      <th className="py-1.5 font-medium">Distance</th>
                      <th className="py-1.5 font-medium">Search Space (Nodes)</th>
                      <th className="py-1.5 font-medium">Latency</th>
                      <th className="py-1.5 font-medium text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#D8CBB3]/10 text-xs">
                    {/* A* */}
                    <tr
                      onClick={() => setActiveAlgorithmKey('A_Star')}
                      className={`hover:bg-white/5 cursor-pointer ${activeAlgorithmKey === 'A_Star' ? 'bg-[#2B6BFF]/10 text-white font-medium' : 'text-[#D8CBB3]/85'}`}
                    >
                      <td className="py-2 flex items-center gap-1.5">
                        <span className="w-2 h-2 rounded-full bg-[#2B6BFF]" />
                        <span>A* Emergency AI</span>
                      </td>
                      <td className="py-2 text-[#D8CBB3]/60">Admissible Heuristic</td>
                      <td className="py-2 font-bold text-white">{aStarResult?.estimated_travel_time_minutes ?? '--'} min</td>
                      <td className="py-2">{aStarResult?.path_distance_km ?? '--'} km</td>
                      <td className="py-2">{aStarResult?.nodes_explored ?? '--'} nodes</td>
                      <td className="py-2">{aStarResult?.execution_time_ms ? `${aStarResult.execution_time_ms.toFixed(2)} ms` : '<1 ms'}</td>
                      <td className="py-2 text-right">
                        <span className="px-2 py-0.5 text-[10px] bg-[#2B6BFF]/20 text-[#2B6BFF] rounded-md font-semibold">
                          Optimal
                        </span>
                      </td>
                    </tr>

                    {/* OSRM */}
                    <tr
                      onClick={() => setActiveAlgorithmKey('OSRM')}
                      className={`hover:bg-white/5 cursor-pointer ${activeAlgorithmKey === 'OSRM' ? 'bg-[#2B6BFF]/10 text-white font-medium' : 'text-[#D8CBB3]/85'}`}
                    >
                      <td className="py-2 flex items-center gap-1.5">
                        <span className="w-2 h-2 rounded-full bg-blue-400" />
                        <span>OSRM Baseline</span>
                      </td>
                      <td className="py-2 text-[#D8CBB3]/60">External Multi-Level Dijkstra</td>
                      <td className="py-2 font-bold text-white">{osrmRoute?.route?.duration_minutes ?? '--'} min</td>
                      <td className="py-2">{osrmRoute?.route?.distance_km ?? '--'} km</td>
                      <td className="py-2">Precomputed Hierarchy</td>
                      <td className="py-2">~120 ms</td>
                      <td className="py-2 text-right">
                        <span className="px-2 py-0.5 text-[10px] bg-white/10 text-[#D8CBB3] rounded-md">
                          Baseline
                        </span>
                      </td>
                    </tr>

                    {/* Greedy Best-First */}
                    <tr
                      onClick={() => setActiveAlgorithmKey('Greedy_Best_First')}
                      className={`hover:bg-white/5 cursor-pointer ${activeAlgorithmKey === 'Greedy_Best_First' ? 'bg-[#2B6BFF]/10 text-white font-medium' : 'text-[#D8CBB3]/85'}`}
                    >
                      <td className="py-2 flex items-center gap-1.5">
                        <span className="w-2 h-2 rounded-full bg-amber-400" />
                        <span>Greedy Best-First</span>
                      </td>
                      <td className="py-2 text-[#D8CBB3]/60">Pure Heuristic Greedy</td>
                      <td className="py-2 font-bold text-white">{greedyResult?.estimated_travel_time_minutes ?? '--'} min</td>
                      <td className="py-2">{greedyResult?.path_distance_km ?? '--'} km</td>
                      <td className="py-2">{greedyResult?.nodes_explored ?? '--'} nodes</td>
                      <td className="py-2">{greedyResult?.execution_time_ms ? `${greedyResult.execution_time_ms.toFixed(2)} ms` : '<1 ms'}</td>
                      <td className="py-2 text-right">
                        <span className="px-2 py-0.5 text-[10px] bg-amber-500/20 text-amber-300 rounded-md">
                          Fast
                        </span>
                      </td>
                    </tr>

                    {/* BFS */}
                    <tr
                      onClick={() => setActiveAlgorithmKey('BFS')}
                      className={`hover:bg-white/5 cursor-pointer ${activeAlgorithmKey === 'BFS' ? 'bg-[#2B6BFF]/10 text-white font-medium' : 'text-[#D8CBB3]/85'}`}
                    >
                      <td className="py-2 flex items-center gap-1.5">
                        <span className="w-2 h-2 rounded-full bg-cyan-400" />
                        <span>BFS (Breadth-First)</span>
                      </td>
                      <td className="py-2 text-[#D8CBB3]/60">Unweighted Hop-Count</td>
                      <td className="py-2 font-bold text-white">{bfsResult?.estimated_travel_time_minutes ?? '--'} min</td>
                      <td className="py-2">{bfsResult?.path_distance_km ?? '--'} km</td>
                      <td className="py-2">{bfsResult?.nodes_explored ?? '--'} nodes</td>
                      <td className="py-2">{bfsResult?.execution_time_ms ? `${bfsResult.execution_time_ms.toFixed(2)} ms` : '<1 ms'}</td>
                      <td className="py-2 text-right">
                        <span className="px-2 py-0.5 text-[10px] bg-cyan-500/20 text-cyan-300 rounded-md">
                          Fewest Hops
                        </span>
                      </td>
                    </tr>

                    {/* DFS */}
                    <tr
                      onClick={() => setActiveAlgorithmKey('DFS')}
                      className={`hover:bg-white/5 cursor-pointer ${activeAlgorithmKey === 'DFS' ? 'bg-[#2B6BFF]/10 text-white font-medium' : 'text-[#D8CBB3]/85'}`}
                    >
                      <td className="py-2 flex items-center gap-1.5">
                        <span className="w-2 h-2 rounded-full bg-purple-400" />
                        <span>DFS (Depth-First)</span>
                      </td>
                      <td className="py-2 text-[#D8CBB3]/60">Exhaustive Branch Search</td>
                      <td className="py-2 font-bold text-white">{dfsResult?.estimated_travel_time_minutes ?? '--'} min</td>
                      <td className="py-2">{dfsResult?.path_distance_km ?? '--'} km</td>
                      <td className="py-2">{dfsResult?.nodes_explored ?? '--'} nodes</td>
                      <td className="py-2">{dfsResult?.execution_time_ms ? `${dfsResult.execution_time_ms.toFixed(2)} ms` : '<1 ms'}</td>
                      <td className="py-2 text-right">
                        <span className="px-2 py-0.5 text-[10px] bg-purple-500/20 text-purple-300 rounded-md">
                          Unbounded
                        </span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <div className="flex items-center justify-between text-[11px] text-[#D8CBB3]/60 pt-1 border-t border-[#D8CBB3]/10">
                <span>
                  Click any row to spotlight that algorithm's trajectory on the map.
                </span>
                <button
                  onClick={() => onNavigateTab('route-performance')}
                  className="text-[#2B6BFF] hover:underline font-semibold"
                >
                  View Full Benchmark Suite &rarr;
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
