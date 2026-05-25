import React from 'react';
import { Brain, Code, AlertTriangle, ShieldAlert } from 'lucide-react';
import { VoiceCommand, Reversibility } from '../types';

interface IntentPanelProps {
  command: VoiceCommand | null;
}

const reversibilityColor: Record<Reversibility, string> = {
  read: 'text-blue-400',
  reversible: 'text-green-400',
  irreversible: 'text-red-400',
};

export const IntentPanel: React.FC<IntentPanelProps> = ({ command }) => {
  const rev = command?.reversibility;

  return (
    <div className="card">
      <div className="panel-header">
        <h2 className="text-lg font-mono font-semibold text-gradient flex items-center gap-2">
          <Brain className="w-5 h-5 text-primary-500" />
          Intent Analysis
        </h2>
        {command?.requires_confirmation && (
          <span className="flex items-center gap-1 text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded px-2 py-1">
            <ShieldAlert className="w-3 h-3" />
            Requires approval
          </span>
        )}
      </div>

      <div className="space-y-1 mb-6">
        <Row label="Action" value={command?.action_type ?? 'None'} />

        <Row
          label="Reversibility"
          value={rev ?? 'None'}
          valueClass={rev ? reversibilityColor[rev] : ''}
        />

        <Row
          label="Confidence"
          value={
            command
              ? `${Math.round(command.confidence * 100)}%`
              : 'None'
          }
        />

        <Row label="Target" value={command?.target ?? '—'} />

        {command?.description && (
          <div className="flex justify-between items-start py-3 border-b border-dark-800">
            <span className="text-sm text-dark-300 font-medium">Description:</span>
            <span className="text-sm font-mono text-dark-100 text-right max-w-[60%]">
              {command.description}
            </span>
          </div>
        )}
      </div>

      {command?.ambiguity_flags && command.ambiguity_flags.length > 0 && (
        <div className="mb-4 p-3 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
          <div className="flex items-center gap-2 text-xs font-semibold text-yellow-400 mb-2">
            <AlertTriangle className="w-3 h-3" />
            Ambiguity detected
          </div>
          <ul className="space-y-1">
            {command.ambiguity_flags.map((flag, i) => (
              <li key={i} className="text-xs text-yellow-300">• {flag}</li>
            ))}
          </ul>
        </div>
      )}

      {command?.steps && command.steps.length > 0 && (
        <div className="mb-4">
          <h3 className="text-sm font-semibold text-dark-300 mb-2">Steps</h3>
          <ol className="space-y-1">
            {command.steps.map((step, i) => (
              <li key={i} className="text-xs font-mono text-dark-200 bg-dark-800 rounded p-2">
                {i + 1}. {step.action_type}
                {step.target ? ` → ${step.target}` : ''}
                {step.value ? ` "${step.value}"` : ''}
              </li>
            ))}
          </ol>
        </div>
      )}

      <div className="bg-dark-800 border border-dark-700 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-dark-300 mb-3 flex items-center gap-2">
          <Code className="w-4 h-4" />
          Raw JSON
        </h3>
        <pre className="text-xs font-mono text-dark-200 bg-dark-950 border border-dark-700 rounded p-3 overflow-x-auto whitespace-pre-wrap">
          {command ? JSON.stringify(command, null, 2) : 'No command parsed yet'}
        </pre>
      </div>
    </div>
  );
};

function Row({
  label,
  value,
  valueClass = 'text-primary-500',
}: {
  label: string;
  value: string;
  valueClass?: string;
}) {
  return (
    <div className="flex justify-between items-center py-3 border-b border-dark-800">
      <span className="text-sm text-dark-300 font-medium">{label}:</span>
      <span className={`text-sm font-mono font-semibold ${valueClass}`}>{value}</span>
    </div>
  );
}
