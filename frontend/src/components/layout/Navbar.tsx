import React, { useEffect, useState } from 'react';
import {
  Activity,
  AlertTriangle,
  BarChart3,
  ChevronDown,
  Compass,
  FileText,
  MapPin,
  Radio,
  Server,
  Sparkles,
  Zap,
} from 'lucide-react';
import { api } from '../../services/api';
import { wsClient } from '../../services/websocket';
import { SystemHealth } from '../../types';

interface NavbarProps {
  activeTab: string;
  onSelectTab: (tab: string) => void;
  activeIncidentsCount?: number;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  onSelectTab,
  activeIncidentsCount = 0,
}) => {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [pagesDropdownOpen, setPagesDropdownOpen] = useState(false);

  useEffect(() => {
    api.getHealth().then(setHealth).catch(console.error);
  }, []);

  const navLinks = [
    { id: 'dashboard', label: 'Home' },
    { id: 'route-planner', label: 'Route Planner' },
    { id: 'road-conditions', label: 'Road Closures' },
  ];

  const secondaryPages = [
    { id: 'emergency-reports', label: 'Fleet & Incidents', badge: activeIncidentsCount > 0 ? activeIncidentsCount : null },
    { id: 'route-performance', label: 'Algorithm Benchmarks', badge: null },
    { id: 'settings', label: 'Settings', badge: null },
  ];

  return (
    <header className="sticky top-3 sm:top-5 z-50 flex justify-center px-4 w-full pointer-events-none select-none">
      <div className="pointer-events-auto bg-white/95 backdrop-blur-xl rounded-full shadow-[0_12px_40px_rgba(30,30,28,0.12)] border border-[#D8CBB3]/60 px-3 sm:px-4 py-2 sm:py-2.5 flex items-center justify-between gap-3 sm:gap-6 max-w-4xl w-full transition-all">
        {/* Left: Clean Typographic Brand Mark */}
        <div
          onClick={() => onSelectTab('dashboard')}
          className="flex items-center gap-2 cursor-pointer group"
        >
          <span className="w-2.5 h-2.5 rounded-full bg-[#2B6BFF] group-hover:scale-125 transition-transform"></span>
          <span className="font-extrabold text-sm tracking-tight text-[#1E1E1C]">
            EmergencyRoute
          </span>
        </div>

        {/* Center: Floating Navigation Pills */}
        <nav className="flex items-center gap-1 sm:gap-2 text-xs font-semibold text-[#1E1E1C]/80">
          {navLinks.map((item) => {
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onSelectTab(item.id)}
                className={`px-3 py-1.5 rounded-full transition-all cursor-pointer flex items-center gap-1.5 ${
                  isActive
                    ? 'text-[#1E1E1C] font-bold bg-[#D8CBB3]/30 shadow-2xs'
                    : 'text-[#1E1E1C]/70 hover:text-[#1E1E1C] hover:bg-black/5'
                }`}
              >
                {isActive && <span className="w-1.5 h-1.5 rounded-full bg-[#2B6BFF]"></span>}
                <span>{item.label}</span>
              </button>
            );
          })}

          {/* Pages Dropdown Pill */}
          <div className="relative">
            <button
              onClick={() => setPagesDropdownOpen(!pagesDropdownOpen)}
              className={`px-3 py-1.5 rounded-full transition-all cursor-pointer flex items-center gap-1 ${
                ['emergency-reports', 'route-performance', 'settings'].includes(activeTab)
                  ? 'text-[#1E1E1C] font-bold bg-[#D8CBB3]/30'
                  : 'text-[#1E1E1C]/70 hover:text-[#1E1E1C] hover:bg-black/5'
              }`}
            >
              <span>Pages</span>
              <ChevronDown className={`w-3.5 h-3.5 transition-transform ${pagesDropdownOpen ? 'rotate-180' : ''}`} />
            </button>

            {pagesDropdownOpen && (
              <div className="absolute top-full left-0 mt-2 w-48 bg-white rounded-2xl shadow-xl border border-[#D8CBB3]/50 p-1.5 flex flex-col gap-0.5 z-50 animate-in fade-in zoom-in-95">
                {secondaryPages.map((pg) => (
                  <button
                    key={pg.id}
                    onClick={() => {
                      onSelectTab(pg.id);
                      setPagesDropdownOpen(false);
                    }}
                    className={`w-full px-3 py-2 text-left rounded-xl text-xs font-medium transition-colors flex items-center justify-between cursor-pointer ${
                      activeTab === pg.id
                        ? 'bg-[#2B6BFF] text-white font-semibold'
                        : 'text-[#1E1E1C] hover:bg-[#D8CBB3]/20'
                    }`}
                  >
                    <span>{pg.label}</span>
                    {pg.badge && (
                      <span className="px-1.5 py-0.2 bg-rose-500 text-white text-[9px] rounded-full font-bold">
                        {pg.badge}
                      </span>
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>
        </nav>

        {/* Right: Quick Action Pill Button */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => onSelectTab('route-planner')}
            className="px-4 py-2 bg-[#2B6BFF] hover:bg-[#1A55E0] text-white text-xs font-bold rounded-full shadow-md shadow-[#2B6BFF]/30 transition-all active:scale-95 cursor-pointer flex items-center gap-1.5"
          >
            <span>Plan Route</span>
            <span className="w-4 h-4 rounded-full bg-white/20 flex items-center justify-center text-[10px] font-bold">
              &rsaquo;
            </span>
          </button>
        </div>
      </div>
    </header>
  );
};
