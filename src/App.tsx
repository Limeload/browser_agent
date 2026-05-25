import { useState, useEffect, useCallback } from 'react';
import { Header } from './components/Header';
import { VoicePanel } from './components/VoicePanel';
import { IntentPanel } from './components/IntentPanel';
import { BrowserPanel } from './components/BrowserPanel';
import { StatusPanel } from './components/StatusPanel';
import { TTSFeedback } from './components/TTSFeedback';
import { useSocket } from './hooks/useSocket';
import { useTTS } from './hooks/useTTS';
import { VoiceCommand, Metrics, LogEntry, SessionData } from './types';

function App() {
  const { connectionStatus, latestScreenshot, connectToBrowser, disconnectFromBrowser, executeCommand, takeScreenshot } = useSocket();
  const { showFeedback, feedback } = useTTS();
  
  const [currentCommand, setCurrentCommand] = useState<VoiceCommand | null>(null);
  const [metrics, setMetrics] = useState<Metrics>({
    commandsExecuted: 0,
    successfulCommands: 0,
    successRate: 0,
    sessionTime: '00:00:00',
  });
  const [logs, setLogs] = useState<LogEntry[]>([
    {
      timestamp: Date.now(),
      type: 'info',
      message: 'System initialized. Ready for voice commands.',
    },
  ]);
  const [isPaused, setIsPaused] = useState(false);
  const [sessionStartTime] = useState(Date.now());
  const [sessionData, setSessionData] = useState<SessionData>({
    timestamp: Date.now(),
    sessionTime: '00:00:00',
    commandsExecuted: 0,
    successfulCommands: 0,
    commands: [],
    logs: [],
    screenshots: [],
  });

  // Update session timer
  useEffect(() => {
    const interval = setInterval(() => {
      const elapsed = Date.now() - sessionStartTime;
      const hours = Math.floor(elapsed / 3600000);
      const minutes = Math.floor((elapsed % 3600000) / 60000);
      const seconds = Math.floor((elapsed % 60000) / 1000);
      
      const timeString = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
      
      setMetrics(prev => ({ ...prev, sessionTime: timeString }));
      setSessionData(prev => ({ ...prev, sessionTime: timeString }));
    }, 1000);

    return () => clearInterval(interval);
  }, [sessionStartTime]);

  const addLog = useCallback((type: LogEntry['type'], message: string) => {
    const newLog: LogEntry = {
      timestamp: Date.now(),
      type,
      message,
    };
    
    setLogs(prev => [...prev, newLog]);
    setSessionData(prev => ({
      ...prev,
      logs: [...prev.logs, newLog],
    }));
  }, []);

  const handleCommandParsed = useCallback((command: VoiceCommand) => {
    setCurrentCommand(command);
    
    if (command.intent !== 'unknown') {
      executeCommand(command);
      setMetrics(prev => ({
        ...prev,
        commandsExecuted: prev.commandsExecuted + 1,
      }));
      
      addLog('info', `Executing command: ${command.command}`);
      showFeedback(`Executing ${command.command} command`);
    }
  }, [executeCommand, addLog, showFeedback]);

  const handleConnectBrowser = useCallback((url: string) => {
    connectToBrowser(url);
    addLog('info', 'Connecting to browser...');
    showFeedback('Connecting to browser');
  }, [connectToBrowser, addLog, showFeedback]);

  const handleDisconnectBrowser = useCallback(() => {
    disconnectFromBrowser();
    addLog('info', 'Disconnecting from browser...');
    showFeedback('Disconnected from browser');
  }, [disconnectFromBrowser, addLog, showFeedback]);

  const handleScreenshot = useCallback(() => {
    takeScreenshot();
    addLog('info', 'Capturing screenshot...');
    showFeedback('Taking screenshot');
  }, [takeScreenshot, addLog, showFeedback]);

  const handleClearLogs = useCallback(() => {
    setLogs([{
      timestamp: Date.now(),
      type: 'info',
      message: 'Logs cleared',
    }]);
    setSessionData(prev => ({
      ...prev,
      logs: [{
        timestamp: Date.now(),
        type: 'info',
        message: 'Logs cleared',
      }],
    }));
  }, []);

  const handleTogglePause = useCallback(() => {
    setIsPaused(prev => !prev);
    addLog('info', `Logs ${isPaused ? 'resumed' : 'paused'}`);
  }, [isPaused, addLog]);

  const handleSaveSession = useCallback(() => {
    const dataToSave = {
      ...sessionData,
      timestamp: Date.now(),
    };
    
    const blob = new Blob([JSON.stringify(dataToSave, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `voice-browser-session-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
    
    addLog('success', 'Session saved successfully');
    showFeedback('Session saved');
  }, [sessionData, addLog, showFeedback]);

  const handleLoadSession = useCallback(() => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.json';
    input.onchange = (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = (e) => {
          try {
            const sessionData = JSON.parse(e.target?.result as string);
            // Restore session data
            setMetrics({
              commandsExecuted: sessionData.commandsExecuted || 0,
              successfulCommands: sessionData.successfulCommands || 0,
              successRate: sessionData.commandsExecuted > 0 ? 
                Math.round((sessionData.successfulCommands / sessionData.commandsExecuted) * 100) : 0,
              sessionTime: sessionData.sessionTime || '00:00:00',
            });
            setLogs(sessionData.logs || []);
            setSessionData(sessionData);
            
            addLog('success', 'Session loaded successfully');
            showFeedback('Session loaded');
          } catch (error) {
            addLog('error', 'Failed to load session: Invalid file format');
            showFeedback('Failed to load session');
          }
        };
        reader.readAsText(file);
      }
    };
    input.click();
  }, [addLog, showFeedback]);

  const handleExportLogs = useCallback(() => {
    const logsData = {
      exportTime: new Date().toISOString(),
      sessionInfo: {
        duration: metrics.sessionTime,
        commandsExecuted: metrics.commandsExecuted,
        successRate: metrics.successRate,
      },
      logs: logs,
    };
    
    const blob = new Blob([JSON.stringify(logsData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `voice-browser-logs-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
    
    addLog('success', 'Logs exported successfully');
    showFeedback('Logs exported');
  }, [metrics, logs, addLog, showFeedback]);

  return (
    <div className="min-h-screen bg-dark-950">
      <Header
        onSaveSession={handleSaveSession}
        onLoadSession={handleLoadSession}
        onExportLogs={handleExportLogs}
      />
      
      <main className="max-w-7xl mx-auto p-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <VoicePanel
            onCommandParsed={handleCommandParsed}
            connectionStatus={connectionStatus}
          />
          
          <IntentPanel command={currentCommand} />
          
          <BrowserPanel
            connectionStatus={connectionStatus}
            screenshot={latestScreenshot}
            onConnect={handleConnectBrowser}
            onDisconnect={handleDisconnectBrowser}
            onScreenshot={handleScreenshot}
          />
          
          <StatusPanel
            metrics={metrics}
            logs={logs}
            onClearLogs={handleClearLogs}
            onTogglePause={handleTogglePause}
            isPaused={isPaused}
          />
        </div>
      </main>
      
      <TTSFeedback message={feedback.message} visible={feedback.visible} />
    </div>
  );
}

export default App;
