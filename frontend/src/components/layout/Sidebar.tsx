import React from 'react';
import {
  AlertTriangle,
  BarChart3,
  Compass,
  FileText,
  LayoutDashboard,
  Settings,
} from 'lucide-react';

interface SidebarProps {
  currentTab: string;
  onSelectTab: (tab: string) => void;
  activeIncidentsCount?: number;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentTab,
  onSelectTab,
  activeIncidentsCount = 0,
}) => {
  const navItems = [
    {
      id: 'dashboard',
      label: 'Dashboard',
      icon: LayoutDashboard,
      badge: null,
    },
    {
      id: 'route-planner',
      label: 'Find a Route',
      icon: Compass,
      badge: 'Main',
    },
    {
      id: 'road-conditions',
      label: 'Road Conditions',
      icon: AlertTriangle,
      badge: null,
    },
    {
      id: 'emergency-reports',
      label: 'Emergency Reports',
      icon: FileText,
      badge: activeIncidentsCount > 0 ? `${activeIncidentsCount}` : null,
      badgeColor: 'bg-rose-500 text-white',
    },
    {
      id: 'route-performance',
      label: 'Route Performance',
      icon: BarChart3,
      badge: null,
    },
    {
      id: 'settings',
      label: 'Settings',
      icon: Settings,
      badge: null,
    },
  ];

  return (
    <aside className="w-64 bg-[#1E1E1C] border-r border-[#D8CBB3]/15 flex flex-col justify-between select-none shrink-0 z-20">
      <div className="py-4 px-3 flex flex-col gap-1.5">
        <div className="px-3 pb-2 text-[10px] font-bold uppercase tracking-widest text-[#D8CBB3]/50 flex items-center justify-between">
          <span>Command Modules</span>
          <span className="w-1.5 h-1.5 rounded-full bg-[#2B6BFF]"></span>
        </div>

        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectTab(item.id)}
              className={`flex items-center justify-between px-3.5 py-3 rounded-2xl text-xs font-semibold transition-all cursor-pointer ${
                isActive
                  ? 'bg-[#2B6BFF] text-white shadow-[0_0_20px_rgba(43,107,255,0.4)] border border-[#2B6BFF]'
                  : 'text-[#D8CBB3]/75 hover:text-[#D8CBB3] hover:bg-[#262624] border border-transparent'
              }`}
            >
              <div className="flex items-center gap-3">
                <Icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-[#D8CBB3]/60'}`} />
                <span className="tracking-wide">{item.label}</span>
              </div>
              {item.badge && (
                <span
                  className={`px-2 py-0.5 text-[9px] font-extrabold uppercase rounded-lg ${
                    isActive
                      ? 'bg-white/20 text-white'
                      : 'bg-[#262624] text-[#D8CBB3] border border-[#D8CBB3]/30'
                  }`}
                >
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Footer Tactical Status Card */}
      <div className="p-3 border-t border-[#D8CBB3]/15">
        <div className="p-3.5 bg-[#262624] rounded-2xl border border-[#D8CBB3]/20 text-[11px] text-[#D8CBB3] flex flex-col gap-1.5">
          <div className="font-bold flex items-center justify-between text-xs">
            <span className="text-[#D8CBB3]">Phagwara Sector</span>
            <span className="px-1.5 py-0.5 text-[9px] bg-[#2B6BFF]/20 text-[#2B6BFF]  font-bold rounded">LIVE</span>
          </div>
          <span className="text-[10px] text-[#D8CBB3]/60 leading-tight">
            Strict Palette: #1E1E1C &bull; #D8CBB3 &bull; #2B6BFF
          </span>
        </div>
      </div>
    </aside>
  );
};
