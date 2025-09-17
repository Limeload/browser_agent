'use client'

import { useState, useEffect, useRef } from 'react'
import { FileText, Clock, AlertCircle, CheckCircle, Info, AlertTriangle } from 'lucide-react'
import { LogEntry } from '@/store/voiceAgentStore'

interface LogsPanelProps {
  logs: LogEntry[]
}

export function LogsPanel({ logs }: LogsPanelProps) {
  const [selectedLog, setSelectedLog] = useState<LogEntry | null>(null)
  const [filterLevel, setFilterLevel] = useState<string>('all')
  const logsEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [logs])

  const getLevelIcon = (level: string) => {
    switch (level.toLowerCase()) {
      case 'error':
        return <AlertCircle className="w-4 h-4 text-error-500" />
      case 'warning':
        return <AlertTriangle className="w-4 h-4 text-warning-500" />
      case 'info':
        return <Info className="w-4 h-4 text-primary-500" />
      case 'success':
        return <CheckCircle className="w-4 h-4 text-success-500" />
      default:
        return <Info className="w-4 h-4 text-gray-500" />
    }
  }

  const getLevelColor = (level: string) => {
    switch (level.toLowerCase()) {
      case 'error':
        return 'border-error-200 bg-error-50'
      case 'warning':
        return 'border-warning-200 bg-warning-50'
      case 'info':
        return 'border-primary-200 bg-primary-50'
      case 'success':
        return 'border-success-200 bg-success-50'
      default:
        return 'border-gray-200 bg-gray-50'
    }
  }

  const getLevelBadge = (level: string) => {
    const colors: Record<string, string> = {
      error: 'bg-error-100 text-error-800',
      warning: 'bg-warning-100 text-warning-800',
      info: 'bg-primary-100 text-primary-800',
      success: 'bg-success-100 text-success-800'
    }
    return colors[level.toLowerCase()] || 'bg-gray-100 text-gray-800'
  }

  const filteredLogs = logs.filter(log => 
    filterLevel === 'all' || log.level.toLowerCase() === filterLevel.toLowerCase()
  )

  const levelCounts = logs.reduce((acc, log) => {
    const level = log.level.toLowerCase()
    acc[level] = (acc[level] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-gray-900 flex items-center space-x-2">
          <FileText className="w-5 h-5" />
          <span>System Logs</span>
        </h2>
        <span className="status-indicator status-info">
          {logs.length} log{logs.length !== 1 ? 's' : ''}
        </span>
      </div>

      {/* Filter Controls */}
      <div className="mb-4 flex items-center space-x-2">
        <span className="text-sm text-gray-600">Filter:</span>
        <div className="flex space-x-1">
          <button
            onClick={() => setFilterLevel('all')}
            className={`px-2 py-1 text-xs rounded ${
              filterLevel === 'all' 
                ? 'bg-primary-100 text-primary-800' 
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            All ({logs.length})
          </button>
          {Object.entries(levelCounts).map(([level, count]) => (
            <button
              key={level}
              onClick={() => setFilterLevel(level)}
              className={`px-2 py-1 text-xs rounded ${
                filterLevel === level 
                  ? 'bg-primary-100 text-primary-800' 
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {level} ({count})
            </button>
          ))}
        </div>
      </div>

      {filteredLogs.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <FileText className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p>No logs yet. System activity will appear here.</p>
        </div>
      ) : (
        <div className="space-y-2 max-h-96 overflow-y-auto scrollbar-hide">
          {filteredLogs.map((log) => (
            <div
              key={log.id}
              className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                selectedLog?.id === log.id
                  ? 'border-primary-500 bg-primary-50'
                  : getLevelColor(log.level)
              }`}
              onClick={() => setSelectedLog(log)}
            >
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0 mt-0.5">
                  {getLevelIcon(log.level)}
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2 mb-1">
                    <span className={`status-indicator ${getLevelBadge(log.level)} text-xs`}>
                      {log.level.toUpperCase()}
                    </span>
                    <span className="text-xs text-gray-500">{log.service}</span>
                  </div>
                  
                  <p className="text-sm text-gray-900 mb-1">{log.message}</p>
                  
                  <div className="flex items-center space-x-2 text-xs text-gray-500">
                    <div className="flex items-center space-x-1">
                      <Clock className="w-3 h-3" />
                      <span>{log.timestamp.toLocaleTimeString()}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
          <div ref={logsEndRef} />
        </div>
      )}

      {/* Selected Log Details */}
      {selectedLog && (
        <div className="mt-6 p-4 bg-gray-50 rounded-lg">
          <h3 className="font-medium text-gray-900 mb-3">Log Details</h3>
          
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">ID:</span>
              <span className="font-mono text-gray-900">{selectedLog.id}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Level:</span>
              <span className={`status-indicator ${getLevelBadge(selectedLog.level)}`}>
                {selectedLog.level.toUpperCase()}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Service:</span>
              <span className="text-gray-900">{selectedLog.service}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Timestamp:</span>
              <span className="text-gray-900">{selectedLog.timestamp.toISOString()}</span>
            </div>
            <div>
              <span className="text-gray-600">Message:</span>
              <p className="mt-1 text-gray-900">{selectedLog.message}</p>
            </div>
            {selectedLog.metadata && Object.keys(selectedLog.metadata).length > 0 && (
              <div>
                <span className="text-gray-600">Metadata:</span>
                <pre className="mt-1 text-xs bg-white p-2 rounded border overflow-x-auto">
                  {JSON.stringify(selectedLog.metadata, null, 2)}
                </pre>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
