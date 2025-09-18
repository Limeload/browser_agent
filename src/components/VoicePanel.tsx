import React from 'react';
import { Mic, MicOff } from 'lucide-react';
import { useVoiceRecognition } from '../hooks/useVoiceRecognition';
import { VoiceCommand } from '../types';

interface VoicePanelProps {
  onCommandParsed: (command: VoiceCommand) => void;
  connectionStatus: {
    connected: boolean;
  };
}

export const VoicePanel: React.FC<VoicePanelProps> = ({ onCommandParsed, connectionStatus }) => {
  const { state, toggleListening, parseIntent } = useVoiceRecognition();

  React.useEffect(() => {
    if (state.transcript) {
      const command = parseIntent(state.transcript);
      onCommandParsed(command);
    }
  }, [state.transcript, parseIntent, onCommandParsed]);

  return (
    <div className="card col-span-2">
      <div className="panel-header">
        <h2 className="text-lg font-mono font-semibold text-gradient flex items-center gap-2">
          <Mic className="w-5 h-5 text-primary-500" />
          Voice Control
        </h2>
        <div className="flex items-center">
          <span className={`status-indicator ${connectionStatus.connected ? 'online' : 'offline'}`}></span>
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
            <>
              <MicOff className="w-4 h-4" />
              Stop Voice Control
            </>
          ) : (
            <>
              <Mic className="w-4 h-4" />
              Start Voice Control
            </>
          )}
        </button>

        <div className="flex-1 max-w-xs">
          <div className={`wave-container flex items-center justify-center gap-1 h-10 ${state.isListening ? 'active' : ''}`}>
            {Array.from({ length: 5 }, (_, i) => (
              <div
                key={i}
                className="wave-bar"
                style={{ height: `${8 + i * 4}px` }}
              />
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
            {state.transcript || 'Click "Start Voice Control" to begin...'}
          </p>
        </div>
      </div>

      {!state.isSupported && (
        <div className="mt-4 p-4 bg-red-500/10 border border-red-500/20 rounded-lg">
          <p className="text-sm text-red-400">
            Speech recognition is not supported in this browser. Please use Chrome or Edge.
          </p>
        </div>
      )}
    </div>
  );
};
