import React, { useState } from 'react';
import {
  Activity,
  BarChart3,
  CheckCircle2,
  Cpu,
  Info,
  Play,
  Zap,
} from 'lucide-react';
import { PhagwaraMap } from '../components/maps/PhagwaraMap';
import { api } from '../services/api';
import {
  AlgorithmComparisonSummary,
  AlgorithmResult,
  OSRMRouteResponse,
} from '../types';

export const RoutePerformance: React.FC = () => {
  const [originCoords, setOriginCoords] = useState<[number, number]>([31.2260, 75.7790]); // Model Town
  const [destCoords, setDestCoords] = useState<[number, number]>([31.2223, 75.7672]); // Civil Hospital
  const [loading, setLoading] = useState(false);
  const [comparisonSummary, setComparisonSummary] = useState<AlgorithmComparisonSummary | null>(null);
  const [osrmRoute, setOsrmRoute] = useState<OSRMRouteResponse | null>(null);

  const handleRunBenchmark = async () => {
    setLoading(true);
    try {
      const [compRes, osrmRes] = await Promise.all([
        api.compareRoutes({
          origin_lat: originCoords[0],
          origin_lng: originCoords[1],
          dest_lat: destCoords[0],
          dest_lng: destCoords[1],
          objective: 'traffic_aware',
        }),
        api.getOSRMRoute(originCoords[0], originCoords[1], destCoords[0], destCoords[1]).catch(() => null),
      ]);
      setComparisonSummary(compRes);
      setOsrmRoute(osrmRes);
    } catch (err) {
      console.error('Error running performance benchmarks:', err);
    } finally {
      setLoading(false);
    }
  };

  const results = comparisonSummary?.results;

  return (
    <div className="flex-1 flex flex-col lg:flex-row h-full overflow-hidden bg-[#FAF8F4] text-[#1E1E1C]">
      {/* Left Benchmark & Heuristic Panel (Light Background) */}
      <div className="w-full lg:w-[460px] p-5 bg-white border-r border-[#D8CBB3]/50 flex flex-col gap-4 overflow-y-auto z-10 shadow-lg">
        {/* Header HUD */}
        <div className="pb-3 border-b border-[#D8CBB3]/30">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-xl bg-[#2B6BFF] flex items-center justify-center text-white shadow-md shadow-[#2B6BFF]/30">
                <BarChart3 className="w-4 h-4 fill-white" />
              </div>
              <div>
                <h2 className="text-base font-extrabold text-[#1E1E1C] tracking-wide ">
                  ALGORITHM AUDIT
                </h2>
                <span className="text-[10px]  text-[#2B6BFF] uppercase tracking-wider font-bold">
                  Heuristic Benchmark Suite
                </span>
              </div>
            </div>
            <span className="px-2.5 py-0.5 text-[9px]  font-bold bg-[#FAF8F4] text-[#1E1E1C]/80 border border-[#D8CBB3]/60 rounded-full">
              PHAGWARA
            </span>
          </div>
          <p className="text-xs text-[#1E1E1C]/65 mt-2 leading-relaxed">
            Audit runtime latency, explored vertex counts, and distance metrics across 5 routing implementations.
          </p>
        </div>

        {/* Algorithm Heuristic Cards */}
        <div className="flex flex-col gap-2.5">
          <span className="text-[10px]  font-bold uppercase tracking-wider text-[#1E1E1C]/60">
            ENGINE HEURISTICS AUDIT
          </span>

          {/* A* */}
          <div className="p-3.5 bg-blue-50/50 border border-[#2B6BFF]/30 rounded-2xl text-xs flex flex-col gap-1 shadow-2xs">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-[#2B6BFF] animate-pulse"></span>
                <strong className="text-[#1E1E1C] font-bold ">A* (Emergency AI Route)</strong>
              </div>
              <span className="px-1.5 py-0.5 text-[8px]  font-bold rounded bg-[#2B6BFF]/20 text-[#2B6BFF] border border-[#2B6BFF]/30">
                OPTIMAL
              </span>
            </div>
            <p className="text-[#1E1E1C]/70 leading-relaxed  text-[11px]">
              Combines edge costs with Euclidean distance heuristics. Guaranteed optimal emergency path.
            </p>
          </div>

          {/* BFS */}
          <div className="p-3.5 bg-[#FAF8F4] border border-[#D8CBB3]/50 rounded-2xl text-xs flex flex-col gap-1">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-[#1E1E1C]"></span>
                <strong className="text-[#1E1E1C] font-bold ">BFS (Breadth-First Search)</strong>
              </div>
              <span className="px-1.5 py-0.5 text-[8px]  font-bold rounded bg-[#D8CBB3]/30 text-[#1E1E1C]">
                HOPS
              </span>
            </div>
            <p className="text-[#1E1E1C]/65 leading-relaxed  text-[11px]">
              Explores vertex frontier by edge hop depth. Ignores metric distance weights.
            </p>
          </div>

          {/* Greedy Best-First */}
          <div className="p-3.5 bg-[#FAF8F4] border border-[#D8CBB3]/50 rounded-2xl text-xs flex flex-col gap-1">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-[#1E1E1C]/60"></span>
                <strong className="text-[#1E1E1C] font-bold ">Greedy Best-First</strong>
              </div>
              <span className="px-1.5 py-0.5 text-[8px]  font-bold rounded bg-[#D8CBB3]/30 text-[#1E1E1C]">
                HEURISTIC
              </span>
            </div>
            <p className="text-[#1E1E1C]/65 leading-relaxed  text-[11px]">
              Directs traversal toward destination coordinate estimate without path accumulation.
            </p>
          </div>

          {/* DFS */}
          <div className="p-3.5 bg-[#FAF8F4] border border-[#D8CBB3]/50 rounded-2xl text-xs flex flex-col gap-1">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-[#1E1E1C]/40"></span>
                <strong className="text-[#1E1E1C] font-bold ">DFS (Depth-First Search)</strong>
              </div>
              <span className="px-1.5 py-0.5 text-[8px]  font-bold rounded bg-[#D8CBB3]/30 text-[#1E1E1C]">
                EXHAUSTIVE
              </span>
            </div>
            <p className="text-[#1E1E1C]/65 leading-relaxed  text-[11px]">
              Explores deepest branches first. Demonstrates non-heuristic worst-case graph search.
            </p>
          </div>
        </div>

        {/* Benchmark Runner Controls */}
        <div className="p-4 bg-[#FAF8F4] border border-[#D8CBB3]/50 rounded-2xl flex flex-col gap-3 shadow-2xs">
          <div className="flex items-center justify-between  text-xs">
            <span className="text-[#1E1E1C] font-bold">Standard Sector Test</span>
            <span className="text-[#2B6BFF] text-[10px] font-bold">Model Town &rarr; Civil Hospital</span>
          </div>

          <button
            onClick={handleRunBenchmark}
            disabled={loading}
            className="w-full py-3 bg-[#2B6BFF] hover:bg-[#1A55E0] text-white  font-bold text-xs rounded-xl shadow-lg shadow-[#2B6BFF]/30 transition-all active:scale-95 disabled:opacity-50 cursor-pointer flex items-center justify-center gap-2"
          >
            {loading ? (
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
            ) : (
              <>
                <Zap className="w-3.5 h-3.5 fill-white" />
                <span>EXECUTE HEURISTIC BENCHMARKS</span>
              </>
            )}
          </button>
        </div>

        {/* Benchmark Results Table */}
        {results && (
          <div className="flex flex-col gap-2 mt-1">
            <span className="text-[10px]  font-bold uppercase tracking-wider text-[#1E1E1C]/60">
              BENCHMARK TELEMETRY RESULTS
            </span>

            <div className="border border-[#D8CBB3]/50 rounded-2xl overflow-hidden text-xs bg-white shadow-sm">
              <table className="w-full text-left ">
                <thead className="bg-[#FAF8F4] border-b border-[#D8CBB3]/30 text-[#1E1E1C]/60 font-bold text-[10px]">
                  <tr>
                    <th className="p-2.5">ENGINE</th>
                    <th className="p-2.5">KM</th>
                    <th className="p-2.5">MIN</th>
                    <th className="p-2.5">NODES</th>
                    <th className="p-2.5">LATENCY</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#D8CBB3]/20">
                  {/* A* */}
                  {results.A_Star && (
                    <tr className="bg-blue-50/40">
                      <td className="p-2.5 font-bold text-[#2B6BFF] flex items-center gap-1.5">
                        <span className="w-2 h-2 rounded-full bg-[#2B6BFF]"></span>
                        A* AI
                      </td>
                      <td className="p-2.5 font-semibold text-[#1E1E1C]">{results.A_Star.path_distance_km}</td>
                      <td className="p-2.5 text-[#2B6BFF] font-bold">{results.A_Star.estimated_travel_time_minutes}m</td>
                      <td className="p-2.5 text-[#1E1E1C]/60">{results.A_Star.nodes_explored}</td>
                      <td className="p-2.5 text-[#2B6BFF] font-bold">{results.A_Star.execution_time_ms.toFixed(1)}ms</td>
                    </tr>
                  )}

                  {/* BFS */}
                  {results.BFS && (
                    <tr>
                      <td className="p-2.5 font-semibold text-[#1E1E1C] flex items-center gap-1.5">
                        <span className="w-2 h-2 rounded-full bg-[#1E1E1C]"></span>
                        BFS
                      </td>
                      <td className="p-2.5 text-[#1E1E1C]">{results.BFS.path_distance_km}</td>
                      <td className="p-2.5 text-[#1E1E1C]">{results.BFS.estimated_travel_time_minutes}m</td>
                      <td className="p-2.5 text-[#1E1E1C]/60">{results.BFS.nodes_explored}</td>
                      <td className="p-2.5 text-[#1E1E1C]/60">{results.BFS.execution_time_ms.toFixed(1)}ms</td>
                    </tr>
                  )}

                  {/* Greedy Best-First */}
                  {results.Greedy_Best_First && (
                    <tr>
                      <td className="p-2.5 font-semibold text-[#1E1E1C]/80 flex items-center gap-1.5">
                        <span className="w-2 h-2 rounded-full bg-[#1E1E1C]/60"></span>
                        Greedy
                      </td>
                      <td className="p-2.5 text-[#1E1E1C]">{results.Greedy_Best_First.path_distance_km}</td>
                      <td className="p-2.5 text-[#1E1E1C]">{results.Greedy_Best_First.estimated_travel_time_minutes}m</td>
                      <td className="p-2.5 text-[#1E1E1C]/60">{results.Greedy_Best_First.nodes_explored}</td>
                      <td className="p-2.5 text-[#1E1E1C]/60">{results.Greedy_Best_First.execution_time_ms.toFixed(1)}ms</td>
                    </tr>
                  )}

                  {/* DFS */}
                  {results.DFS && (
                    <tr>
                      <td className="p-2.5 font-semibold text-[#1E1E1C]/60 flex items-center gap-1.5">
                        <span className="w-2 h-2 rounded-full bg-[#1E1E1C]/40"></span>
                        DFS
                      </td>
                      <td className="p-2.5 text-[#1E1E1C]">{results.DFS.path_distance_km}</td>
                      <td className="p-2.5 text-[#1E1E1C]">{results.DFS.estimated_travel_time_minutes}m</td>
                      <td className="p-2.5 text-[#1E1E1C]/60">{results.DFS.nodes_explored}</td>
                      <td className="p-2.5 text-[#1E1E1C]/60">{results.DFS.execution_time_ms.toFixed(1)}ms</td>
                    </tr>
                  )}

                  {/* OSRM External */}
                  {osrmRoute?.success && osrmRoute.route && (
                    <tr className="bg-[#FAF8F4]">
                      <td className="p-2.5 font-bold text-[#1E1E1C] flex items-center gap-1.5">
                        <span className="w-2 h-2 rounded-full bg-[#1E1E1C]"></span>
                        OSRM
                      </td>
                      <td className="p-2.5 font-semibold text-[#1E1E1C]">{osrmRoute.route.distance_km}</td>
                      <td className="p-2.5 text-[#1E1E1C] font-bold">{osrmRoute.route.duration_minutes}m</td>
                      <td className="p-2.5 text-[#1E1E1C]/40">Ext</td>
                      <td className="p-2.5 text-[#1E1E1C]/40">HTTP</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            <p className="text-[10px] text-[#1E1E1C]/50 mt-1 ">
              Tested on authoritative Phagwara graph (3,975 nodes, 10,229 edges).
            </p>
          </div>
        )}
      </div>

      {/* Right Map Viewport (Default Dark) */}
      <div className="flex-1 h-full relative">
        <PhagwaraMap
          activeRoute={results?.A_Star}
          comparisonRoutes={results}
          osrmRoute={osrmRoute}
          routeMode="compare_both"
          selectedOrigin={originCoords}
          selectedDestination={destCoords}
        />
      </div>
    </div>
  );
};
