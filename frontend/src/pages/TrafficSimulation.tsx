import React, { useState } from 'react';
import {
  AlertOctagon,
  Flame,
  RotateCcw,
  Zap,
} from 'lucide-react';
import { PhagwaraMap } from '../components/maps/PhagwaraMap';
import { api } from '../services/api';
import { AlgorithmResult, RerouteResponse } from '../types';

export const TrafficSimulation: React.FC = () => {
  const [activeRoute, setActiveRoute] = useState<AlgorithmResult | null>(null);
  const [rerouteState, setRerouteState] = useState<RerouteResponse | null>(null);
  const [selectedCorridor, setSelectedCorridor] = useState('GT Road Hanumangarh Chowk');
  const [congestionFactor, setCongestionFactor] = useState(2.0);
  const [loading, setLoading] = useState(false);
  const [simStatus, setSimStatus] = useState<string>('Ready for test closure evaluation');

  // Baseline Model Town -> Civil Hospital
  const initBaselineRoute = async () => {
    setLoading(true);
    try {
      const route = await api.calculateOptimalRoute({
        origin_lat: 31.2260,
        origin_lng: 75.7790,
        dest_lat: 31.2223,
        dest_lng: 75.7672,
        objective: 'travel_time',
      });
      setActiveRoute(route);
      setRerouteState(null);
      setSimStatus('Initial route established (A* Search Optimal).');
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleSimulateBlockage = async () => {
    if (!activeRoute) {
      await initBaselineRoute();
    }
    setLoading(true);
    setSimStatus('Simulating road closure & testing dynamic detour...');

    try {
      const routeToBlock = activeRoute!;
      const midEdge = routeToBlock.edge_path[Math.floor(routeToBlock.edge_path.length / 2)];

      const closurePayload = {
        closure_id: `user_close_${Date.now()}`,
        u: midEdge.u,
        v: midEdge.v,
        key: midEdge.key,
        reason: `Operator test road closure on ${midEdge.name}`,
        severity: 'impassable',
      };

      const rerouteResp = await api.dynamicReroute({
        route_id: 'active_emergency_run',
        current_route: routeToBlock,
        new_closures: [closurePayload],
        min_improvement_threshold_pct: 10.0,
      });

      setRerouteState(rerouteResp);
      setActiveRoute(rerouteResp.active_route);
      setSimStatus(`Road closed: ${midEdge.name}. Dynamic detour executed (${rerouteResp.decision}).`);
    } catch (err) {
      console.error('Simulation error:', err);
      setSimStatus('Road closure test failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleRestoreNormal = async () => {
    setLoading(true);
    try {
      await api.manageClosures({ action: 'clear' });
      setRerouteState(null);
      await initBaselineRoute();
      setSimStatus('All test bottlenecks cleared. Restored baseline flow.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col lg:flex-row h-full overflow-hidden bg-slate-50">
      {/* Simulation Controls Sidebar */}
      <div className="w-full lg:w-[440px] p-5 bg-white border-r border-slate-200/90 flex flex-col gap-4 overflow-y-auto z-10 shadow-xs">
        <div>
          <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <Flame className="w-5 h-5 text-orange-600" />
            <span>Road Closure &amp; Detour Lab</span>
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Test real-time A* dynamic recalculation on the actual OpenStreetMap graph.
          </p>
        </div>

        {/* Operational Disclaimer Banner */}
        <div className="p-3.5 bg-amber-50 border border-amber-200 rounded-2xl text-[11px] text-amber-800 leading-relaxed">
          <strong className="font-semibold text-amber-900">No Automated Detection:</strong> EmergencyRoute AI does NOT detect accidents or street events automatically. Dispatchers can manually close road links to evaluate automatic A* detour recalculation.
        </div>

        {/* Step 1: Active Route Check */}
        {!activeRoute && (
          <div className="p-4 bg-slate-50 border border-slate-200 rounded-2xl flex flex-col gap-2.5">
            <span className="text-xs font-bold text-slate-800">1. Initialize Test Route</span>
            <p className="text-[11px] text-slate-500">
              Establish a baseline route from Model Town to Civil Hospital Phagwara before injecting closures.
            </p>
            <button
              onClick={initBaselineRoute}
              disabled={loading}
              className="py-2 px-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs rounded-xl shadow-xs transition-colors cursor-pointer"
            >
              {loading ? 'Initializing...' : 'Establish Baseline Route'}
            </button>
          </div>
        )}

        {/* Closure Injection Panel */}
        <div className="p-4 bg-white border border-slate-200/90 rounded-2xl flex flex-col gap-3 shadow-xs">
          <span className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
            <AlertOctagon className="w-4 h-4 text-rose-600" />
            <span>Road Closure Testing Controls</span>
          </span>

          <div>
            <label className="text-[11px] font-semibold text-slate-600 block mb-1">Target Corridor / Chowk</label>
            <select
              value={selectedCorridor}
              onChange={(e) => setSelectedCorridor(e.target.value)}
              className="w-full bg-slate-50 border border-slate-200 text-xs text-slate-800 rounded-xl p-2.5 focus:outline-none focus:border-blue-500 shadow-2xs"
            >
              <option value="GT Road Hanumangarh Chowk">GT Road &bull; Hanumangarh Chowk (Major Artery)</option>
              <option value="Railway Road Underpass">Phagwara Railway Road Underpass</option>
              <option value="Model Town Main Road">Model Town Commercial Corridor</option>
              <option value="NH44 Highway Interchange">NH44 Highway Interchange</option>
            </select>
          </div>

          <div>
            <div className="flex justify-between text-[11px] font-semibold text-slate-600 mb-1">
              <span>Congestion Multiplier</span>
              <span className="text-orange-700 font-bold">{congestionFactor}x Slowdown</span>
            </div>
            <input
              type="range"
              min="1.0"
              max="4.0"
              step="0.5"
              value={congestionFactor}
              onChange={(e) => setCongestionFactor(parseFloat(e.target.value))}
              className="w-full accent-blue-600 cursor-pointer"
            />
          </div>

          <div className="grid grid-cols-2 gap-2 mt-1">
            <button
              onClick={handleSimulateBlockage}
              disabled={loading}
              className="py-2.5 bg-rose-600 hover:bg-rose-700 text-white font-semibold text-xs rounded-xl shadow-xs transition-all active:scale-95 disabled:opacity-50 cursor-pointer"
            >
              Simulate Road Blockage
            </button>

            <button
              onClick={handleRestoreNormal}
              disabled={loading}
              className="py-2.5 bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 font-semibold text-xs rounded-xl shadow-2xs transition-all cursor-pointer flex items-center justify-center gap-1.5"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Restore Baseline</span>
            </button>
          </div>
        </div>

        {/* Dynamic Reroute Evaluation Output */}
        {rerouteState && (
          <div className="p-4 bg-emerald-50/50 border border-emerald-200 rounded-2xl flex flex-col gap-2 shadow-xs">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-emerald-800 uppercase tracking-wider flex items-center gap-1.5">
                <Zap className="w-4 h-4 text-emerald-600" />
                <span>Reroute Engine Triggered</span>
              </span>
              <span className="px-2 py-0.5 text-[9px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-300 rounded-full">
                {rerouteState.decision}
              </span>
            </div>

            <p className="text-[11px] text-slate-700 leading-relaxed font-medium">
              {rerouteState.reason}
            </p>

            {rerouteState.comparison && (
              <div className="grid grid-cols-2 gap-2 bg-white p-3 rounded-xl border border-emerald-200/80 text-[11px] mt-1 shadow-2xs">
                <div>
                  <span className="text-slate-500 block">Original Route ETA:</span>
                  <span className="font-bold text-slate-400 line-through">
                    {(rerouteState.comparison.old_travel_time_seconds / 60.0).toFixed(1)} min
                  </span>
                </div>
                <div>
                  <span className="text-emerald-700 block font-semibold">New Detour ETA:</span>
                  <span className="font-bold text-emerald-700 text-sm">
                    {(rerouteState.comparison.new_travel_time_seconds / 60.0).toFixed(1)} min
                  </span>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Status Feed */}
        <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl text-[11px] text-slate-500 mt-auto">
          <span className="font-semibold text-slate-700">Lab Status:</span> {simStatus}
        </div>
      </div>

      {/* Right Canvas: Phagwara Map */}
      <div className="flex-1 h-full relative">
        <PhagwaraMap activeRoute={activeRoute} />
      </div>
    </div>
  );
};
