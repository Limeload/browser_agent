export interface VoiceCommand {
  intent: string;
  type: 'navigation' | 'interaction' | 'capture' | 'timing' | 'unknown';
  params: Record<string, any>;
  command: string;
  target?: string;
  value?: string;
  duration?: number;
  direction?: string;
}

export interface SessionData {
  timestamp: number;
  sessionTime: string;
  commandsExecuted: number;
  successfulCommands: number;
  commands: CommandResult[];
  logs: LogEntry[];
  screenshots: ScreenshotResult[];
}

export interface CommandResult {
  success: boolean;
  command: string;
  result?: any;
  error?: string;
  timestamp: number;
}

export interface LogEntry {
  timestamp: number;
  type: 'info' | 'success' | 'warning' | 'error';
  message: string;
}

export interface ScreenshotResult {
  success: boolean;
  screenshot?: string;
  error?: string;
  timestamp: string;
}

export interface BrowserSession {
  id: string;
  url: string;
  connected: boolean;
  createdAt: Date;
}

export interface ConnectionStatus {
  connected: boolean;
  sessionId?: string;
  url?: string;
  error?: string;
}

export interface Metrics {
  commandsExecuted: number;
  successfulCommands: number;
  successRate: number;
  sessionTime: string;
}

export interface TTSFeedback {
  message: string;
  visible: boolean;
}

export interface VoiceRecognitionState {
  isListening: boolean;
  transcript: string;
  confidence: number;
  isSupported: boolean;
}

export interface IntentDisplay {
  detectedIntent: string;
  commandType: string;
  parameters: Record<string, any>;
  commandStructure: VoiceCommand;
}
