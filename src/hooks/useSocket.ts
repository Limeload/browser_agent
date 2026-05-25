import { useEffect, useState, useCallback } from 'react';
import { ConnectionStatus } from '../types';

interface UseSocketReturn {
  websocket: WebSocket | null;
  connectionStatus: ConnectionStatus;
  latestScreenshot: string | null;
  connectToBrowser: (url: string) => void;
  disconnectFromBrowser: () => void;
  executeCommand: (command: unknown) => void;
  takeScreenshot: () => void;
}

export const useSocket = (): UseSocketReturn => {
  const [websocket, setWebsocket] = useState<WebSocket | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>({ connected: false });
  const [latestScreenshot, setLatestScreenshot] = useState<string | null>(null);

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws');

    ws.onopen = () => setConnectionStatus(prev => ({ ...prev, connected: true }));
    ws.onclose = () => setConnectionStatus({ connected: false });

    ws.onmessage = (event) => {
      let data: Record<string, unknown>;
      try {
        data = JSON.parse(event.data as string);
      } catch {
        return;
      }

      if (data.type === 'browser-status') {
        setConnectionStatus({
          connected: Boolean(data.connected),
          sessionId: data.sessionId as string | undefined,
          url: data.url as string | undefined,
          error: data.error as string | undefined,
        });
      } else if (data.type === 'screenshot-result' && data.success && data.screenshot) {
        setLatestScreenshot(data.screenshot as string);
      }
    };

    ws.onerror = () => setConnectionStatus({ connected: false });

    setWebsocket(ws);
    return () => ws.close();
  }, []);

  const connectToBrowser = useCallback((url: string) => {
    if (websocket?.readyState === WebSocket.OPEN) {
      websocket.send(JSON.stringify({ type: 'connect-browser', url }));
    }
  }, [websocket]);

  const disconnectFromBrowser = useCallback(() => {
    if (websocket?.readyState === WebSocket.OPEN) {
      websocket.send(JSON.stringify({
        type: 'disconnect-browser',
        sessionId: connectionStatus.sessionId,
      }));
    }
  }, [websocket, connectionStatus.sessionId]);

  const executeCommand = useCallback((command: unknown) => {
    if (websocket?.readyState === WebSocket.OPEN && connectionStatus.sessionId) {
      websocket.send(JSON.stringify({
        type: 'execute-command',
        sessionId: connectionStatus.sessionId,
        command,
      }));
    }
  }, [websocket, connectionStatus.sessionId]);

  const takeScreenshot = useCallback(() => {
    if (websocket?.readyState === WebSocket.OPEN && connectionStatus.sessionId) {
      websocket.send(JSON.stringify({
        type: 'take-screenshot',
        sessionId: connectionStatus.sessionId,
      }));
    }
  }, [websocket, connectionStatus.sessionId]);

  return {
    websocket,
    connectionStatus,
    latestScreenshot,
    connectToBrowser,
    disconnectFromBrowser,
    executeCommand,
    takeScreenshot,
  };
};
