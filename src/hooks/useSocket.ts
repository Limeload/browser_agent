import { useEffect, useState, useCallback } from 'react';
import { ConnectionStatus } from '../types';
import { PendingAction } from '../components/HITLModal';

interface InjectionAlert {
  text: string;
  detections: Array<{ attack_type: string; confidence: number }>;
}

interface UseSocketReturn {
  websocket: WebSocket | null;
  connectionStatus: ConnectionStatus;
  latestScreenshot: string | null;
  pendingAction: PendingAction | null;
  injectionAlert: InjectionAlert | null;
  connectToBrowser: (url: string) => void;
  disconnectFromBrowser: () => void;
  executeCommand: (command: unknown) => void;
  takeScreenshot: () => void;
  approveAction: (actionId: string, modifiedIntent?: Record<string, unknown>) => void;
  denyAction: (actionId: string) => void;
  dismissInjectionAlert: () => void;
}

export const useSocket = (): UseSocketReturn => {
  const [websocket, setWebsocket] = useState<WebSocket | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>({ connected: false });
  const [latestScreenshot, setLatestScreenshot] = useState<string | null>(null);
  const [pendingAction, setPendingAction] = useState<PendingAction | null>(null);
  const [injectionAlert, setInjectionAlert] = useState<InjectionAlert | null>(null);

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
      } else if (data.type === 'action-pending') {
        setPendingAction({
          actionId: data.actionId as string,
          actionType: data.actionType as string,
          reversibility: data.reversibility as string,
          description: data.description as string,
          target: data.target as string | undefined,
        });
      } else if (data.type === 'action-denied') {
        setPendingAction(null);
      } else if (data.type === 'command-result') {
        setPendingAction(null);
      } else if (data.type === 'injection-blocked') {
        setInjectionAlert({
          text: data.text as string,
          detections: data.detections as Array<{ attack_type: string; confidence: number }>,
        });
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

  const approveAction = useCallback((actionId: string, modifiedIntent?: Record<string, unknown>) => {
    if (websocket?.readyState === WebSocket.OPEN) {
      websocket.send(JSON.stringify({
        type: 'approve-action',
        actionId,
        ...(modifiedIntent ? { modifiedIntent } : {}),
      }));
    }
    setPendingAction(null);
  }, [websocket]);

  const denyAction = useCallback((actionId: string) => {
    if (websocket?.readyState === WebSocket.OPEN) {
      websocket.send(JSON.stringify({ type: 'deny-action', actionId }));
    }
    setPendingAction(null);
  }, [websocket]);

  const dismissInjectionAlert = useCallback(() => {
    setInjectionAlert(null);
  }, []);

  return {
    websocket,
    connectionStatus,
    latestScreenshot,
    pendingAction,
    injectionAlert,
    connectToBrowser,
    disconnectFromBrowser,
    executeCommand,
    takeScreenshot,
    approveAction,
    denyAction,
    dismissInjectionAlert,
  };
};
