import React, { useEffect, useState } from 'react';
import {
  Compass,
  Plus,
  ShieldAlert,
  Truck,
  X,
} from 'lucide-react';
import { PhagwaraMap } from '../components/maps/PhagwaraMap';
import { api } from '../services/api';
import { wsClient } from '../services/websocket';
import {
  AlgorithmResult,
  EmergencyIncident,
  Vehicle,
  VehicleRankingCandidate,
} from '../types';

export const EmergencyDispatch: React.FC = () => {
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [incidents, setIncidents] = useState<EmergencyIncident[]>([]);
  const [selectedIncident, setSelectedIncident] = useState<EmergencyIncident | null>(null);
  const [rankedCandidates, setRankedCandidates] = useState<VehicleRankingCandidate[]>([]);
  const [dispatchRoute, setDispatchRoute] = useState<AlgorithmResult | null>(null);

  // New incident modal state
  const [showNewModal, setShowNewModal] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newType, setNewType] = useState('cardiac_arrest');
  const [newPriority, setNewPriority] = useState('critical');
  const [newLat, setNewLat] = useState('31.2215');
  const [newLng, setNewLng] = useState('75.7738');

  const [loading, setLoading] = useState(false);
  const [rankingLoading, setRankingLoading] = useState(false);

  const refreshData = async () => {
    setLoading(true);
    try {
      const [vList, iList] = await Promise.all([api.getVehicles(), api.getIncidents()]);
      setVehicles(vList);
      setIncidents(iList);
      if (!selectedIncident && iList.length > 0) {
        handleSelectIncident(iList[0]);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshData();
    const unsub1 = wsClient.subscribe('incident_created', () => refreshData());
    const unsub2 = wsClient.subscribe('vehicle_dispatched', () => refreshData());
    return () => {
      unsub1();
      unsub2();
    };
  }, []);

  const handleSelectIncident = async (inc: EmergencyIncident) => {
    setSelectedIncident(inc);
    setDispatchRoute(null);
    setRankingLoading(true);
    try {
      const res = await api.rankVehicles(inc.incident_id);
      setRankedCandidates(res.ranked_candidates);
    } catch (e) {
      console.error('Error ranking vehicles:', e);
    } finally {
      setRankingLoading(false);
    }
  };

  const handleAssignVehicle = async (vehId: string) => {
    if (!selectedIncident) return;
    setLoading(true);
    try {
      const res = await api.assignVehicle(selectedIncident.incident_id, vehId);
      setDispatchRoute(res.dispatch_route);
      await refreshData();
    } catch (e: any) {
      alert(`Assignment failed: ${e.response?.data?.detail || e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateNewIncident = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim()) return;
    try {
      const inc = await api.createIncident({
        title: newTitle,
        incident_type: newType,
        priority: newPriority,
        lat: parseFloat(newLat),
        lng: parseFloat(newLng),
      });
      setShowNewModal(false);
      setNewTitle('');
      await refreshData();
      handleSelectIncident(inc);
    } catch (err: any) {
      alert('Error creating incident: ' + err.message);
    }
  };

  return (
    <div className="flex-1 flex flex-col lg:flex-row h-full overflow-hidden bg-slate-50">
      {/* Left Control Column */}
      <div className="w-full lg:w-[480px] p-5 bg-white border-r border-slate-200/90 flex flex-col gap-4 overflow-y-auto z-10 shadow-xs">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <Truck className="w-5 h-5 text-blue-600" />
              <span>Emergency Dispatch Operations</span>
            </h2>
            <p className="text-[11px] text-slate-500 mt-0.5">
              Multi-criteria A* ranking and municipal emergency unit allocation.
            </p>
          </div>
          <button
            onClick={() => setShowNewModal(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white font-medium text-xs rounded-xl shadow-xs transition-all active:scale-95 cursor-pointer"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>New 112 Call</span>
          </button>
        </div>

        {/* Operational Directive Notice */}
        <div className="px-3.5 py-2.5 bg-slate-50 border border-slate-200/80 rounded-2xl text-[11px] text-slate-600 leading-relaxed">
          <div className="flex items-center gap-1.5 mb-1">
            <span className="px-1.5 py-0.5 text-[8px] font-bold rounded bg-slate-200 text-slate-700">
              OPERATIONAL DIRECTIVE
            </span>
            <span className="font-semibold text-slate-800">Intake Policy</span>
          </div>
          All incidents must be manually registered via dispatcher intake (e.g. 112 phone calls). EmergencyRoute AI does <span className="font-semibold text-slate-900">NOT</span> detect accidents or traffic events automatically.
        </div>

        {/* Active Incidents List */}
        <div className="flex flex-col gap-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Emergency Incidents ({incidents.length})
            </span>
            <span className={`px-2 py-0.5 text-[9px] font-bold rounded-full border ${
              incidents.length === 0
                ? 'bg-slate-100 text-slate-600 border-slate-200'
                : 'bg-rose-50 text-rose-700 border-rose-200'
            }`}>
              {incidents.length === 0 ? 'UNAVAILABLE' : 'USER REPORTED'}
            </span>
          </div>
          <div className="flex flex-col gap-2 max-h-48 overflow-y-auto pr-1">
            {incidents.length === 0 ? (
              <div className="p-4 bg-slate-50 border border-dashed border-slate-200 rounded-2xl text-center">
                <p className="text-xs text-slate-700 font-semibold">No verified emergency incidents are currently available.</p>
                <p className="text-[11px] text-slate-500 mt-1">
                  Click <strong className="text-blue-600 font-semibold">+ New 112 Call</strong> above to record an incoming caller emergency report.
                </p>
              </div>
            ) : (
              incidents.map((inc) => {
                const isSelected = selectedIncident?.incident_id === inc.incident_id;
                const isCrit = inc.priority === 'critical';
                return (
                  <div
                    key={inc.incident_id}
                    onClick={() => handleSelectIncident(inc)}
                    className={`p-3 rounded-2xl border transition-all cursor-pointer flex flex-col gap-1.5 ${
                      isSelected
                        ? 'bg-blue-50/70 border-blue-500 shadow-xs'
                        : 'bg-white border-slate-200 hover:border-slate-300'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-xs text-slate-900 truncate max-w-[240px]">{inc.title}</span>
                      <div className="flex items-center gap-1.5">
                        <span className="px-1.5 py-0.5 text-[8px] font-bold rounded bg-amber-50 text-amber-700 border border-amber-200">
                          USER REPORTED
                        </span>
                        <span
                          className={`px-1.5 py-0.5 text-[9px] font-bold rounded uppercase ${
                            isCrit
                              ? 'bg-rose-50 text-rose-700 border border-rose-200'
                              : 'bg-amber-50 text-amber-700 border border-amber-200'
                          }`}
                        >
                          {inc.priority}
                        </span>
                      </div>
                    </div>
                    <div className="flex justify-between text-[11px] text-slate-500">
                      <span>{inc.incident_type.replace('_', ' ')} &bull; 112 Phone Intake</span>
                      <span className={inc.status === 'dispatched' ? 'text-amber-700 font-semibold' : 'text-slate-500'}>
                        Status: {inc.status.toUpperCase()}
                      </span>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Intelligent Vehicle Ranking Panel for Selected Incident */}
        {selectedIncident && (
          <div className="flex flex-col gap-2.5 mt-2 flex-1">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-1.5">
                <Compass className="w-4 h-4 text-blue-600" />
                <span>Response Units</span>
              </span>
              <span className={`px-2 py-0.5 text-[9px] font-bold rounded-full border ${
                vehicles.length === 0
                  ? 'bg-slate-100 text-slate-600 border-slate-200'
                  : 'bg-emerald-50 text-emerald-700 border-emerald-200'
              }`}>
                {vehicles.length === 0 ? 'UNAVAILABLE' : 'OFFICIALLY VERIFIED'}
              </span>
            </div>

            {vehicles.length === 0 ? (
              <div className="p-4 bg-slate-50 border border-dashed border-slate-200 text-center rounded-2xl flex flex-col items-center gap-1">
                <span className="text-xs text-slate-700 font-semibold">No connected emergency vehicle tracking feed.</span>
                <span className="text-[11px] text-slate-500">
                  Vehicle telematics must be connected before A* travel time ranking can be executed.
                </span>
              </div>
            ) : rankingLoading ? (
              <div className="py-6 text-center text-xs text-slate-500 flex items-center justify-center gap-2">
                <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                <span>Computing live A* travel times for municipal fleet...</span>
              </div>
            ) : rankedCandidates.length === 0 ? (
              <div className="p-4 bg-slate-50 text-center text-xs text-slate-500 rounded-2xl border border-slate-200">
                No available vehicles match the requirements for this incident.
              </div>
            ) : (
              <div className="flex flex-col gap-2 max-h-64 overflow-y-auto pr-1">
                {rankedCandidates.map((cand) => (
                  <div
                    key={cand.vehicle.vehicle_id}
                    className="p-3 bg-white border border-slate-200 hover:border-blue-400 rounded-2xl flex items-center justify-between transition-all shadow-2xs"
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="w-5 h-5 rounded-full bg-blue-50 text-blue-700 font-bold text-[10px] flex items-center justify-center border border-blue-200">
                          #{cand.rank}
                        </span>
                        <span className="font-bold text-xs text-slate-900">{cand.vehicle.call_sign}</span>
                        <span className="text-[10px] text-slate-400 ">({cand.vehicle.vehicle_type})</span>
                      </div>
                      <div className="text-[11px] text-slate-600 mt-1">
                        ETA: <strong className="text-blue-700">{cand.estimated_travel_time_minutes} min</strong> &bull;{' '}
                        {cand.distance_km} km
                      </div>
                      <div className="text-[10px] text-slate-400 truncate max-w-[220px]">
                        Base: {cand.vehicle.base_station}
                      </div>
                    </div>

                    <button
                      onClick={() => handleAssignVehicle(cand.vehicle.vehicle_id)}
                      disabled={loading || selectedIncident.status === 'dispatched'}
                      className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-40 text-white font-medium text-xs rounded-xl shadow-xs transition-all active:scale-95 cursor-pointer"
                    >
                      {selectedIncident.status === 'dispatched' ? 'Dispatched' : 'Dispatch'}
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Right Canvas: Phagwara Map */}
      <div className="flex-1 h-full relative">
        <PhagwaraMap
          activeRoute={dispatchRoute}
          vehicles={vehicles}
          incidents={incidents}
        />
      </div>

      {/* Modal: Create Incident */}
      {showNewModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="w-full max-w-md bg-white border border-slate-200 rounded-3xl p-6 shadow-xl flex flex-col gap-4 animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <ShieldAlert className="w-5 h-5 text-blue-600" />
                <span>Register Emergency 112 Call</span>
              </h3>
              <button
                onClick={() => setShowNewModal(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreateNewIncident} className="flex flex-col gap-3">
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Incident Headline</label>
                <input
                  type="text"
                  placeholder="e.g. Critical Cardiac Arrest at Bus Stand"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 text-xs text-slate-800 p-2.5 rounded-xl focus:outline-none focus:border-blue-500 shadow-2xs"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold text-slate-700 block mb-1">Incident Category</label>
                  <select
                    value={newType}
                    onChange={(e) => setNewType(e.target.value)}
                    className="w-full bg-slate-50 border border-slate-200 text-xs text-slate-800 p-2.5 rounded-xl focus:outline-none focus:border-blue-500 shadow-2xs"
                  >
                    <option value="cardiac_arrest">Cardiac Arrest</option>
                    <option value="road_hazard">Road Obstruction / Hazard</option>
                    <option value="road_accident">Reported Road Collision (Caller)</option>
                    <option value="fire_emergency">Fire Emergency</option>
                    <option value="crime_in_progress">Crime in Progress</option>
                    <option value="general_medical">General Medical</option>
                  </select>
                </div>

                <div>
                  <label className="text-xs font-semibold text-slate-700 block mb-1">Priority</label>
                  <select
                    value={newPriority}
                    onChange={(e) => setNewPriority(e.target.value)}
                    className="w-full bg-slate-50 border border-slate-200 text-xs text-slate-800 p-2.5 rounded-xl focus:outline-none focus:border-blue-500 shadow-2xs"
                  >
                    <option value="critical">Critical</option>
                    <option value="high">High</option>
                    <option value="medium">Medium</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold text-slate-700 block mb-1">Latitude</label>
                  <input
                    type="text"
                    value={newLat}
                    onChange={(e) => setNewLat(e.target.value)}
                    className="w-full bg-slate-50 border border-slate-200 text-xs text-slate-800 p-2 rounded-xl  shadow-2xs"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-700 block mb-1">Longitude</label>
                  <input
                    type="text"
                    value={newLng}
                    onChange={(e) => setNewLng(e.target.value)}
                    className="w-full bg-slate-50 border border-slate-200 text-xs text-slate-800 p-2 rounded-xl  shadow-2xs"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 mt-2 pt-2 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowNewModal(false)}
                  className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs rounded-xl font-medium transition-colors cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs rounded-xl font-semibold shadow-xs transition-colors cursor-pointer"
                >
                  Log &amp; Dispatch
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
