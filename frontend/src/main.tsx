import React, { Component, ErrorInfo, ReactNode } from 'react';
import ReactDOM from 'react-dom/client';
import 'leaflet/dist/leaflet.css';
import './index.css';
import App from './App';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

class RootErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Unhandled React Error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-[#1E1E1C] text-[#D8CBB3] flex flex-col items-center justify-center p-6 text-center">
          <div className="max-w-md bg-[#282826] border border-[#D8CBB3]/30 rounded-2xl p-6 shadow-2xl flex flex-col items-center gap-4">
            <span className="w-12 h-12 rounded-full bg-rose-500/20 text-rose-400 flex items-center justify-center font-bold text-xl">!</span>
            <h1 className="text-lg font-bold text-white">Something went wrong</h1>
            <p className="text-xs text-[#D8CBB3]/70 leading-relaxed">
              {this.state.error?.message || 'An unexpected rendering error occurred.'}
            </p>
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-[#2B6BFF] hover:bg-[#1A55E0] text-white font-semibold text-xs rounded-xl shadow-md transition-all cursor-pointer"
            >
              Reload Application
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <RootErrorBoundary>
      <App />
    </RootErrorBoundary>
  </React.StrictMode>
);

