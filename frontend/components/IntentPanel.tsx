'use client'

import { useState } from 'react'
import { Brain, Clock, CheckCircle, AlertCircle, Eye } from 'lucide-react'
import { Intent } from '@/store/voiceAgentStore'

interface IntentPanelProps {
  intents: Intent[]
}

export function IntentPanel({ intents }: IntentPanelProps) {
  const [selectedIntent, setSelectedIntent] = useState<Intent | null>(null)

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

  const getIntentTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      navigation: 'bg-blue-100 text-blue-800',
      search: 'bg-green-100 text-green-800',
      click_action: 'bg-purple-100 text-purple-800',
      form_filling: 'bg-yellow-100 text-yellow-800',
      scroll_action: 'bg-orange-100 text-orange-800',
      data_extraction: 'bg-pink-100 text-pink-800',
      unknown: 'bg-gray-100 text-gray-800'
    }
    return colors[type] || colors.unknown
  }

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-gray-900 flex items-center space-x-2">
          <Brain className="w-5 h-5" />
          <span>Intents</span>
        </h2>
        <span className="status-indicator status-info">
          {intents.length} intent{intents.length !== 1 ? 's' : ''}
        </span>
      </div>

      {intents.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <Brain className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p>No intents parsed yet. Speak a command to see parsed intents.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {intents.map((intent) => (
            <div
              key={intent.id}
              className={`p-4 rounded-lg border cursor-pointer transition-colors ${
                selectedIntent?.id === intent.id
                  ? 'border-primary-500 bg-primary-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
              onClick={() => setSelectedIntent(intent)}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-2">
                    <span className={`status-indicator ${getIntentTypeColor(intent.type)}`}>
                      {intent.type.replace('_', ' ')}
                    </span>
                    <div className={`flex items-center space-x-1 ${getConfidenceColor(intent.confidence)}`}>
                      {getConfidenceIcon(intent.confidence)}
                      <span className="text-sm">{Math.round(intent.confidence * 100)}%</span>
                    </div>
                  </div>
                  
                  <p className="text-gray-900 mb-2">{intent.rawText}</p>
                  
                  <div className="flex items-center space-x-4 text-sm text-gray-500">
                    <div className="flex items-center space-x-1">
                      <Clock className="w-4 h-4" />
                      <span>{intent.timestamp.toLocaleTimeString()}</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <Eye className="w-4 h-4" />
                      <span>{intent.actions.length} action{intent.actions.length !== 1 ? 's' : ''}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Selected Intent Details */}
      {selectedIntent && (
        <div className="mt-6 p-4 bg-gray-50 rounded-lg">
          <h3 className="font-medium text-gray-900 mb-3">Intent Details</h3>
          
          <div className="space-y-3">
            <div>
              <span className="text-sm text-gray-600">Raw Text:</span>
              <p className="text-gray-900 font-medium">{selectedIntent.rawText}</p>
            </div>
            
            <div>
              <span className="text-sm text-gray-600">Type:</span>
              <span className={`ml-2 status-indicator ${getIntentTypeColor(selectedIntent.type)}`}>
                {selectedIntent.type.replace('_', ' ')}
              </span>
            </div>
            
            <div>
              <span className="text-sm text-gray-600">Confidence:</span>
              <span className={`ml-2 font-medium ${getConfidenceColor(selectedIntent.confidence)}`}>
                {Math.round(selectedIntent.confidence * 100)}%
              </span>
            </div>
            
            {Object.keys(selectedIntent.entities).length > 0 && (
              <div>
                <span className="text-sm text-gray-600">Entities:</span>
                <div className="mt-1 space-y-1">
                  {Object.entries(selectedIntent.entities).map(([key, value]) => (
                    <div key={key} className="flex justify-between text-sm">
                      <span className="text-gray-600">{key}:</span>
                      <span className="text-gray-900 font-mono">{String(value)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {selectedIntent.actions.length > 0 && (
              <div>
                <span className="text-sm text-gray-600">Actions:</span>
                <div className="mt-1 space-y-1">
                  {selectedIntent.actions.map((action, index) => (
                    <div key={index} className="text-sm bg-white p-2 rounded border">
                      <div className="font-medium text-gray-900">{action.action_type}</div>
                      {action.selector && (
                        <div className="text-gray-600">Selector: {action.selector}</div>
                      )}
                      {action.text && (
                        <div className="text-gray-600">Text: {action.text}</div>
                      )}
                      {action.url && (
                        <div className="text-gray-600">URL: {action.url}</div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            <div className="text-xs text-gray-500">
              <span>Timestamp: {selectedIntent.timestamp.toISOString()}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
