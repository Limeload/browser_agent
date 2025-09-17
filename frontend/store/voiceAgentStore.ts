import { create } from 'zustand'
import { subscribeWithSelector } from 'zustand/middleware'

export interface Transcript {
  id: string
  text: string
  confidence: number
  timestamp: Date
  isFinal: boolean
}

export interface Intent {
  id: string
  type: string
  confidence: number
  entities: Record<string, any>
  rawText: string
  actions: any[]
  timestamp: Date
}

export interface Execution {
  id: string
  success: boolean
  actions: any[]
  screenshots: string[]
  finalUrl?: string
  executionTime: number
  errorMessage?: string
  timestamp: Date
}

export interface LogEntry {
  id: string
  level: string
  service: string
  message: string
  timestamp: Date
  metadata?: Record<string, any>
}

interface VoiceAgentState {
  // Connection state
  isConnected: boolean
  sessionId: string | null
  
  // Audio state
  isRecording: boolean
  isProcessing: boolean
  audioLevel: number
  
  // Data
  transcripts: Transcript[]
  intents: Intent[]
  executions: Execution[]
  logs: LogEntry[]
  
  // UI state
  activeTab: 'agent' | 'sessions' | 'monitoring'
  selectedSession: string | null
  
  // Actions
  setConnected: (connected: boolean) => void
  setSessionId: (sessionId: string | null) => void
  setRecording: (recording: boolean) => void
  setProcessing: (processing: boolean) => void
  setAudioLevel: (level: number) => void
  addTranscript: (transcript: Transcript) => void
  addIntent: (intent: Intent) => void
  addExecution: (execution: Execution) => void
  addLog: (log: LogEntry) => void
  setActiveTab: (tab: 'agent' | 'sessions' | 'monitoring') => void
  setSelectedSession: (sessionId: string | null) => void
  clearSession: () => void
}

export const useVoiceAgentStore = create<VoiceAgentState>()(
  subscribeWithSelector((set, get) => ({
    // Initial state
    isConnected: false,
    sessionId: null,
    isRecording: false,
    isProcessing: false,
    audioLevel: 0,
    transcripts: [],
    intents: [],
    executions: [],
    logs: [],
    activeTab: 'agent',
    selectedSession: null,
    
    // Actions
    setConnected: (connected) => set({ isConnected: connected }),
    setSessionId: (sessionId) => set({ sessionId }),
    setRecording: (recording) => set({ isRecording: recording }),
    setProcessing: (processing) => set({ isProcessing: processing }),
    setAudioLevel: (level) => set({ audioLevel: level }),
    
    addTranscript: (transcript) => set((state) => ({
      transcripts: [...state.transcripts, transcript]
    })),
    
    addIntent: (intent) => set((state) => ({
      intents: [...state.intents, intent]
    })),
    
    addExecution: (execution) => set((state) => ({
      executions: [...state.executions, execution]
    })),
    
    addLog: (log) => set((state) => ({
      logs: [...state.logs, log].slice(-100) // Keep last 100 logs
    })),
    
    setActiveTab: (tab) => set({ activeTab: tab }),
    setSelectedSession: (sessionId) => set({ selectedSession: sessionId }),
    
    clearSession: () => set({
      transcripts: [],
      intents: [],
      executions: [],
      logs: [],
      sessionId: null
    })
  }))
)
