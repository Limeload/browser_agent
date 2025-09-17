'use client'

import { useState } from 'react'
import { MessageSquare, Clock, CheckCircle, AlertCircle } from 'lucide-react'
import { Transcript } from '@/store/voiceAgentStore'

interface TranscriptPanelProps {
  transcripts: Transcript[]
}

export function TranscriptPanel({ transcripts }: TranscriptPanelProps) {
  const [selectedTranscript, setSelectedTranscript] = useState<Transcript | null>(null)

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-success-600'
    if (confidence >= 0.6) return 'text-warning-600'
    return 'text-error-600'
  }

  const getConfidenceIcon = (confidence: number) => {
    if (confidence >= 0.8) return <CheckCircle className="w-4 h-4" />
    if (confidence >= 0.6) return <AlertCircle className="w-4 h-4" />
    return <AlertCircle className="w-4 h-4" />
  }

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-gray-900 flex items-center space-x-2">
          <MessageSquare className="w-5 h-5" />
          <span>Transcripts</span>
        </h2>
        <span className="status-indicator status-info">
          {transcripts.length} transcript{transcripts.length !== 1 ? 's' : ''}
        </span>
      </div>

      {transcripts.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <MessageSquare className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p>No transcripts yet. Start recording to see your voice commands.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {transcripts.map((transcript) => (
            <div
              key={transcript.id}
              className={`p-4 rounded-lg border cursor-pointer transition-colors ${
                selectedTranscript?.id === transcript.id
                  ? 'border-primary-500 bg-primary-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
              onClick={() => setSelectedTranscript(transcript)}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <p className="text-gray-900 mb-2">{transcript.text}</p>
                  <div className="flex items-center space-x-4 text-sm text-gray-500">
                    <div className="flex items-center space-x-1">
                      <Clock className="w-4 h-4" />
                      <span>{transcript.timestamp.toLocaleTimeString()}</span>
                    </div>
                    <div className={`flex items-center space-x-1 ${getConfidenceColor(transcript.confidence)}`}>
                      {getConfidenceIcon(transcript.confidence)}
                      <span>{Math.round(transcript.confidence * 100)}%</span>
                    </div>
                    {transcript.isFinal && (
                      <span className="status-indicator status-success text-xs">
                        Final
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Selected Transcript Details */}
      {selectedTranscript && (
        <div className="mt-6 p-4 bg-gray-50 rounded-lg">
          <h3 className="font-medium text-gray-900 mb-2">Transcript Details</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">ID:</span>
              <span className="font-mono text-gray-900">{selectedTranscript.id}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Timestamp:</span>
              <span className="text-gray-900">{selectedTranscript.timestamp.toISOString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Confidence:</span>
              <span className={`font-medium ${getConfidenceColor(selectedTranscript.confidence)}`}>
                {Math.round(selectedTranscript.confidence * 100)}%
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Status:</span>
              <span className="text-gray-900">
                {selectedTranscript.isFinal ? 'Final' : 'Partial'}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
