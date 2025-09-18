import React from 'react';
import { Activity, Trash2, Pause, Play } from 'lucide-react';
import { Metrics, LogEntry } from '../types';

interface StatusPanelProps {
  metrics: Metrics;
  logs: LogEntry[];
  onClearLogs: () => void;
  onTogglePause: () => void;
  isPaused: boolean;
}

export const StatusPanel: React.FC<StatusPanelProps> = ({
  metrics,
  logs,
  onClearLogs,
  onTogglePause,
  isPaused,
}) => {
  return (
    <div className="card col-span-2">
      <div className="panel-header">
        <h2 className="text-lg font-mono font-semibold text-gradient flex items-center gap-2">
          <Activity className="w-5 h-5 text-primary-500" />
          Live Status
        </h2>
        <div className="flex gap-2">
          <button onClick={onClearLogs} className="btn btn-small btn-secondary">
            <Trash2 className="w-3 h-3" />
            Clear
          </button>
          <button onClick={onTogglePause} className="btn btn-small btn-secondary">
            {isPaused ? <Play className="w-3 h-3" /> : <Pause className="w-3 h-3" />}
            {isPaused ? 'Resume' : 'Pause'}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="metric-card">
          <span className="metric-label">Commands Executed</span>
          <span className="metric-value">{metrics.commandsExecuted}</span>
        </div>

        <div className="metric-card">
          <span className="metric-label">Success Rate</span>
          <span className="metric-value">{metrics.successRate}%</span>
        </div>

        <div className="metric-card">
          <span className="metric-label">Session Time</span>
          <span className="metric-value">{metrics.sessionTime}</span>
        </div>
      </div>

      <div className="bg-dark-800 border border-dark-700 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-dark-300 mb-3">Execution Logs</h3>
        <div className="max-h-[300px] overflow-y-auto bg-dark-950 border border-dark-700 rounded-lg p-3">
          {logs.length === 0 ? (
            <div className="text-center text-dark-500 py-8">
              <Activity className="w-8 h-8 mx-auto mb-2" />
              <p className="text-sm">No logs yet</p>
            </div>
          ) : (
            logs.map((log, index) => (
              <div key={index} className={`log-entry ${log.type}`}>
                <span className="text-dark-500 min-w-[60px]">
                  {new Date(log.timestamp).toLocaleTimeString()}
                </span>
                <span className="min-w-[50px]">{log.type.toUpperCase()}</span>
                <span className="text-dark-100 flex-1">{log.message}</span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
