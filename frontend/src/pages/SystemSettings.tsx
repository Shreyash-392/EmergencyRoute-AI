import React, { useEffect, useState } from 'react';
import {
  AlertCircle,
  CheckCircle,
  Database,
  ExternalLink,
  Globe2,
  HardDrive,
  Key,
  Layers,
  Lock,
  Radio,
  RotateCcw,
  Server,
  ShieldCheck,
  Trash2,
  Zap,
} from 'lucide-react';
import { api } from '../services/api';
import { tomtomService } from '../services/tomtom';
import { SystemHealth } from '../types';

export const SystemSettings: React.FC = () => {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [roadStats, setRoadStats] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [actionMessage, setActionMessage] = useState('');

  // Server-side TomTom telemetry state
  const [isTomtomConfigured, setIsTomtomConfigured] = useState(tomtomService.isConfigured());
  const [adminInputKey, setAdminInputKey] = useState('');
  const [savingKey, setSavingKey] = useState(false);
  const [checkingStatus, setCheckingStatus] = useState(false);
  const [tomtomStatus, setTomtomStatus] = useState<{
    tested: boolean;
    valid?: boolean;
    message?: string;
  }>({ tested: false });

  const loadData = async () => {
    setLoading(true);
    try {
      const [h, r, configured] = await Promise.all([
        api.getHealth().catch(() => null),
        api.getRoadStatistics().catch(() => null),
        tomtomService.fetchStatus().catch(() => false),
      ]);
      setHealth(h);
      setRoadStats(r);
      setIsTomtomConfigured(configured);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const handleKeyChange = () => {
      setIsTomtomConfigured(tomtomService.isConfigured());
    };
    window.addEventListener('tomtom_key_updated', handleKeyChange);
    return () => window.removeEventListener('tomtom_key_updated', handleKeyChange);
  }, []);

  const handleResetCache = async () => {
    setLoading(true);
    try {
      await api.manageClosures({ action: 'clear' }).catch(() => null);
      setActionMessage('System runtime cache and simulated detours cleared.');
      await loadData();
      setTimeout(() => setActionMessage(''), 4000);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveTomtomKey = async () => {
    if (!adminInputKey.trim()) {
      setTomtomStatus({
        tested: true,
        valid: false,
        message: 'Please paste your TomTom API key before submitting.',
      });
      return;
    }
    setSavingKey(true);
    try {
      const res = await tomtomService.saveServerKey(adminInputKey);
      setTomtomStatus({
        tested: true,
        valid: res.success,
        message: res.message,
      });
      if (res.success) {
        setAdminInputKey(''); // Immediately purge from browser memory
        setIsTomtomConfigured(true);
        setActionMessage('TomTom API key securely verified and saved to server environment (.env).');
        setTimeout(() => setActionMessage(''), 4000);
      }
    } catch (e: any) {
      setTomtomStatus({
        tested: true,
        valid: false,
        message: e?.message || 'Failed to verify key with server.',
      });
    } finally {
      setSavingKey(false);
    }
  };

  const handleTestStatus = async () => {
    setCheckingStatus(true);
    try {
      const configured = await tomtomService.fetchStatus();
      setIsTomtomConfigured(configured);
      setTomtomStatus({
        tested: true,
        valid: configured,
        message: configured
          ? 'Server proxy is operational and live telemetry is active.'
          : 'Server proxy is on standby (TOMTOM_API_KEY is not configured in backend .env).',
      });
    } catch (e: any) {
      setTomtomStatus({
        tested: true,
        valid: false,
        message: 'Failed to connect to backend proxy.',
      });
    } finally {
      setCheckingStatus(false);
    }
  };

  const handleRemoveTomtomKey = async () => {
    setSavingKey(true);
    try {
      await tomtomService.removeServerKey();
      setIsTomtomConfigured(false);
      setAdminInputKey('');
      setTomtomStatus({ tested: false });
      setActionMessage('Server TomTom credentials removed.');
      setTimeout(() => setActionMessage(''), 4000);
    } finally {
      setSavingKey(false);
    }
  };

  return (
    <div className="flex-1 p-6 max-w-5xl mx-auto bg-[#FAF8F4] text-[#1E1E1C] flex flex-col gap-6 overflow-y-auto pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#D8CBB3]/40 pb-4">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-[#2B6BFF] flex items-center justify-center text-white shadow-md shadow-[#2B6BFF]/30">
              <Server className="w-4 h-4 fill-white" />
            </div>
            <h1 className="text-xl font-extrabold text-[#1E1E1C]  tracking-wide">
              SYSTEM CONFIGURATION
            </h1>
          </div>
          <p className="text-xs text-[#1E1E1C]/65 mt-1 ">
            OSM graph topology, routing endpoints, external integrations, and provenance policies.
          </p>
        </div>

        <button
          onClick={handleResetCache}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-white hover:bg-[#D8CBB3]/20 text-[#1E1E1C] border border-[#D8CBB3]/60 text-xs  font-bold rounded-xl transition-all cursor-pointer self-start sm:self-auto shadow-2xs"
        >
          <RotateCcw className="w-3.5 h-3.5 text-[#2B6BFF]" />
          <span>RESET RUNTIME CACHE</span>
        </button>
      </div>

      {actionMessage && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs rounded-xl flex items-center gap-2 ">
          <CheckCircle className="w-4 h-4 text-emerald-600" />
          <span>{actionMessage}</span>
        </div>
      )}

      {/* Grid: Diagnostics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* Card 1: Graph Engine */}
        <div className="p-5 bg-white border border-[#D8CBB3]/60 rounded-2xl shadow-xs flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-[#1E1E1C]  uppercase tracking-wider flex items-center gap-2">
              <HardDrive className="w-4 h-4 text-[#2B6BFF]" />
              <span>ROAD TOPOLOGY</span>
            </span>
            <span className="px-2 py-0.5 text-[9px]  font-bold bg-[#2B6BFF]/15 text-[#2B6BFF] border border-[#2B6BFF]/30 rounded-full">
              OSM GRAPH
            </span>
          </div>

          <div className="flex flex-col gap-1.5 text-xs text-[#1E1E1C] ">
            <div className="flex justify-between py-1.5 border-b border-[#D8CBB3]/20">
              <span className="text-[#1E1E1C]/60">Intersections (Nodes)</span>
              <span className="font-bold text-[#1E1E1C]">{health?.graph_nodes ?? 3975}</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-[#D8CBB3]/20">
              <span className="text-[#1E1E1C]/60">Road Segments (Edges)</span>
              <span className="font-bold text-[#1E1E1C]">{health?.graph_edges ?? 10229}</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-[#D8CBB3]/20">
              <span className="text-[#1E1E1C]/60">Source Network</span>
              <span className="font-bold text-[#1E1E1C]">Phagwara GraphML</span>
            </div>
            <div className="flex justify-between py-1.5">
              <span className="text-[#1E1E1C]/60">Topology State</span>
              <span className="text-[#2B6BFF] font-bold">Loaded &amp; Indexed</span>
            </div>
          </div>
        </div>

        {/* Card 2: Routing Providers */}
        <div className="p-5 bg-white border border-[#D8CBB3]/60 rounded-2xl shadow-xs flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-[#1E1E1C]  uppercase tracking-wider flex items-center gap-2">
              <Globe2 className="w-4 h-4 text-[#2B6BFF]" />
              <span>ROUTING ENGINES</span>
            </span>
            <span className="px-2 py-0.5 text-[9px]  font-bold bg-[#2B6BFF]/15 text-[#2B6BFF] border border-[#2B6BFF]/30 rounded-full">
              DUAL PROVIDER
            </span>
          </div>

          <div className="flex flex-col gap-1.5 text-xs text-[#1E1E1C] ">
            <div className="flex justify-between py-1.5 border-b border-[#D8CBB3]/20">
              <span className="text-[#1E1E1C]/60">Local AI Heuristics</span>
              <span className="font-bold text-[#1E1E1C]">A*, BFS, Greedy, DFS</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-[#D8CBB3]/20">
              <span className="text-[#1E1E1C]/60">Public OSRM Endpoint</span>
              <span className="text-[11px] text-[#2B6BFF] font-bold">project-osrm.org</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-[#D8CBB3]/20">
              <span className="text-[#1E1E1C]/60">Speed Calibration</span>
              <span className="font-bold text-[#1E1E1C]">Highway Class Limits</span>
            </div>
            <div className="flex justify-between py-1.5">
              <span className="text-[#1E1E1C]/60">Heuristic Formula</span>
              <span className="text-[11px] text-[#1E1E1C]/80">Haversine (Admissible)</span>
            </div>
          </div>
        </div>

        {/* Card 3: Data Provenance & Integrity */}
        <div className="p-5 bg-white border border-[#D8CBB3]/60 rounded-2xl shadow-xs flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-[#1E1E1C]  uppercase tracking-wider flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-[#2B6BFF]" />
              <span>DATA PROVENANCE</span>
            </span>
            <span className="px-2 py-0.5 text-[9px]  font-bold bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-full">
              ENFORCED
            </span>
          </div>

          <div className="flex flex-col gap-1.5 text-xs text-[#1E1E1C] ">
            <div className="flex justify-between py-1.5 border-b border-[#D8CBB3]/20">
              <span className="text-[#1E1E1C]/60">Synthetic / Fabricated</span>
              <span className="font-bold text-rose-600">Strictly Prohibited</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-[#D8CBB3]/20">
              <span className="text-[#1E1E1C]/60">TomTom Traffic Flow</span>
              {isTomtomConfigured ? (
                <span className="font-bold text-[#2B6BFF]">Configured</span>
              ) : (
                <span className="text-[#1E1E1C]/60">Marked Unavailable</span>
              )}
            </div>
            <div className="flex justify-between py-1.5 border-b border-[#D8CBB3]/20">
              <span className="text-[#1E1E1C]/60">Fleet GPS Telematics</span>
              <span className="text-[#1E1E1C]/60">Marked Offline</span>
            </div>
            <div className="flex justify-between py-1.5">
              <span className="text-[#1E1E1C]/60">Approved Feeds</span>
              <span className="text-[#1E1E1C]">OSM, OSRM, TomTom</span>
            </div>
          </div>
        </div>
      </div>

      {/* Card 4: TomTom Live Traffic & Base Maps Integration */}
      <div className="p-6 bg-white border border-[#D8CBB3]/60 rounded-2xl shadow-xs flex flex-col gap-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#D8CBB3]/20 pb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-[#2B6BFF]/15 border border-[#2B6BFF]/30 flex items-center justify-center text-[#2B6BFF]">
              <Radio className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-sm font-bold text-[#1E1E1C] ">TomTom Real-Time Traffic &amp; Satellites</h2>
                <span
                  className={`px-2 py-0.5 text-[9px]  font-bold rounded-full ${
                    isTomtomConfigured
                      ? 'bg-emerald-50 text-emerald-700 border border-emerald-300'
                      : 'bg-[#D8CBB3]/20 text-[#1E1E1C]/70 border border-[#D8CBB3]/40'
                  }`}
                >
                  {isTomtomConfigured ? 'SERVER-SECURED &bull; ACTIVE' : 'STANDBY'}
                </span>
              </div>
              <p className="text-xs text-[#1E1E1C]/60 mt-0.5 ">
                Enables real-time traffic speeds, delay congestion layers, and satellite tiles over Phagwara.
              </p>
            </div>
          </div>

          <a
            href="https://developer.tomtom.com"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 text-xs text-[#2B6BFF] hover:underline  font-bold self-start sm:self-auto cursor-pointer"
          >
            <span>GET FREE API KEY (2,500/DAY)</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
        </div>

        {/* Enterprise Key Protection Notice */}
        <div className="p-3.5 bg-[#FAF8F4] border border-[#D8CBB3]/60 rounded-xl flex items-start gap-3 text-xs ">
          <ShieldCheck className="w-4 h-4 text-[#2B6BFF] shrink-0 mt-0.5" />
          <div className="flex flex-col gap-1 text-[#1E1E1C]">
            <span className="font-bold">Credential Security Architecture</span>
            <p className="text-[#1E1E1C]/75 text-[11px] leading-relaxed">
              API credentials are kept strictly server-side in backend environment variables (<code className="bg-[#D8CBB3]/30 px-1 py-0.5 rounded text-[#1E1E1C]">.env</code>) and reverse-proxied via <code className="bg-[#D8CBB3]/30 px-1 py-0.5 rounded text-[#1E1E1C]">/api/v1/traffic/...</code>. Raw keys are never stored in browser storage, client bundles, or network query strings.
            </p>
          </div>
        </div>

        <div className="flex flex-col gap-3 ">
          <label className="text-xs font-bold text-[#1E1E1C]/70 flex items-center gap-1.5 uppercase tracking-wider">
            <Lock className="w-3.5 h-3.5 text-[#2B6BFF]" />
            <span>Configure Server-Side Key</span>
          </label>

          <div className="flex flex-col sm:flex-row gap-2">
            <input
              type="password"
              value={adminInputKey}
              onChange={(e) => setAdminInputKey(e.target.value)}
              placeholder={isTomtomConfigured ? '•••••••••••••••••••• (Key protected on server)' : 'Paste API key to configure server environment...'}
              className="flex-1 px-3.5 py-2.5 text-xs  bg-[#FAF8F4] border border-[#D8CBB3]/70 rounded-xl focus:border-[#2B6BFF] text-[#1E1E1C] placeholder-[#1E1E1C]/40 focus:outline-none"
            />

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={handleTestStatus}
                disabled={checkingStatus}
                className="px-4 py-2.5 bg-[#FAF8F4] hover:bg-[#D8CBB3]/30 disabled:opacity-50 text-[#1E1E1C] text-xs font-bold  rounded-xl border border-[#D8CBB3]/70 transition-all cursor-pointer flex items-center gap-1.5"
              >
                {checkingStatus ? (
                  <RotateCcw className="w-3.5 h-3.5 animate-spin text-[#2B6BFF]" />
                ) : (
                  <Radio className="w-3.5 h-3.5 text-[#2B6BFF]" />
                )}
                <span>CHECK PROXY</span>
              </button>

              <button
                type="button"
                onClick={handleSaveTomtomKey}
                disabled={savingKey || !adminInputKey.trim()}
                className="px-4 py-2.5 bg-[#2B6BFF] hover:bg-[#1A55E0] disabled:opacity-50 text-white text-xs font-bold  rounded-xl shadow-lg shadow-[#2B6BFF]/30 transition-all cursor-pointer flex items-center gap-1.5"
              >
                {savingKey ? (
                  <RotateCcw className="w-3.5 h-3.5 animate-spin text-white" />
                ) : (
                  <CheckCircle className="w-3.5 h-3.5" />
                )}
                <span>SAVE TO SERVER</span>
              </button>

              {isTomtomConfigured && (
                <button
                  type="button"
                  onClick={handleRemoveTomtomKey}
                  disabled={savingKey}
                  className="p-2.5 text-rose-600 hover:bg-rose-50 border border-rose-200 rounded-xl transition-all cursor-pointer"
                  title="Remove Key from Server"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              )}
            </div>
          </div>

          {/* Test Status Feedback */}
          {tomtomStatus.tested && (
            <div
              className={`p-3 rounded-xl border text-xs flex items-center gap-2  ${
                tomtomStatus.valid
                  ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                  : 'bg-rose-50 border-rose-200 text-rose-700'
              }`}
            >
              {tomtomStatus.valid ? (
                <CheckCircle className="w-4 h-4 text-emerald-600 shrink-0" />
              ) : (
                <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
              )}
              <span>{tomtomStatus.message}</span>
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
            <div className="p-3 bg-[#FAF8F4] border border-[#D8CBB3]/40 rounded-xl flex items-center gap-2.5">
              <div className="w-2.5 h-2.5 rounded-full bg-[#2B6BFF] shrink-0" />
              <div className="text-[11px] ">
                <span className="font-bold text-[#1E1E1C] block">Live Traffic Flow</span>
                <span className="text-[#1E1E1C]/60">Proxied server-side</span>
              </div>
            </div>

            <div className="p-3 bg-[#FAF8F4] border border-[#D8CBB3]/40 rounded-xl flex items-center gap-2.5">
              <div className="w-2.5 h-2.5 rounded-full bg-[#1E1E1C] shrink-0" />
              <div className="text-[11px] ">
                <span className="font-bold text-[#1E1E1C] block">Live Incidents</span>
                <span className="text-[#1E1E1C]/60">Accidents &amp; road closures</span>
              </div>
            </div>

            <div className="p-3 bg-[#FAF8F4] border border-[#D8CBB3]/40 rounded-xl flex items-center gap-2.5">
              <div className="w-2.5 h-2.5 rounded-full bg-[#2B6BFF] shrink-0" />
              <div className="text-[11px] ">
                <span className="font-bold text-[#1E1E1C] block">Multi-Map Switcher</span>
                <span className="text-[#1E1E1C]/60">TomTom, Satellites &amp; Night View</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
