import React, { useState } from 'react';
import { Globe, Plug, Unplug, Camera, ExternalLink } from 'lucide-react';
import { ConnectionStatus } from '../types';

interface BrowserPanelProps {
  connectionStatus: ConnectionStatus;
  screenshot: string | null;
  onConnect: (url: string) => void;
  onDisconnect: () => void;
  onScreenshot: () => void;
}

export const BrowserPanel: React.FC<BrowserPanelProps> = ({
  connectionStatus,
  screenshot,
  onConnect,
  onDisconnect,
  onScreenshot,
}) => {
  const [targetUrl, setTargetUrl] = useState('https://www.google.com');

  return (
    <div className="card">
      <div className="panel-header">
        <h2 className="text-lg font-mono font-semibold text-gradient flex items-center gap-2">
          <Globe className="w-5 h-5 text-primary-500" />
          Browser Automation
        </h2>
        <div className="flex items-center gap-1">
          <span className={`status-indicator ${connectionStatus.connected ? 'online' : 'offline'}`} />
          <span className="text-sm text-dark-400">
            {connectionStatus.connected ? 'Connected' : 'Not Connected'}
          </span>
        </div>
      </div>

      <div className="space-y-4 mb-6">
        <div>
          <label htmlFor="target-url" className="block text-sm font-medium text-dark-300 mb-2">
            Target URL
          </label>
          <div className="relative">
            <input
              id="target-url"
              type="url"
              value={targetUrl}
              onChange={(e) => setTargetUrl(e.target.value)}
              placeholder="https://example.com"
              className="w-full bg-dark-800 border border-dark-700 rounded-lg px-4 py-3 text-dark-100 placeholder-dark-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all duration-200"
            />
            <ExternalLink className="absolute right-3 top-3 w-4 h-4 text-dark-500" />
          </div>
        </div>

        {connectionStatus.error && (
          <p className="text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded p-2">
            {connectionStatus.error}
          </p>
        )}

        <div className="flex gap-3 flex-wrap">
          <button
            onClick={() => onConnect(targetUrl)}
            disabled={connectionStatus.connected}
            className="btn btn-primary"
          >
            <Plug className="w-4 h-4" />
            Connect
          </button>

          <button
            onClick={onDisconnect}
            disabled={!connectionStatus.connected}
            className="btn btn-danger"
          >
            <Unplug className="w-4 h-4" />
            Disconnect
          </button>

          <button
            onClick={onScreenshot}
            disabled={!connectionStatus.connected}
            className="btn btn-secondary"
          >
            <Camera className="w-4 h-4" />
            Screenshot
          </button>
        </div>
      </div>

      <div className="bg-dark-800 border border-dark-700 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-dark-300 mb-3">Screenshot</h3>
        <div className="min-h-[200px] border-2 border-dashed border-dark-700 rounded-lg flex items-center justify-center bg-dark-950 overflow-hidden">
          {screenshot ? (
            <img
              src={`data:image/png;base64,${screenshot}`}
              alt="Browser screenshot"
              className="w-full h-auto rounded"
            />
          ) : (
            <div className="text-center text-dark-500 p-4">
              <Camera className="w-8 h-8 mx-auto mb-2" />
              <p className="text-sm">No screenshot taken yet</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
