import { api } from './api';

type EventCallback = (event: { type: string; timestamp: string; data: any }) => void;

class WebSocketClient {
  private socket: WebSocket | null = null;
  private listeners: Map<string, Set<EventCallback>> = new Map();
  private reconnectTimeout: any = null;
  private pollInterval: any = null;
  private isConnected = false;
  private lastPolledTimestamp = '';

  public get connected(): boolean {
    return this.isConnected;
  }

  constructor() {
    this.connect();
  }

  public connect() {
    if (this.socket && (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING)) {
      return;
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    let wsUrl = `${protocol}//${window.location.host}/ws/events`;
    if (import.meta.env.VITE_WS_URL) {
      wsUrl = `${import.meta.env.VITE_WS_URL.replace(/\/+$/, '')}/ws/events`;
    } else if (import.meta.env.VITE_API_URL) {
      try {
        const u = new URL(import.meta.env.VITE_API_URL);
        const wsProto = u.protocol === 'https:' ? 'wss:' : 'ws:';
        wsUrl = `${wsProto}//${u.host}/ws/events`;
      } catch (e) {
        // Fallback to location.host
      }
    }

    try {
      this.socket = new WebSocket(wsUrl);

      this.socket.onopen = () => {
        this.isConnected = true;
        this.stopPollingFallback();
        console.log('[EmergencyRoute WebSocket] Connected to real-time events stream.');
      };

      this.socket.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          this.notifyListeners(payload.type, payload);
          this.notifyListeners('*', payload);
        } catch (e) {
          console.error('[EmergencyRoute WebSocket] JSON parse error:', e);
        }
      };

      this.socket.onclose = () => {
        this.isConnected = false;
        this.startPollingFallback();
        this.scheduleReconnect();
      };

      this.socket.onerror = () => {
        this.isConnected = false;
        this.socket?.close();
      };
    } catch (e) {
      this.startPollingFallback();
      this.scheduleReconnect();
    }
  }

  private scheduleReconnect() {
    if (this.reconnectTimeout) clearTimeout(this.reconnectTimeout);
    this.reconnectTimeout = setTimeout(() => {
      this.connect();
    }, 4000);
  }

  private startPollingFallback() {
    if (this.pollInterval) return;
    console.warn('[EmergencyRoute WebSocket] Connection inactive. Starting HTTP event polling fallback (3s interval).');
    this.pollInterval = setInterval(async () => {
      try {
        const events = await api.pollRecentEvents(5);
        for (const ev of events) {
          if (!this.lastPolledTimestamp || ev.timestamp > this.lastPolledTimestamp) {
            this.lastPolledTimestamp = ev.timestamp;
            this.notifyListeners(ev.type, ev);
            this.notifyListeners('*', ev);
          }
        }
      } catch (err) {
        // quiet polling failure
      }
    }, 3000);
  }

  private stopPollingFallback() {
    if (this.pollInterval) {
      clearInterval(this.pollInterval);
      this.pollInterval = null;
    }
  }

  public subscribe(eventType: string, callback: EventCallback): () => void {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, new Set());
    }
    this.listeners.get(eventType)!.add(callback);

    return () => {
      this.listeners.get(eventType)?.delete(callback);
    };
  }

  private notifyListeners(eventType: string, payload: any) {
    const callbacks = this.listeners.get(eventType);
    if (callbacks) {
      callbacks.forEach((cb) => {
        try {
          cb(payload);
        } catch (e) {
          console.error('[EmergencyRoute WebSocket Listener Error]', e);
        }
      });
    }
  }
}

export const wsClient = new WebSocketClient();
