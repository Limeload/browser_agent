'use client'

import { useState, useEffect, useRef } from 'react'
import { Mic, MicOff, Play, Pause, Download, Trash2 } from 'lucide-react'
import { AudioCapture } from './AudioCapture'
import { TranscriptPanel } from './TranscriptPanel'
import { IntentPanel } from './IntentPanel'
import { ExecutionPanel } from './ExecutionPanel'
import { LogsPanel } from './LogsPanel'
import { useVoiceAgentStore } from '@/store/voiceAgentStore'
import { WebSocketService } from '@/services/websocket'
import toast from 'react-hot-toast'

export function VoiceAgent() {
  const {
    isRecording,
    isProcessing,
    audioLevel,
    transcripts,
    intents,
    executions,
    logs,
    setRecording,
    setProcessing,
    setAudioLevel,
    addTranscript,
    addIntent,
    addExecution,
    addLog,
    clearSession
  } = useVoiceAgentStore()

  const [isConnected, setIsConnected] = useState(false)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const wsService = useRef<WebSocketService | null>(null)

  useEffect(() => {
    // Initialize WebSocket connection
    const initWebSocket = () => {
      const newSessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
      setSessionId(newSessionId)
      
      wsService.current = new WebSocketService(
        `ws://localhost:8000/ws/${newSessionId}`,
        {
          onConnect: () => {
            setIsConnected(true)
            toast.success('Connected to voice agent')
          },
          onDisconnect: () => {
            setIsConnected(false)
            toast.error('Disconnected from voice agent')
          },
          onTranscript: (data) => {
            addTranscript({
              id: `transcript_${Date.now()}`,
              text: data.transcript,
              confidence: data.confidence,
              timestamp: new Date(data.timestamp),
              isFinal: data.is_final
            })
          },
          onIntent: (data) => {
            addIntent({
              id: `intent_${Date.now()}`,
              type: data.intent_type,
              confidence: data.confidence,
              entities: data.entities,
              rawText: data.raw_text,
              actions: data.parsed_actions,
              timestamp: new Date(data.timestamp)
            })
          },
          onExecution: (data) => {
            addExecution({
              id: `execution_${Date.now()}`,
              success: data.success,
              actions: data.actions_executed,
              screenshots: data.screenshots,
              finalUrl: data.final_url,
              executionTime: data.execution_time,
              errorMessage: data.error_message,
              timestamp: new Date(data.timestamp)
            })
          },
          onError: (error) => {
            toast.error(`Error: ${error.message}`)
            addLog({
              id: `log_${Date.now()}`,
              level: 'error',
              service: 'websocket',
              message: error.message,
              timestamp: new Date()
            })
          }
        }
      )
    }

    initWebSocket()

    return () => {
      if (wsService.current) {
        wsService.current.disconnect()
      }
    }
  }, [])

  const handleStartRecording = () => {
    if (!isConnected) {
      toast.error('Not connected to voice agent')
      return
    }

    setRecording(true)
    toast.success('Recording started')
  }

  const handleStopRecording = () => {
    setRecording(false)
    toast.success('Recording stopped')
  }

  const handleClearSession = () => {
    clearSession()
    toast.success('Session cleared')
  }

  const handleExportSession = async () => {
    if (!sessionId) {
      toast.error('No active session to export')
      return
    }

    try {
      const response = await fetch(`http://localhost:8000/api/export/${sessionId}`)
      const data = await response.json()
      
      // Download as JSON file
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `voice-agent-session-${sessionId}.json`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
      
      toast.success('Session exported successfully')
    } catch (error) {
      toast.error('Failed to export session')
    }
  }

  return (
    <div className="space-y-6">
      {/* Audio Controls */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">Voice Controls</h2>
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-success-500' : 'bg-error-500'}`} />
            <span className="text-sm text-gray-600">
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
        </div>
        
        <div className="flex items-center space-x-4">
          <button
            onClick={isRecording ? handleStopRecording : handleStartRecording}
            disabled={!isConnected || isProcessing}
            className={`btn ${isRecording ? 'btn-error' : 'btn-primary'} flex items-center space-x-2`}
          >
            {isRecording ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
            <span>{isRecording ? 'Stop Recording' : 'Start Recording'}</span>
          </button>
          
          <button
            onClick={handleClearSession}
            className="btn btn-secondary flex items-center space-x-2"
          >
            <Trash2 className="w-5 h-5" />
            <span>Clear Session</span>
          </button>
          
          <button
            onClick={handleExportSession}
            disabled={!sessionId}
            className="btn btn-secondary flex items-center space-x-2"
          >
            <Download className="w-5 h-5" />
            <span>Export Session</span>
          </button>
        </div>
        
        {/* Audio Level Indicator */}
        {isRecording && (
          <div className="mt-4">
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-600">Audio Level:</span>
              <div className="flex-1 bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-primary-500 h-2 rounded-full transition-all duration-100"
                  style={{ width: `${audioLevel * 100}%` }}
                />
              </div>
              <span className="text-sm text-gray-600">{Math.round(audioLevel * 100)}%</span>
            </div>
          </div>
        )}
      </div>

      {/* Audio Capture Component */}
      <AudioCapture
        isRecording={isRecording}
        onAudioLevelChange={setAudioLevel}
        onAudioData={(data) => {
          if (wsService.current && isConnected) {
            wsService.current.sendAudio(data)
          }
        }}
      />

      {/* Content Panels */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Transcripts */}
        <TranscriptPanel transcripts={transcripts} />
        
        {/* Intents */}
        <IntentPanel intents={intents} />
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Executions */}
        <ExecutionPanel executions={executions} />
        
        {/* Logs */}
        <LogsPanel logs={logs} />
      </div>
    </div>
  )
}
