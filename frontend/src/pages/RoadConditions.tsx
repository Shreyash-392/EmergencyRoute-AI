import React, { useEffect, useState } from 'react';
import {
  Activity,
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Construction,
  Info,
  MapPin,
  Plus,
  Radio,
  RefreshCw,
  RotateCcw,
  ShieldAlert,
  TrafficCone,
  Trash2,
  Zap,
} from 'lucide-react';
import { PhagwaraMap, RoadSegmentFeature } from '../components/maps/PhagwaraMap';
import { api } from '../services/api';
import { tomtomService, TomTomIncident } from '../services/tomtom';
import { ActiveRoadClosure } from '../types';

export const RoadConditions: React.FC = () => {
  const [closures, setClosures] = useState<ActiveRoadClosure[]>([]);
  const [tomtomIncidents, setTomtomIncidents] = useState<TomTomIncident[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingIncidents, setLoadingIncidents] = useState(false);
  const [activeTab, setActiveTab] = useState<'status' | 'live_incidents' | 'detour_lab'>('status');
  const [isTomTomActive, setIsTomTomActive] = useState(tomtomService.isConfigured());

  // Detour simulation state
  const [testReason, setTestReason] = useState('Reported Road Barrier');
  const [testCorridor, setTestCorridor] = useState('GT Road / Civil Hospital Crossing');

  // Simulated road segments for map visualization
  const [closedSegments, setClosedSegments] = useState<RoadSegmentFeature[]>([]);

  const fetchClosures = async () => {
    setLoading(true);
    try {
      const res = await api.getTraffic();
      if (res && res.closures) {
        setClosures(res.closures);
      } else {
        setClosures([]);
      }
    } catch (err) {
      console.error('Error fetching road closures:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchTomTomIncidents = async () => {
    if (!tomtomService.isConfigured()) {
      setTomtomIncidents([]);
      return;
    }
    setLoadingIncidents(true);
    try {
      const list = await tomtomService.getIncidentDetails();
      setTomtomIncidents(list);
    } catch (err) {
      console.error('Error fetching TomTom incident details:', err);
      setTomtomIncidents([]);
    } finally {
      setLoadingIncidents(false);
    }
  };

  useEffect(() => {
    fetchClosures();
    tomtomService.fetchStatus().then((active) => {
      setIsTomTomActive(active);
      if (active) fetchTomTomIncidents();
    });

    const handleKeyChange = () => {
      const active = tomtomService.isConfigured();
      setIsTomTomActive(active);
      if (active) fetchTomTomIncidents();
    };
    window.addEventListener('tomtom_key_updated', handleKeyChange);
    return () => {
      window.removeEventListener('tomtom_key_updated', handleKeyChange);
    };
  }, []);

  const handleAddTestClosure = async () => {
    setLoading(true);
    try {
      const res = await api.manageClosures({
        action: 'add',
        reason: `${testReason} (${testCorridor})`,
        severity: 'high',
      });
      if (res && res.active_closures) {
        setClosures(res.active_closures);
      }
      const newSeg: RoadSegmentFeature = {
        name: testCorridor,
        coordinates: [
          [31.2223, 75.7672],
          [31.2241, 75.7695],
        ],
        reason: testReason,
        source: 'USER REPORTED',
        status: 'CLOSED',
        reported_at: new Date().toLocaleTimeString(),
      };
      setClosedSegments([newSeg]);
    } catch (err: any) {
      alert(`Could not record closure: ${err?.message || err}`);
    } finally {
      setLoading(false);
    }
  };

  const handleClearClosures = async () => {
    setLoading(true);
    try {
      await api.manageClosures({ action: 'clear' });
      setClosures([]);
      setClosedSegments([]);
    } catch (err: any) {
      alert(`Could not clear closures: ${err?.message || err}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col lg:flex-row h-full overflow-hidden bg-[#FAF8F4] text-[#1E1E1C]">
      {/* Left Tactical Command Panel (Light Background) */}
      <div className="w-full lg:w-[460px] p-5 bg-white border-r border-[#D8CBB3]/50 flex flex-col gap-4 overflow-y-auto z-10 shadow-lg">
        {/* Header HUD */}
        <div className="pb-3 border-b border-[#D8CBB3]/30">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-xl bg-[#2B6BFF] flex items-center justify-center text-white shadow-md shadow-[#2B6BFF]/30">
                <AlertTriangle className="w-4 h-4 fill-white" />
              </div>
              <div>
                <h2 className="text-base font-extrabold text-[#1E1E1C] tracking-wide ">
                  ROAD RESTRICTIONS
                </h2>
                <span className="text-[10px]  text-[#2B6BFF] uppercase tracking-wider font-bold">
                  Sector Impedance Matrix
                </span>
              </div>
            </div>
            <span className="px-2.5 py-0.5 text-[9px]  font-bold bg-[#FAF8F4] text-[#1E1E1C]/80 border border-[#D8CBB3]/60 rounded-full">
              PHAGWARA
            </span>
          </div>
          <p className="text-xs text-[#1E1E1C]/65 mt-2 leading-relaxed">
            Inspect verified closures, TomTom real-time incidents, and simulate dynamic detour barriers.
          </p>
        </div>

        {/* Live Traffic Feed Status Card */}
        <div className="p-4 bg-[#FAF8F4] border border-[#D8CBB3]/60 rounded-2xl flex flex-col gap-2 shadow-2xs">
          <div className="flex items-center justify-between">
            <span className="text-xs  font-bold text-[#1E1E1C] flex items-center gap-2">
              <Radio className={`w-3.5 h-3.5 ${isTomTomActive ? 'text-[#2B6BFF] animate-pulse' : 'text-[#1E1E1C]/40'}`} />
              <span>LIVE TRAFFIC FEED</span>
            </span>
            <span
              className={`px-2 py-0.5 text-[9px]  font-bold rounded-full ${
                isTomTomActive
                  ? 'bg-[#2B6BFF]/15 text-[#2B6BFF] border border-[#2B6BFF]/30'
                  : 'bg-[#D8CBB3]/20 text-[#1E1E1C]/70 border border-[#D8CBB3]/40'
              }`}
            >
              {isTomTomActive ? 'TOMTOM ACTIVE' : 'STANDBY (ADD KEY)'}
            </span>
          </div>
          <p className="text-xs text-[#1E1E1C]/65 leading-relaxed  text-[11px]">
            {isTomTomActive
              ? 'Real-time TomTom traffic flow and incident feeds are active on the map with sub-second delta updates.'
              : 'TomTom traffic telemetry is currently offline. Road speeds use standard legal corridor limits.'}
          </p>
        </div>

        {/* Tactical Tab Switcher */}
        <div className="p-1 bg-[#FAF8F4] rounded-xl flex gap-1 border border-[#D8CBB3]/60">
          <button
            onClick={() => setActiveTab('status')}
            className={`flex-1 py-1.5 px-1.5 text-xs  font-bold rounded-lg transition-all cursor-pointer ${
              activeTab === 'status'
                ? 'bg-[#2B6BFF] text-white shadow-md shadow-[#2B6BFF]/30'
                : 'text-[#1E1E1C]/70 hover:text-[#1E1E1C]'
            }`}
          >
            Closures ({closures.length})
          </button>
          <button
            onClick={() => setActiveTab('live_incidents')}
            className={`flex-1 py-1.5 px-1.5 text-xs  font-bold rounded-lg transition-all cursor-pointer flex items-center justify-center gap-1 ${
              activeTab === 'live_incidents'
                ? 'bg-[#2B6BFF] text-white shadow-md shadow-[#2B6BFF]/30'
                : 'text-[#1E1E1C]/70 hover:text-[#1E1E1C]'
            }`}
          >
            <TrafficCone className="w-3 h-3" />
            <span>Incidents ({tomtomIncidents.length})</span>
          </button>
          <button
            onClick={() => setActiveTab('detour_lab')}
            className={`flex-1 py-1.5 px-1.5 text-xs  font-bold rounded-lg transition-all cursor-pointer ${
              activeTab === 'detour_lab'
                ? 'bg-[#2B6BFF] text-white shadow-md shadow-[#2B6BFF]/30'
                : 'text-[#1E1E1C]/70 hover:text-[#1E1E1C]'
            }`}
          >
            Simulate Block
          </button>
        </div>

        {/* Tab 1: Recorded Closures */}
        {activeTab === 'status' && (
          <div className="flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <span className="text-[10px]  font-bold uppercase tracking-wider text-[#1E1E1C]/60">
                DATABASE RESTRICTIONS
              </span>
              <button
                onClick={fetchClosures}
                disabled={loading}
                className="text-[11px]  text-[#2B6BFF] hover:underline font-bold flex items-center gap-1 cursor-pointer"
              >
                <RefreshCw className={`w-3 h-3 ${loading ? 'animate-spin' : ''}`} />
                <span>REFRESH</span>
              </button>
            </div>

            {closures.length === 0 ? (
              <div className="p-8 bg-[#FAF8F4] border border-dashed border-[#D8CBB3]/50 rounded-2xl text-center flex flex-col items-center gap-2.5">
                <CheckCircle2 className="w-6 h-6 text-[#2B6BFF]" />
                <p className="text-xs font-bold text-[#1E1E1C] ">
                  No active closures in database.
                </p>
                <p className="text-[11px] text-[#1E1E1C]/60 max-w-xs leading-relaxed ">
                  All Phagwara corridors are currently marked open. Use the Detour Lab to simulate roadblocks.
                </p>
              </div>
            ) : (
              <div className="flex flex-col gap-2">
                {closures.map((c) => (
                  <div
                    key={c.closure_id}
                    className="p-3.5 bg-white border border-[#D8CBB3]/60 rounded-2xl flex flex-col gap-1.5 shadow-2xs"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-xs text-[#1E1E1C] ">
                        {c.reason || 'Recorded Road Closure'}
                      </span>
                      <span className="px-1.5 py-0.5 text-[8px]  font-bold rounded bg-rose-50 text-rose-600 border border-rose-200">
                        CLOSED
                      </span>
                    </div>
                    <div className="text-[11px] text-[#1E1E1C]/65 ">
                      SEVERITY: <strong className="capitalize text-[#1E1E1C]">{c.severity}</strong> &bull; STATUS: IMPASSABLE
                    </div>
                    <div className="text-[10px] text-[#1E1E1C]/40 ">
                      SOURCE: VERIFIED RESTRICTION &bull; {c.reported_at || 'Active'}
                    </div>
                  </div>
                ))}

                <button
                  onClick={handleClearClosures}
                  className="w-full py-2.5 bg-[#FAF8F4] hover:bg-[#D8CBB3]/30 text-[#1E1E1C] border border-[#D8CBB3]/60  font-bold text-xs rounded-xl transition-all cursor-pointer flex items-center justify-center gap-1.5 mt-1"
                >
                  <Trash2 className="w-3.5 h-3.5 text-[#2B6BFF]" />
                  <span>CLEAR RECORDED CLOSURES</span>
                </button>
              </div>
            )}
          </div>
        )}

        {/* Tab 2: TomTom Live Incidents */}
        {activeTab === 'live_incidents' && (
          <div className="flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <span className="text-[10px]  font-bold uppercase tracking-wider text-[#1E1E1C]/60 flex items-center gap-1.5">
                <TrafficCone className="w-3.5 h-3.5 text-[#2B6BFF]" />
                <span>TOMTOM INCIDENT STREAM</span>
              </span>
              <button
                onClick={fetchTomTomIncidents}
                disabled={loadingIncidents || !isTomTomActive}
                className="text-[11px]  text-[#2B6BFF] hover:underline font-bold flex items-center gap-1 cursor-pointer"
              >
                <RefreshCw className={`w-3 h-3 ${loadingIncidents ? 'animate-spin' : ''}`} />
                <span>REFRESH</span>
              </button>
            </div>

            {!isTomTomActive ? (
              <div className="p-8 bg-[#FAF8F4] border border-dashed border-[#D8CBB3]/50 rounded-2xl text-center flex flex-col items-center gap-2.5">
                <AlertCircle className="w-6 h-6 text-[#1E1E1C]/40" />
                <p className="text-xs font-bold text-[#1E1E1C] ">
                  TomTom Incident Stream in Standby
                </p>
                <p className="text-[11px] text-[#1E1E1C]/60 max-w-xs leading-relaxed ">
                  Configure <code className="bg-[#D8CBB3]/30 px-1 py-0.5 rounded text-[#1E1E1C]">TOMTOM_API_KEY</code> in server environment (<code className="bg-[#D8CBB3]/30 px-1 py-0.5 rounded text-[#1E1E1C]">.env</code>) to activate live accident feeds and road hazards.
                </p>
              </div>
            ) : tomtomIncidents.length === 0 ? (
              <div className="p-8 bg-[#FAF8F4] border border-dashed border-[#D8CBB3]/50 rounded-2xl text-center flex flex-col items-center gap-2.5">
                <CheckCircle2 className="w-6 h-6 text-[#2B6BFF]" />
                <p className="text-xs font-bold text-[#1E1E1C] ">
                  No active incidents reported.
                </p>
                <p className="text-[11px] text-[#1E1E1C]/60 max-w-xs leading-relaxed ">
                  TomTom traffic sensors report normal flow with no major accidents in Phagwara.
                </p>
              </div>
            ) : (
              <div className="flex flex-col gap-2.5">
                {tomtomIncidents.map((inc) => (
                  <div
                    key={inc.id}
                    className="p-3.5 bg-white border border-[#D8CBB3]/60 rounded-2xl flex flex-col gap-1.5 shadow-2xs"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-xs text-[#1E1E1C]  flex items-center gap-1.5">
                        <TrafficCone className="w-3.5 h-3.5 text-[#2B6BFF] shrink-0" />
                        <span>{inc.categoryName || inc.description}</span>
                      </span>
                      <span className="px-1.5 py-0.5 text-[8px]  font-bold rounded bg-[#2B6BFF]/15 text-[#2B6BFF] border border-[#2B6BFF]/30">
                        {inc.delaySeconds > 0 ? `+${Math.round(inc.delaySeconds / 60)} MIN DELAY` : 'ACTIVE'}
                      </span>
                    </div>

                    <p className="text-xs text-[#1E1E1C]/80 leading-snug">{inc.description}</p>

                    {(inc.from || inc.to) && (
                      <div className="text-[11px] text-[#1E1E1C]/60 flex items-center gap-1 ">
                        <MapPin className="w-3 h-3 text-[#2B6BFF] shrink-0" />
                        <span>Between {inc.from || 'Start'} and {inc.to || 'End'}</span>
                      </div>
                    )}

                    <div className="flex items-center justify-between text-[10px] text-[#1E1E1C]/40 pt-1 border-t border-[#D8CBB3]/20 ">
                      <span>Source: Official TomTom Incident Feed</span>
                      {inc.lengthMeters ? <span>Affected: {inc.lengthMeters}m</span> : null}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Tab 3: Detour Simulation Lab */}
        {activeTab === 'detour_lab' && (
          <div className="flex flex-col gap-3">
            <div className="p-3 bg-[#FAF8F4] border border-[#2B6BFF]/30 rounded-2xl text-xs text-[#1E1E1C] leading-snug ">
              <strong className="text-[#2B6BFF]">Detour Simulation Lab:</strong> Test how road impedance instantly recalculates emergency routes on Phagwara corridors.
            </div>

            {/* 1-Click Quick Preset Scenarios */}
            <div className="flex flex-col gap-1.5">
              <label className="text-[10px]  font-bold text-[#1E1E1C]/70 uppercase tracking-wider">
                1-Click Quick Scenarios
              </label>
              <div className="grid grid-cols-1 gap-1.5">
                <button
                  type="button"
                  onClick={() => {
                    setTestCorridor('GT Road / Civil Hospital Crossing');
                    setTestReason('Major Traffic Collision & Detour');
                  }}
                  className="p-2 bg-white hover:bg-[#FAF8F4] border border-[#D8CBB3]/70 rounded-xl text-left text-xs  text-[#1E1E1C] transition-all cursor-pointer flex items-center justify-between"
                >
                  <span>GT Road (Hospital Crossing)</span>
                  <span className="text-[10px] text-[#2B6BFF] font-bold">LOAD</span>
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setTestCorridor('Railway Underpass');
                    setTestReason('Severe Monsoon Waterlogging');
                  }}
                  className="p-2 bg-white hover:bg-[#FAF8F4] border border-[#D8CBB3]/70 rounded-xl text-left text-xs  text-[#1E1E1C] transition-all cursor-pointer flex items-center justify-between"
                >
                  <span>Railway Underpass (Flooded)</span>
                  <span className="text-[10px] text-[#2B6BFF] font-bold">LOAD</span>
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setTestCorridor('Model Town Main Market Street');
                    setTestReason('Festival Market Congestion');
                  }}
                  className="p-2 bg-white hover:bg-[#FAF8F4] border border-[#D8CBB3]/70 rounded-xl text-left text-xs  text-[#1E1E1C] transition-all cursor-pointer flex items-center justify-between"
                >
                  <span>Model Town Market Street</span>
                  <span className="text-[10px] text-[#2B6BFF] font-bold">LOAD</span>
                </button>
              </div>
            </div>

            <div className="flex flex-col gap-3">
              <div>
                <label className="text-[10px]  font-bold text-[#1E1E1C]/70 uppercase tracking-wider block mb-1.5">
                  Corridor to Close
                </label>
                <select
                  value={testCorridor}
                  onChange={(e) => setTestCorridor(e.target.value)}
                  className="w-full bg-white border border-[#D8CBB3]/70 text-xs text-[#1E1E1C] rounded-xl p-2.5 focus:outline-none focus:border-[#2B6BFF] shadow-2xs"
                >
                  <option value="GT Road / Civil Hospital Crossing">GT Road (Civil Hospital Crossing)</option>
                  <option value="Banga Road / Railway Crossing">Banga Road (Railway Crossing)</option>
                  <option value="Model Town Main Market Street">Model Town Main Market Street</option>
                  <option value="Railway Underpass">Phagwara Railway Underpass</option>
                </select>
              </div>

              <div>
                <label className="text-[10px]  font-bold text-[#1E1E1C]/70 uppercase tracking-wider block mb-1.5">
                  Closure Reason
                </label>
                <input
                  type="text"
                  value={testReason}
                  onChange={(e) => setTestReason(e.target.value)}
                  className="w-full bg-white border border-[#D8CBB3]/70 text-xs text-[#1E1E1C] placeholder-[#1E1E1C]/40 rounded-xl p-2.5 focus:outline-none focus:border-[#2B6BFF] shadow-2xs"
                  placeholder="e.g. Construction / Fallen tree"
                />
              </div>

              <button
                onClick={handleAddTestClosure}
                disabled={loading}
                className="w-full py-3 bg-[#2B6BFF] hover:bg-[#1A55E0] text-white  font-bold text-xs rounded-xl shadow-lg shadow-[#2B6BFF]/30 transition-all active:scale-95 cursor-pointer flex items-center justify-center gap-2"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>SIMULATE ROAD CLOSURE</span>
              </button>

              {closures.length > 0 && (
                <button
                  onClick={handleClearClosures}
                  className="w-full py-2 bg-[#FAF8F4] hover:bg-[#D8CBB3]/20 text-[#1E1E1C] border border-[#D8CBB3]/60  font-bold text-xs rounded-xl transition-all cursor-pointer flex items-center justify-center gap-1.5"
                >
                  <RotateCcw className="w-3.5 h-3.5 text-[#2B6BFF]" />
                  <span>RESET ALL CLOSURES</span>
                </button>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Right Map Viewport (Default Dark) */}
      <div className="flex-1 h-full relative">
        <PhagwaraMap closedRoadSegments={closedSegments} />
      </div>
    </div>
  );
};
