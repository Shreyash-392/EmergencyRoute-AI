import React from 'react';

interface NavbarProps {
  activeTab: string;
  onSelectTab: (tab: string) => void;
  activeIncidentsCount?: number;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  onSelectTab,
}) => {
  const navLinks = [
    { id: 'dashboard', label: 'Home' },
    { id: 'route-planner', label: 'Route Planner' },
    { id: 'road-conditions', label: 'Road Closures' },
  ];

  return (
    <header className="absolute top-3 left-3 sm:left-6 z-40 pointer-events-none select-none">
      <div className="pointer-events-auto bg-[#181816]/95 backdrop-blur-xl rounded-full shadow-2xl border border-[#D8CBB3]/30 px-3.5 py-1.5 flex items-center gap-2.5 transition-all text-[#D8CBB3]">
        {/* Clean Typographic Brand Mark */}
        <div
          onClick={() => onSelectTab('dashboard')}
          className="flex items-center cursor-pointer pr-1"
        >
          <span className="font-extrabold text-sm tracking-tight text-white hover:text-[#2B6BFF] transition-colors">
            EmergencyRoute
          </span>
        </div>

        <div className="w-px h-4 bg-[#D8CBB3]/20" />

        {/* Floating Navigation Pills */}
        <nav className="flex items-center gap-1 text-xs font-semibold">
          {navLinks.map((item) => {
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onSelectTab(item.id)}
                className={`px-3 py-1 rounded-full transition-all cursor-pointer ${
                  isActive
                    ? 'text-white font-bold bg-[#2B6BFF] shadow-xs'
                    : 'text-[#D8CBB3]/70 hover:text-white hover:bg-white/10'
                }`}
              >
                {item.label}
              </button>
            );
          })}
        </nav>
      </div>
    </header>
  );
};
