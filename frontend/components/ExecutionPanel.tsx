'use client'

import { useState } from 'react'
import { Play, Clock, CheckCircle, XCircle, Image, ExternalLink } from 'lucide-react'
import { Execution } from '@/store/voiceAgentStore'

interface ExecutionPanelProps {
  executions: Execution[]
}

export function ExecutionPanel({ executions }: ExecutionPanelProps) {
  const [selectedExecution, setSelectedExecution] = useState<Execution | null>(null)

  const getStatusColor = (success: boolean) => {
    return success ? 'text-success-600' : 'text-error-600'
  }

  const getStatusIcon = (success: boolean) => {
    return success ? <CheckCircle className="w-4 h-4" /> : <XCircle className="w-4 h-4" />
  }

  const getStatusBadge = (success: boolean) => {
    return success ? 'status-success' : 'status-error'
  }

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-gray-900 flex items-center space-x-2">
          <Play className="w-5 h-5" />
          <span>Executions</span>
        </h2>
        <span className="status-indicator status-info">
          {executions.length} execution{executions.length !== 1 ? 's' : ''}
        </span>
      </div>

      {executions.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <Play className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p>No executions yet. Commands will be executed here.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {executions.map((execution) => (
            <div
              key={execution.id}
              className={`p-4 rounded-lg border cursor-pointer transition-colors ${
                selectedExecution?.id === execution.id
                  ? 'border-primary-500 bg-primary-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
              onClick={() => setSelectedExecution(execution)}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-2">
                    <span className={`status-indicator ${getStatusBadge(execution.success)}`}>
                      {execution.success ? 'Success' : 'Failed'}
                    </span>
                    <div className={`flex items-center space-x-1 ${getStatusColor(execution.success)}`}>
                      {getStatusIcon(execution.success)}
                      <span className="text-sm">{execution.executionTime.toFixed(2)}s</span>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-4 text-sm text-gray-500 mb-2">
                    <div className="flex items-center space-x-1">
                      <Clock className="w-4 h-4" />
                      <span>{execution.timestamp.toLocaleTimeString()}</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <Play className="w-4 h-4" />
                      <span>{execution.actions.length} action{execution.actions.length !== 1 ? 's' : ''}</span>
                    </div>
                    {execution.screenshots.length > 0 && (
                      <div className="flex items-center space-x-1">
                        <Image className="w-4 h-4" />
                        <span>{execution.screenshots.length} screenshot{execution.screenshots.length !== 1 ? 's' : ''}</span>
                      </div>
                    )}
                  </div>
                  
                  {execution.finalUrl && (
                    <div className="flex items-center space-x-1 text-sm text-gray-600">
                      <ExternalLink className="w-4 h-4" />
                      <span className="truncate">{execution.finalUrl}</span>
                    </div>
                  )}
                  
                  {execution.errorMessage && (
                    <div className="mt-2 p-2 bg-error-50 border border-error-200 rounded text-sm text-error-700">
                      {execution.errorMessage}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Selected Execution Details */}
      {selectedExecution && (
        <div className="mt-6 p-4 bg-gray-50 rounded-lg">
          <h3 className="font-medium text-gray-900 mb-3">Execution Details</h3>
          
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-600">Status:</span>
                <span className={`ml-2 status-indicator ${getStatusBadge(selectedExecution.success)}`}>
                  {selectedExecution.success ? 'Success' : 'Failed'}
                </span>
              </div>
              <div>
                <span className="text-gray-600">Duration:</span>
                <span className="ml-2 text-gray-900">{selectedExecution.executionTime.toFixed(2)}s</span>
              </div>
            </div>
            
            {selectedExecution.finalUrl && (
              <div>
                <span className="text-sm text-gray-600">Final URL:</span>
                <div className="mt-1 text-sm text-gray-900 break-all">{selectedExecution.finalUrl}</div>
              </div>
            )}
            
            {selectedExecution.errorMessage && (
              <div>
                <span className="text-sm text-gray-600">Error:</span>
                <div className="mt-1 p-2 bg-error-50 border border-error-200 rounded text-sm text-error-700">
                  {selectedExecution.errorMessage}
                </div>
              </div>
            )}
            
            {selectedExecution.actions.length > 0 && (
              <div>
                <span className="text-sm text-gray-600">Actions Executed:</span>
                <div className="mt-1 space-y-2">
                  {selectedExecution.actions.map((action, index) => (
                    <div key={index} className="text-sm bg-white p-3 rounded border">
                      <div className="font-medium text-gray-900 mb-1">
                        {index + 1}. {action.action_type}
                      </div>
                      {action.selector && (
                        <div className="text-gray-600 mb-1">
                          <span className="font-medium">Selector:</span> {action.selector}
                        </div>
                      )}
                      {action.text && (
                        <div className="text-gray-600 mb-1">
                          <span className="font-medium">Text:</span> {action.text}
                        </div>
                      )}
                      {action.url && (
                        <div className="text-gray-600 mb-1">
                          <span className="font-medium">URL:</span> {action.url}
                        </div>
                      )}
                      {action.wait_time && (
                        <div className="text-gray-600 mb-1">
                          <span className="font-medium">Wait Time:</span> {action.wait_time}s
                        </div>
                      )}
                      {action.metadata && Object.keys(action.metadata).length > 0 && (
                        <div className="text-gray-600">
                          <span className="font-medium">Metadata:</span>
                          <pre className="mt-1 text-xs bg-gray-50 p-2 rounded">
                            {JSON.stringify(action.metadata, null, 2)}
                          </pre>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {selectedExecution.screenshots.length > 0 && (
              <div>
                <span className="text-sm text-gray-600">Screenshots:</span>
                <div className="mt-1 grid grid-cols-2 gap-2">
                  {selectedExecution.screenshots.map((screenshot, index) => (
                    <div key={index} className="relative">
                      <img
                        src={screenshot}
                        alt={`Screenshot ${index + 1}`}
                        className="w-full h-32 object-cover rounded border"
                      />
                      <div className="absolute bottom-1 left-1 bg-black bg-opacity-50 text-white text-xs px-1 rounded">
                        {index + 1}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            <div className="text-xs text-gray-500">
              <span>Timestamp: {selectedExecution.timestamp.toISOString()}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
