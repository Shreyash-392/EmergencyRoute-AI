import React, { useEffect, useState } from 'react';
import {
  AlertOctagon,
  CheckCircle2,
  FileText,
  Info,
  MapPin,
  Plus,
  Send,
  ShieldAlert,
  Zap,
} from 'lucide-react';
import { PhagwaraMap } from '../components/maps/PhagwaraMap';
import { api } from '../services/api';
import { wsClient } from '../services/websocket';
import { EmergencyIncident } from '../types';

export const EmergencyReports: React.FC = () => {
  const [incidents, setIncidents] = useState<EmergencyIncident[]>([]);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Form Fields
  const [locationName, setLocationName] = useState('Civil Hospital Phagwara');
  const [lat, setLat] = useState('31.2223');
  const [lng, setLng] = useState('75.7672');
  const [reportType, setReportType] = useState('general_medical');
  const [priority, setPriority] = useState('high');
  const [description, setDescription] = useState('');
  const [reportSource, setReportSource] = useState('Caller Report');
  const [formSuccess, setFormSuccess] = useState(false);

  const fetchIncidents = async () => {
    setLoading(true);
    try {
      const list = await api.getIncidents();
      setIncidents(list);
    } catch (err) {
      console.error('Error fetching emergency reports:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIncidents();
    const unsub = wsClient.subscribe('incident_created', () => fetchIncidents());
    return () => unsub();
  }, []);

  const handleLocationPresetChange = (loc: string) => {
    setLocationName(loc);
    switch (loc) {
      case 'Civil Hospital Phagwara':
        setLat('31.2223');
        setLng('75.7672');
        break;
      case 'Model Town Crossing':
        setLat('31.2260');
        setLng('75.7790');
        break;
      case 'Phagwara Bus Stand':
        setLat('31.2215');
        setLng('75.7738');
        break;
      case 'Railway Station Road':
        setLat('31.2185');
        setLng('75.7725');
        break;
      case 'Hanumangarh Chowk':
        setLat('31.2241');
        setLng('75.7695');
        break;
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setFormSuccess(false);

    try {
      await api.createIncident({
        title: `${reportType.replace('_', ' ').toUpperCase()} at ${locationName}`,
        description: description.trim() || `Report received via ${reportSource}.`,
        incident_type: reportType,
        priority,
        lat: parseFloat(lat),
        lng: parseFloat(lng),
      });

      setDescription('');
      setFormSuccess(true);
      await fetchIncidents();
      setTimeout(() => setFormSuccess(false), 4000);
    } catch (err: any) {
      alert(`Submission failed: ${err?.message || err}`);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col lg:flex-row h-full overflow-hidden bg-[#FAF8F4] text-[#1E1E1C]">
      {/* Left Tactical Intake Panel (Light Background) */}
      <div className="w-full lg:w-[460px] p-5 bg-white border-r border-[#D8CBB3]/50 flex flex-col gap-4 overflow-y-auto z-10 shadow-lg">
        {/* Header HUD */}
        <div className="pb-3 border-b border-[#D8CBB3]/30">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-xl bg-[#2B6BFF] flex items-center justify-center text-white shadow-md shadow-[#2B6BFF]/30">
                <FileText className="w-4 h-4 fill-white" />
              </div>
              <div>
                <h2 className="text-base font-extrabold text-[#1E1E1C] tracking-wide ">
                  INCIDENT INTAKE
                </h2>
                <span className="text-[10px]  text-[#2B6BFF] uppercase tracking-wider font-bold">
                  Emergency Dispatch Feed
                </span>
              </div>
            </div>
            <span className="px-2.5 py-0.5 text-[9px]  font-bold bg-[#FAF8F4] text-[#1E1E1C]/80 border border-[#D8CBB3]/60 rounded-full">
              LIVE AUDIT
            </span>
          </div>
          <p className="text-xs text-[#1E1E1C]/65 mt-2 leading-relaxed">
            Record, broadcast, and verify emergency reports across Phagwara sectors.
          </p>
        </div>

        {/* Disclaimer Notice */}
        <div className="p-3 bg-[#FAF8F4] border border-[#D8CBB3]/50 rounded-2xl text-xs text-[#1E1E1C]/70 leading-relaxed flex items-start gap-2.5  text-[11px]">
          <Info className="w-4 h-4 text-[#2B6BFF] shrink-0 mt-0.5" />
          <span>
            Citizen reports are archived into the verifiable audit trail without simulated data.
          </span>
        </div>

        {/* Report Intake Form */}
        <form onSubmit={handleSubmit} className="p-4 bg-[#FAF8F4] border border-[#D8CBB3]/60 rounded-2xl flex flex-col gap-3 shadow-2xs">
          <h3 className="text-xs  font-bold uppercase tracking-wider text-[#1E1E1C]/80">
            DISPATCH NEW REPORT
          </h3>

          {/* Location field */}
          <div>
            <label className="text-[10px]  font-bold text-[#1E1E1C]/60 uppercase tracking-wider block mb-1">
              Location Sector
            </label>
            <select
              value={locationName}
              onChange={(e) => handleLocationPresetChange(e.target.value)}
              className="w-full bg-white border border-[#D8CBB3]/70 text-xs text-[#1E1E1C] rounded-xl p-2.5 focus:outline-none focus:border-[#2B6BFF] shadow-2xs"
            >
              <option value="Civil Hospital Phagwara">Civil Hospital Phagwara (GT Road)</option>
              <option value="Model Town Crossing">Model Town Crossing</option>
              <option value="Phagwara Bus Stand">Phagwara Central Bus Stand</option>
              <option value="Railway Station Road">Phagwara Railway Station Road</option>
              <option value="Hanumangarh Chowk">Hanumangarh Chowk</option>
            </select>
          </div>

          {/* Type of Report & Priority */}
          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="text-[10px]  font-bold text-[#1E1E1C]/60 uppercase tracking-wider block mb-1">
                Category
              </label>
              <select
                value={reportType}
                onChange={(e) => setReportType(e.target.value)}
                className="w-full bg-white border border-[#D8CBB3]/70 text-xs text-[#1E1E1C] rounded-xl p-2.5 focus:outline-none focus:border-[#2B6BFF] shadow-2xs"
              >
                <option value="general_medical">Medical Emergency</option>
                <option value="road_accident">Road Accident / Crash</option>
                <option value="fire_emergency">Fire Emergency</option>
                <option value="hazard">Road Obstruction / Hazard</option>
              </select>
            </div>

            <div>
              <label className="text-[10px]  font-bold text-[#1E1E1C]/60 uppercase tracking-wider block mb-1">
                Priority
              </label>
              <select
                value={priority}
                onChange={(e) => setPriority(e.target.value)}
                className="w-full bg-white border border-[#D8CBB3]/70 text-xs text-[#1E1E1C] rounded-xl p-2.5 focus:outline-none focus:border-[#2B6BFF] shadow-2xs"
              >
                <option value="critical">Critical</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
            </div>
          </div>

          {/* Report Source */}
          <div>
            <label className="text-[10px]  font-bold text-[#1E1E1C]/60 uppercase tracking-wider block mb-1">
              Source Channel
            </label>
            <select
              value={reportSource}
              onChange={(e) => setReportSource(e.target.value)}
              className="w-full bg-white border border-[#D8CBB3]/70 text-xs text-[#1E1E1C] rounded-xl p-2.5 focus:outline-none focus:border-[#2B6BFF] shadow-2xs"
            >
              <option value="Caller Report">Caller Report (Direct Contact)</option>
              <option value="Operator Intake">Operator Intake (Station Desk)</option>
              <option value="Field Observation">Field Observation (Public Observer)</option>
            </select>
          </div>

          {/* Description */}
          <div>
            <label className="text-[10px]  font-bold text-[#1E1E1C]/60 uppercase tracking-wider block mb-1">
              Incident Description
            </label>
            <textarea
              rows={2}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe the emergency or blockage..."
              className="w-full bg-white border border-[#D8CBB3]/70 text-xs text-[#1E1E1C] placeholder-[#1E1E1C]/40 rounded-xl p-2.5 focus:outline-none focus:border-[#2B6BFF] shadow-2xs"
            />
          </div>

          {formSuccess && (
            <div className="p-2.5 bg-emerald-50 border border-emerald-200 rounded-xl text-xs text-emerald-800 flex items-center gap-2 ">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
              <span>Report recorded successfully in database.</span>
            </div>
          )}

          {/* Submit Button */}
          <button
            type="submit"
            disabled={submitting}
            className="w-full py-3 bg-[#2B6BFF] hover:bg-[#1A55E0] text-white  font-bold text-xs rounded-xl shadow-lg shadow-[#2B6BFF]/30 transition-all active:scale-95 disabled:opacity-50 cursor-pointer flex items-center justify-center gap-2"
          >
            {submitting ? (
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
            ) : (
              <>
                <Send className="w-3.5 h-3.5" />
                <span>SUBMIT DISPATCH REPORT</span>
              </>
            )}
          </button>
        </form>

        {/* Recorded Reports List */}
        <div className="flex flex-col gap-2 mt-1">
          <div className="flex items-center justify-between">
            <span className="text-[10px]  font-bold uppercase tracking-wider text-[#1E1E1C]/60">
              LOGGED DISPATCHES ({incidents.length})
            </span>
            <span className="text-[10px]  text-[#1E1E1C]/40">
              {incidents.length === 0 ? 'NO RECORDS' : 'DATABASE PERSISTENT'}
            </span>
          </div>

          {incidents.length === 0 ? (
            <div className="p-8 bg-[#FAF8F4] border border-dashed border-[#D8CBB3]/50 rounded-2xl text-center flex flex-col items-center gap-2.5">
              <ShieldAlert className="w-6 h-6 text-[#1E1E1C]/40" />
              <p className="text-xs  font-bold text-[#1E1E1C]">No reports logged yet.</p>
              <p className="text-[11px] text-[#1E1E1C]/60 max-w-xs ">
                Dispatched reports will appear here and on the Phagwara map immediately.
              </p>
            </div>
          ) : (
            <div className="flex flex-col gap-2 max-h-60 overflow-y-auto pr-1">
              {incidents.map((inc) => (
                <div
                  key={inc.incident_id}
                  className="p-3.5 bg-white border border-[#D8CBB3]/50 rounded-2xl flex flex-col gap-1.5 shadow-2xs"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-xs text-[#1E1E1C]  truncate max-w-[200px]">
                      {inc.title}
                    </span>
                    <span className="px-1.5 py-0.5 text-[8px]  font-bold rounded bg-[#2B6BFF]/15 text-[#2B6BFF] border border-[#2B6BFF]/30">
                      DISPATCHED
                    </span>
                  </div>
                  <div className="text-[11px] text-[#1E1E1C]/65 ">
                    TYPE: <strong className="capitalize text-[#1E1E1C]">{inc.incident_type.replace('_', ' ')}</strong> &bull; PRIORITY: <span className="uppercase text-[#2B6BFF] font-bold">{inc.priority}</span>
                  </div>
                  {inc.description && (
                    <div className="text-[11px] text-[#1E1E1C]/75 italic">
                      "{inc.description}"
                    </div>
                  )}
                  <div className="text-[10px] text-[#1E1E1C]/40  mt-0.5">
                    ID: {inc.incident_id} &bull; STATUS: {inc.status}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Right Map Viewport (Default Dark) */}
      <div className="flex-1 h-full relative">
        <PhagwaraMap incidents={incidents} />
      </div>
    </div>
  );
};
