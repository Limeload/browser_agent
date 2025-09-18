import { useEffect, useState, useCallback } from 'react';
import { ConnectionStatus } from '../types';

interface UseSocketReturn {
  websocket: WebSocket | null;
  connectionStatus: ConnectionStatus;
  connectToBrowser: (url: string) => void;
  disconnectFromBrowser: () => void;
  executeCommand: (command: any) => void;
  takeScreenshot: () => void;
}

export const useSocket = (): UseSocketReturn => {
  const [websocket, setWebsocket] = useState<WebSocket | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>({
    connected: false,
  });

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws');

    ws.onopen = () => {
      setConnectionStatus({ connected: true });
    };

    ws.onclose = () => {
      setConnectionStatus({ connected: false });
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.type === 'browser-status') {
          setConnectionStatus({
            connected: data.connected,
            sessionId: data.sessionId,
            url: data.url,
            error: data.error,
          });
        }
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setConnectionStatus({ connected: false });
    };

    setWebsocket(ws);

    return () => {
      ws.close();
    };
  }, []);

  const connectToBrowser = useCallback((url: string) => {
    if (websocket && websocket.readyState === WebSocket.OPEN) {
      websocket.send(JSON.stringify({
        type: 'connect-browser',
        url: url
      }));
    }
  }, [websocket]);

  const disconnectFromBrowser = useCallback(() => {
    if (websocket && websocket.readyState === WebSocket.OPEN) {
      websocket.send(JSON.stringify({
        type: 'disconnect-browser',
        sessionId: connectionStatus.sessionId
      }));
    }
  }, [websocket, connectionStatus.sessionId]);

  const executeCommand = useCallback((command: any) => {
    if (websocket && websocket.readyState === WebSocket.OPEN && connectionStatus.sessionId) {
      websocket.send(JSON.stringify({
        type: 'execute-command',
        sessionId: connectionStatus.sessionId,
        command: command
      }));
    }
  }, [websocket, connectionStatus.sessionId]);

  const takeScreenshot = useCallback(() => {
    if (websocket && websocket.readyState === WebSocket.OPEN && connectionStatus.sessionId) {
      websocket.send(JSON.stringify({
        type: 'take-screenshot',
        sessionId: connectionStatus.sessionId
      }));
    }
  }, [websocket, connectionStatus.sessionId]);

  return {
    websocket,
    connectionStatus,
    connectToBrowser,
    disconnectFromBrowser,
    executeCommand,
    takeScreenshot,
  };
};
