export type ActionType =
  | 'navigate' | 'click' | 'type' | 'scroll' | 'wait'
  | 'screenshot' | 'extract' | 'form_submit'
  | 'back' | 'forward' | 'refresh' | 'multi_step' | 'unknown';

export type Reversibility = 'read' | 'reversible' | 'irreversible';

export interface TaskStep {
  action_type: ActionType;
  target?: string;
  value?: string;
  reversibility: Reversibility;
  description: string;
}

/** Unified command type — populated by the backend /parse API. */
export interface VoiceCommand {
  // Backend TaskIntent fields
  action_type: ActionType;
  reversibility: Reversibility;
  requires_confirmation: boolean;
  confidence: number;
  ambiguity_flags: string[];
  description: string;
  raw_transcript: string;
  target?: string;
  value?: string;
  steps: TaskStep[];
  // Legacy aliases kept for backward compat with existing components
  intent: string;         // mirrors action_type
  type: string;           // coarse category
  params: Record<string, unknown>;
  command: string;        // mirrors action_type
  direction?: string;
  duration?: number;
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
  result?: unknown;
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
  screenshot?: string;  // base64 PNG
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
