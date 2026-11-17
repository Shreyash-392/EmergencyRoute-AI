import React, { useEffect, useState } from 'react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { BarChart3, Cpu, Filter, Info } from 'lucide-react';
import { api } from '../services/api';
import { AlgorithmComparisonSummary } from '../types';

export const AlgorithmComparison: React.FC = () => {
  const [metricObjective, setMetricObjective] = useState<'travel_time' | 'distance'>('travel_time');
  const [summary, setSummary] = useState<AlgorithmComparisonSummary | null>(null);
  const [loading, setLoading] = useState(false);

  // Model Town -> Civil Hospital Phagwara
  const fetchBenchmark = async (obj: 'travel_time' | 'distance') => {
    setLoading(true);
    try {
      const data = await api.compareRoutes({
        origin_lat: 31.2260,
        origin_lng: 75.7790,
        dest_lat: 31.2223,
        dest_lng: 75.7672,
        objective: obj,
      });
      setSummary(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBenchmark(metricObjective);
  }, [metricObjective]);

  const chartData = summary
    ? Object.entries(summary.results).map(([key, res]) => ({
        algorithm: key.replace('_', ' '),
        travelTimeMin: res.estimated_travel_time_minutes,
        nodesExplored: res.nodes_explored,
        runtimeMs: res.execution_time_ms,
        distanceKm: res.path_distance_km,
      }))
    : [];

  return (
    <div className="flex-1 p-6 bg-slate-50 flex flex-col gap-6 overflow-y-auto">
      {/* Header & Metric Selector */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 text-[10px] font-bold uppercase rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
              OSM DATA
            </span>
            <span className="text-xs text-slate-500 font-medium">Phagwara Road MultiDiGraph</span>
          </div>
          <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2.5 mt-1">
            <Cpu className="w-6 h-6 text-blue-600" />
            <span>Routing Engine Algorithmic Benchmarks</span>
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Empirical runtime, node exploration, and travel-time comparisons executed directly on the actual Phagwara OpenStreetMap graph (3,975 nodes, 10,229 edges).
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-slate-400" />
          <span className="text-xs text-slate-600 font-medium">Optimization Cost:</span>
          <select
            value={metricObjective}
            onChange={(e) => setMetricObjective(e.target.value as any)}
            className="bg-white border border-slate-200 text-xs text-slate-800 rounded-xl px-3 py-2 shadow-2xs focus:outline-none focus:border-blue-500"
          >
            <option value="travel_time">Travel Time (OSM Legal Speeds)</option>
            <option value="distance">Shortest Road Distance (OSM Length)</option>
          </select>
        </div>
      </div>

      {/* Visual Analytics Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Chart 1: Travel Time */}
        <div className="p-5 bg-white border border-slate-200/90 rounded-2xl shadow-xs flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-blue-600" />
              <span>Calculated Travel Time (Minutes)</span>
            </h3>
            <span className="text-[10px] text-emerald-700 font-semibold bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
              Lower is Better
            </span>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="algorithm" stroke="#64748b" fontSize={11} tickLine={false} />
                <YAxis stroke="#64748b" fontSize={11} tickLine={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#ffffff', borderColor: '#e2e8f0', borderRadius: '12px', fontSize: '11px', boxShadow: '0 4px 12px rgba(0,0,0,0.06)' }}
                />
                <Bar dataKey="travelTimeMin" fill="#2563eb" name="Travel Time (min)" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 2: Search Efficiency (Nodes Explored) */}
        <div className="p-5 bg-white border border-slate-200/90 rounded-2xl shadow-xs flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-2">
              <Cpu className="w-4 h-4 text-indigo-600" />
              <span>Nodes Explored (Search Space Pruning)</span>
            </h3>
            <span className="text-[10px] text-blue-700 font-semibold bg-blue-50 px-2 py-0.5 rounded-full border border-blue-200">
              Search Efficiency
            </span>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="algorithm" stroke="#64748b" fontSize={11} tickLine={false} />
                <YAxis stroke="#64748b" fontSize={11} tickLine={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#ffffff', borderColor: '#e2e8f0', borderRadius: '12px', fontSize: '11px', boxShadow: '0 4px 12px rgba(0,0,0,0.06)' }}
                />
                <Bar dataKey="nodesExplored" fill="#6366f1" name="Nodes Explored" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Comparison Table */}
      <div className="p-5 bg-white border border-slate-200/90 rounded-2xl shadow-xs flex flex-col gap-4">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-2">
          <span>Authoritative Metrics Comparison Table</span>
        </h3>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-200 text-slate-500 font-semibold text-[11px] bg-slate-50/70">
                <th className="py-3 px-3 rounded-l-xl">Algorithm</th>
                <th className="py-3 px-3">Optimality Status</th>
                <th className="py-3 px-3">Distance (km)</th>
                <th className="py-3 px-3">Est. Travel Time</th>
                <th className="py-3 px-3">Nodes Explored</th>
                <th className="py-3 px-3">Execution Time</th>
                <th className="py-3 px-3 rounded-r-xl">Guarantees</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {summary &&
                Object.entries(summary.results).map(([key, res]) => (
                  <tr key={key} className="hover:bg-slate-50/60 transition-colors">
                    <td className="py-3.5 px-3 font-bold text-slate-900 flex items-center gap-2">
                      <span className="w-2.5 h-2.5 rounded-full bg-blue-600"></span>
                      <span>{key.replace('_', ' ')}</span>
                    </td>
                    <td className="py-3.5 px-3">
                      {key === 'A_Star' ? (
                        <span className="px-2 py-0.5 text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-full">
                          Provably Optimal
                        </span>
                      ) : key === 'BFS' ? (
                        <span className="px-2 py-0.5 text-[10px] font-bold bg-blue-50 text-blue-700 border border-blue-200 rounded-full">
                          Hop-Optimal Only
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 text-[10px] font-bold bg-amber-50 text-amber-700 border border-amber-200 rounded-full">
                          Non-Optimal
                        </span>
                      )}
                    </td>
                    <td className="py-3.5 px-3 text-slate-800 font-semibold">{res.path_distance_km} km</td>
                    <td className="py-3.5 px-3 text-blue-700 font-bold">{res.estimated_travel_time_minutes} min</td>
                    <td className="py-3.5 px-3 text-slate-700">{res.nodes_explored}</td>
                    <td className="py-3.5 px-3 text-slate-500 ">{res.execution_time_ms} ms</td>
                    <td className="py-3.5 px-3 text-slate-500 text-[11px]">
                      {key === 'A_Star' && 'Admissible lower bound h(n) <= h*(n)'}
                      {key === 'Greedy_Best_First' && 'Heuristic-only target seeking'}
                      {key === 'BFS' && 'Unweighted FIFO expansion'}
                      {key === 'DFS' && 'Cycle-safe stack traversal'}
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Algorithmic Disclaimers & Mathematical Guarantees */}
      <div className="p-5 bg-blue-50/40 border border-blue-200/80 rounded-2xl text-xs text-slate-700 flex flex-col gap-2">
        <div className="flex items-center gap-2 font-bold text-slate-900">
          <Info className="w-4 h-4 text-blue-600" />
          <span>Scientific Principles &amp; Algorithmic Guarantees</span>
        </div>
        <p className="leading-relaxed">
          <strong>A* Search Optimality:</strong> Guaranteed to produce the globally minimal travel time because its geographic
          heuristic is strictly bounded by h(n) = haversine(n, target) / v_max, ensuring admissibility (h(n) &le; h*(n))
          and monotonicity on directed edges.
        </p>
        <p className="leading-relaxed">
          <strong>BFS &amp; DFS Behavior:</strong> BFS evaluates edge hops rather than physical distance or travel time, leading
          to sub-optimal routes in weighted road graphs. DFS follows deep paths and is vulnerable to circuitous detours;
          it is included as a comparative academic baseline.
        </p>
      </div>
    </div>
  );
};
