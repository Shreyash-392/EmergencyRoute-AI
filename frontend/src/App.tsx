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
    <div className="flex flex-col h-screen bg-[#FAF8F4] text-[#1E1E1C] font-sans overflow-hidden antialiased relative">
      {/* Floating Island Navigation Capsule (Reference Layout) */}
      <Navbar
        activeTab={currentTab}
        onSelectTab={setCurrentTab}
        activeIncidentsCount={activeIncidentsCount}
      />

      {/* Main Full-Width Application Viewport */}
      <main className="flex-1 overflow-y-auto">
        {currentTab === 'dashboard' && (
          <div className="h-full w-full">
            <Dashboard onNavigateTab={setCurrentTab} />
          </div>
        )}

        {currentTab === 'route-planner' && (
          <div className="h-full pt-2">
            <RoutePlanner />
          </div>
        )}

        {currentTab === 'road-conditions' && (
          <div className="h-full pt-2">
            <RoadConditions />
          </div>
        )}

        {currentTab === 'emergency-reports' && (
          <div className="h-full pt-2">
            <EmergencyReports />
          </div>
        )}

        {currentTab === 'route-performance' && (
          <div className="h-full pt-2">
            <RoutePerformance />
          </div>
        )}

        {currentTab === 'settings' && (
          <div className="h-full pt-2">
            <SystemSettings />
          </div>
        )}
      </main>
    </div>
  );
}
