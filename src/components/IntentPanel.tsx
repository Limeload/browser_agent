import React from 'react';
import { Brain, Code } from 'lucide-react';
import { VoiceCommand } from '../types';

interface IntentPanelProps {
  command: VoiceCommand | null;
}

export const IntentPanel: React.FC<IntentPanelProps> = ({ command }) => {
  return (
    <div className="card">
      <div className="panel-header">
        <h2 className="text-lg font-mono font-semibold text-gradient flex items-center gap-2">
          <Brain className="w-5 h-5 text-primary-500" />
          Intent Analysis
        </h2>
      </div>

      <div className="space-y-4 mb-6">
        <div className="flex justify-between items-center py-3 border-b border-dark-800">
          <span className="text-sm text-dark-300 font-medium">Detected Intent:</span>
          <span className="text-sm font-mono font-semibold text-primary-500">
            {command?.intent || 'None'}
          </span>
        </div>

        <div className="flex justify-between items-center py-3 border-b border-dark-800">
          <span className="text-sm text-dark-300 font-medium">Command Type:</span>
          <span className="text-sm font-mono font-semibold text-primary-500">
            {command?.type || 'None'}
          </span>
        </div>

        <div className="py-3">
          <span className="text-sm text-dark-300 font-medium block mb-2">Parameters:</span>
          <div className="bg-dark-800 border border-dark-700 rounded-lg p-3">
            <pre className="text-xs font-mono text-dark-200 whitespace-pre-wrap">
              {command?.params ? JSON.stringify(command.params, null, 2) : 'None'}
            </pre>
          </div>
        </div>
      </div>

      <div className="bg-dark-800 border border-dark-700 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-dark-300 mb-3 flex items-center gap-2">
          <Code className="w-4 h-4" />
          Command Structure
        </h3>
        <pre className="text-xs font-mono text-dark-200 bg-dark-950 border border-dark-700 rounded p-3 overflow-x-auto whitespace-pre-wrap">
          {command ? JSON.stringify(command, null, 2) : 'No command detected'}
        </pre>
      </div>
    </div>
  );
};
