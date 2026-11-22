import { useEffect, useState } from 'react';
import { Navbar } from './components/layout/Navbar';
import { Dashboard } from './pages/Dashboard';
import { RoutePlanner } from './pages/RoutePlanner';
import { RoadConditions } from './pages/RoadConditions';
import { EmergencyReports } from './pages/EmergencyReports';
import { RoutePerformance } from './pages/RoutePerformance';
import { SystemSettings } from './pages/SystemSettings';
import { api } from './services/api';
import { wsClient } from './services/websocket';
import { EmergencyIncident } from './types';

export default function App() {
  const [currentTab, setCurrentTab] = useState<string>('dashboard');
  const [incidents, setIncidents] = useState<EmergencyIncident[]>([]);

  useEffect(() => {
    // Initial fetch of active incidents for the badge
    api.getIncidents()
      .then((data) => {
        if (Array.isArray(data)) setIncidents(data);
      })
      .catch((err) => console.warn('Could not fetch incidents on load:', err));

    // Listen to real-time events via WebSocket
    const unsubscribe = wsClient.subscribe('*', (event) => {
      if (
        event.type === 'incident_created' ||
        event.type === 'dispatch_created'
      ) {
        api.getIncidents().then((data) => {
          if (Array.isArray(data)) setIncidents(data);
        }).catch(console.warn);
      }
    });

    return () => unsubscribe();
  }, []);

  const activeIncidentsCount = Array.isArray(incidents)
    ? incidents.filter(
        (inc) => inc.status === 'reported' || inc.status === 'dispatched'
      ).length
    : 0;

  return (
    <div className="h-screen w-screen bg-[#1E1E1C] text-[#1E1E1C] font-sans overflow-hidden antialiased relative">
      {/* Floating Island Navigation Capsule (Top Left) */}
      <Navbar
        activeTab={currentTab}
        onSelectTab={setCurrentTab}
        activeIncidentsCount={activeIncidentsCount}
      />

      {/* Main Full-Width Application Viewport (True Edge-to-Edge) */}
      <main className="w-full h-full relative overflow-hidden">
        {currentTab === 'dashboard' && (
          <div className="h-full w-full">
            <Dashboard onNavigateTab={setCurrentTab} />
          </div>
        )}

        {currentTab === 'route-planner' && (
          <div className="h-full pt-14 bg-[#FAF8F4] overflow-y-auto">
            <RoutePlanner />
          </div>
        )}

        {currentTab === 'road-conditions' && (
          <div className="h-full pt-14 bg-[#FAF8F4] overflow-y-auto">
            <RoadConditions />
          </div>
        )}

        {currentTab === 'emergency-reports' && (
          <div className="h-full pt-14 bg-[#FAF8F4] overflow-y-auto">
            <EmergencyReports />
          </div>
        )}

        {currentTab === 'route-performance' && (
          <div className="h-full pt-14 bg-[#FAF8F4] overflow-y-auto">
            <RoutePerformance />
          </div>
        )}

        {currentTab === 'settings' && (
          <div className="h-full pt-14 bg-[#FAF8F4] overflow-y-auto">
            <SystemSettings />
          </div>
        )}
      </main>
    </div>
  );
}
