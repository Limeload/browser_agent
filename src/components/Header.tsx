import React from 'react';
import { Bot, Save, FolderOpen, Download } from 'lucide-react';

interface HeaderProps {
  onSaveSession: () => void;
  onLoadSession: () => void;
  onExportLogs: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onSaveSession, onLoadSession, onExportLogs }) => {
  return (
    <header className="bg-dark-900 border-b border-dark-800 px-8 py-4 sticky top-0 z-40 backdrop-blur-sm">
      <div className="max-w-7xl mx-auto flex justify-between items-center">
        <div className="flex items-center gap-3">
          <Bot className="w-6 h-6 text-primary-500" />
          <h1 className="text-xl font-mono font-semibold text-gradient">
            Voice Browser Agent
          </h1>
        </div>

        <div className="flex gap-3">
          <button onClick={onSaveSession} className="btn btn-secondary">
            <Save className="w-4 h-4" />
            Save Session
          </button>
          <button onClick={onLoadSession} className="btn btn-secondary">
            <FolderOpen className="w-4 h-4" />
            Load Session
          </button>
          <button onClick={onExportLogs} className="btn btn-secondary">
            <Download className="w-4 h-4" />
            Export Logs
          </button>
        </div>
      </div>
    </header>
  );
};
