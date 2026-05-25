import React, { useState } from 'react';
import { Mic, MicOff, Loader } from 'lucide-react';
import { useVoiceRecognition } from '../hooks/useVoiceRecognition';
import { VoiceCommand, ActionType, Reversibility } from '../types';

interface VoicePanelProps {
  onCommandParsed: (command: VoiceCommand) => void;
  connectionStatus: { connected: boolean };
}

// Coarse category label for legacy `type` field
function actionCategory(action: ActionType): string {
  if (['navigate', 'back', 'forward', 'refresh'].includes(action)) return 'navigation';
  if (['click', 'type', 'scroll', 'form_submit'].includes(action)) return 'interaction';
  if (['screenshot', 'extract'].includes(action)) return 'capture';
  if (action === 'wait') return 'timing';
  if (action === 'multi_step') return 'multi-step';
  return 'unknown';
}

function adaptApiResponse(data: Record<string, unknown>, transcript: string): VoiceCommand {
  const action = (data.action_type as ActionType) ?? 'unknown';
  return {
    action_type: action,
    reversibility: (data.reversibility as Reversibility) ?? 'reversible',
    requires_confirmation: Boolean(data.requires_confirmation),
    confidence: Number(data.confidence ?? 0),
    ambiguity_flags: (data.ambiguity_flags as string[]) ?? [],
    description: String(data.description ?? ''),
    raw_transcript: transcript,
    target: data.target as string | undefined,
    value: data.value as string | undefined,
    steps: (data.steps as VoiceCommand['steps']) ?? [],
    // Legacy aliases
    intent: action,
    type: actionCategory(action),
    params: { target: data.target, value: data.value },
    command: action,
  };
}

// Rule-based local fallback used when the backend is unreachable
function localParse(transcript: string): VoiceCommand {
  const t = transcript.toLowerCase().trim();
  let action: ActionType = 'unknown';
  let target: string | undefined;
  let value: string | undefined;

  if (/go to|navigate to|visit/.test(t)) {
    action = 'navigate';
    const m = t.match(/(?:https?:\/\/)?(?:www\.)?([a-z0-9-]+\.[a-z]{2,})/);
    target = m ? (m[0].startsWith('http') ? m[0] : `https://${m[0]}`) : undefined;
  } else if (/click|press|tap/.test(t)) {
    action = 'click';
    target = t.includes('button') ? 'button' : t.includes('link') ? 'a' : 'button';
  } else if (/type|enter|input/.test(t)) {
    action = 'type';
    const m = t.match(/(?:type|enter|input)\s+(.+?)(?:\s+(?:into|in|on)\s+(.+))?$/);
    if (m) { value = m[1]; target = m[2] ?? 'input'; }
  } else if (/scroll/.test(t)) {
    action = 'scroll';
  } else if (/wait|pause/.test(t)) {
    action = 'wait';
  } else if (/screenshot|capture/.test(t)) {
    action = 'screenshot';
  } else if (/go back|back/.test(t)) {
    action = 'back';
  } else if (/refresh|reload/.test(t)) {
    action = 'refresh';
  }

  return {
    action_type: action,
    reversibility: action === 'screenshot' ? 'read' : 'reversible',
    requires_confirmation: false,
    confidence: 0.5,
    ambiguity_flags: action === 'unknown' ? ['Could not determine intent (offline parse)'] : [],
    description: `${action}${target ? ` → ${target}` : ''}`,
    raw_transcript: transcript,
    target,
    value,
    steps: [],
    intent: action,
    type: actionCategory(action),
    params: { target, value },
    command: action,
  };
}

export const VoicePanel: React.FC<VoicePanelProps> = ({ onCommandParsed, connectionStatus }) => {
  const { state, toggleListening } = useVoiceRecognition();
  const [isParsing, setIsParsing] = useState(false);
  const lastTranscriptRef = React.useRef('');

  React.useEffect(() => {
    const transcript = state.transcript.trim();
    if (!transcript || transcript === lastTranscriptRef.current || isParsing) return;
    lastTranscriptRef.current = transcript;

    setIsParsing(true);
    fetch('/parse', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ transcript }),
    })
      .then(res => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json() as Promise<Record<string, unknown>>;
      })
      .then(data => onCommandParsed(adaptApiResponse(data, transcript)))
      .catch(() => onCommandParsed(localParse(transcript)))
      .finally(() => setIsParsing(false));
  }, [state.transcript, isParsing, onCommandParsed]);

  return (
    <div className="card col-span-2">
      <div className="panel-header">
        <h2 className="text-lg font-mono font-semibold text-gradient flex items-center gap-2">
          <Mic className="w-5 h-5 text-primary-500" />
          Voice Control
        </h2>
        <div className="flex items-center gap-2">
          {isParsing && <Loader className="w-4 h-4 text-primary-500 animate-spin" />}
          <span className={`status-indicator ${connectionStatus.connected ? 'online' : 'offline'}`} />
          <span className="text-sm text-dark-400">
            {connectionStatus.connected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
      </div>

      <div className="flex items-center gap-8 mb-8">
        <button
          onClick={toggleListening}
          disabled={!state.isSupported}
          className={`btn ${state.isListening ? 'btn-danger' : 'btn-primary'} ${
            state.isListening ? 'animate-pulse-slow' : ''
          }`}
        >
          {state.isListening ? (
            <><MicOff className="w-4 h-4" /> Stop Listening</>
          ) : (
            <><Mic className="w-4 h-4" /> Start Listening</>
          )}
        </button>

        <div className="flex-1 max-w-xs">
          <div className={`wave-container flex items-center justify-center gap-1 h-10 ${state.isListening ? 'active' : ''}`}>
            {Array.from({ length: 5 }, (_, i) => (
              <div key={i} className="wave-bar" style={{ height: `${8 + i * 4}px` }} />
            ))}
          </div>
        </div>
      </div>

      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <h3 className="text-sm font-semibold text-dark-300">Live Transcription</h3>
          <div className="flex items-center gap-2 text-xs text-dark-400">
            <span>Confidence:</span>
            <div className="w-16 h-1 bg-dark-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-red-500 via-yellow-500 to-green-500 transition-all duration-300"
                style={{ width: `${state.confidence * 100}%` }}
              />
            </div>
            <span>{Math.round(state.confidence * 100)}%</span>
          </div>
        </div>

        <div className="bg-dark-950 border border-dark-800 rounded-lg p-4 min-h-[80px]">
          <p className="text-sm font-mono text-dark-100 leading-relaxed">
            {state.transcript || 'Click "Start Listening" to begin...'}
          </p>
        </div>
      </div>

      {!state.isSupported && (
        <div className="mt-4 p-4 bg-red-500/10 border border-red-500/20 rounded-lg">
          <p className="text-sm text-red-400">
            Speech recognition is not supported in this browser. Use Chrome or Edge.
          </p>
        </div>
      )}
    </div>
  );
};
