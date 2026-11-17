import React, { useEffect, useState } from 'react';
import {
  AlertTriangle,
  Radio,
  RefreshCw,
} from 'lucide-react';
import { PhagwaraMap } from '../components/maps/PhagwaraMap';
import { api } from '../services/api';
import { wsClient } from '../services/websocket';
import { ActiveRoadClosure } from '../types';

export const TrafficMonitor: React.FC = () => {
  const [closures, setClosures] = useState<ActiveRoadClosure[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchTraffic = async () => {
    setLoading(true);
    try {
      const data = await api.getTraffic();
      setClosures(data.closures || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTraffic();
    const unsub = wsClient.subscribe('traffic_update', () => fetchTraffic());
    return () => unsub();
  }, []);

  return (
    <div className="flex-1 flex flex-col lg:flex-row h-full overflow-hidden bg-slate-50">
      {/* Left Sidebar Control */}
      <div className="w-full lg:w-[440px] p-5 bg-white border-r border-slate-200/90 flex flex-col gap-4 overflow-y-auto z-10 shadow-xs">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <Radio className="w-5 h-5 text-blue-600" />
              <span>Traffic &amp; Road Intelligence</span>
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">Authoritative road restrictions and telemetry status.</p>
          </div>
          <button
            onClick={() => fetchTraffic()}
            disabled={loading}
            className="p-2 bg-slate-50 hover:bg-slate-100 text-slate-600 border border-slate-200 rounded-xl transition-colors cursor-pointer"
            title="Refresh Status"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>

        {/* Live Traffic Data Status */}
        <div className="p-4 bg-slate-50/70 border border-slate-200/80 rounded-2xl flex flex-col gap-2">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
              Live Traffic Status
            </span>
            <span className="px-2 py-0.5 text-[9px] font-bold bg-slate-100 text-slate-600 border border-slate-200 rounded-full">
              UNAVAILABLE
            </span>
          </div>
          <p className="text-xs text-slate-800 font-semibold">
            No verified live traffic information is currently available.
          </p>
          <p className="text-[11px] text-slate-500 leading-relaxed">
            Third-party sensor feeds and floating car telematics are not connected for this municipal jurisdiction. No artificial traffic congestion is generated.
          </p>
        </div>

        {/* OSM Road Network Status */}
        <div className="p-4 bg-white border border-slate-200/90 rounded-2xl flex flex-col gap-2 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
              Road Network Geometry
            </span>
            <span className="px-2 py-0.5 text-[9px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-full">
              OSM DATA
            </span>
          </div>
          <div className="grid grid-cols-2 gap-2 text-xs mt-1">
            <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
              <span className="text-[10px] text-slate-500 font-medium block">Intersections</span>
              <span className="font-bold text-slate-900 text-base">3,975</span>
            </div>
            <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
              <span className="text-[10px] text-slate-500 font-medium block">Directed Edges</span>
              <span className="font-bold text-slate-900 text-base">10,229</span>
            </div>
          </div>
          <p className="text-[11px] text-slate-500 mt-1">
            Retrieved from OpenStreetMap. Speeds derived from verified highway classification speed limits.
          </p>
        </div>

        {/* Active Road Closures List */}
        <div className="p-4 bg-white border border-slate-200/90 rounded-2xl flex flex-col gap-2.5 flex-1 shadow-xs">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <AlertTriangle className="w-4 h-4 text-rose-600" />
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">
                Recorded Road Closures ({closures.length})
              </h3>
            </div>
            <span className={`px-2 py-0.5 text-[9px] font-bold rounded-full border ${
              closures.length === 0
                ? 'bg-slate-100 text-slate-600 border-slate-200'
                : 'bg-rose-50 text-rose-700 border-rose-200'
            }`}>
              {closures.length === 0 ? 'UNAVAILABLE' : 'USER REPORTED'}
            </span>
          </div>

          {closures.length === 0 ? (
            <div className="py-6 px-4 bg-slate-50 border border-dashed border-slate-200 rounded-2xl text-center flex flex-col items-center gap-1">
              <span className="text-xs text-slate-700 font-semibold">
                No recorded road closures found. This does not guarantee that all roads are open.
              </span>
              <span className="text-[11px] text-slate-500 mt-0.5">
                Unrecorded obstructions, localized repair works, or weather hazards may still exist.
              </span>
            </div>
          ) : (
            <div className="flex flex-col gap-2 max-h-60 overflow-y-auto">
              {closures.map((c) => (
                <div key={c.closure_id} className="p-3 bg-rose-50/40 border border-rose-200 rounded-xl text-xs">
                  <div className="flex justify-between font-bold text-rose-900">
                    <span>{c.reason}</span>
                    <span className="text-[8px] uppercase px-1.5 py-0.5 bg-white text-rose-700 border border-rose-300 rounded">
                      USER REPORTED
                    </span>
                  </div>
                  <div className="text-[10px] text-slate-600 mt-1 ">
                    Edge: {c.u} &rarr; {c.v} (key: {c.key})
                  </div>
                  <div className="text-[10px] text-slate-500 mt-0.5">
                    Recorded: {c.reported_at ? new Date(c.reported_at).toLocaleString() : 'Active session'}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Right Canvas: Phagwara Map */}
      <div className="flex-1 h-full relative">
        <PhagwaraMap />
      </div>
    </div>
  );
};
