'use client'

import { useState, useEffect } from 'react'
import { Download, Trash2, Eye, Calendar, Clock, FolderOpen } from 'lucide-react'
import toast from 'react-hot-toast'

interface Session {
  session_id: string
  timestamp: string
  storage: string
}

export function SessionManager() {
  const [sessions, setSessions] = useState<Session[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedSession, setSelectedSession] = useState<string | null>(null)

  useEffect(() => {
    loadSessions()
  }, [])

  const loadSessions = async () => {
    try {
      setLoading(true)
      const response = await fetch('http://localhost:8000/api/sessions')
      const data = await response.json()
      setSessions(data.sessions || [])
    } catch (error) {
      console.error('Failed to load sessions:', error)
      toast.error('Failed to load sessions')
    } finally {
      setLoading(false)
    }
  }

  const handleExportSession = async (sessionId: string) => {
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
      console.error('Failed to export session:', error)
      toast.error('Failed to export session')
    }
  }

  const handleDeleteSession = async (sessionId: string) => {
    if (!confirm('Are you sure you want to delete this session?')) {
      return
    }

    try {
      // Note: This would need a DELETE endpoint in the backend
      toast.error('Delete functionality not implemented yet')
    } catch (error) {
      console.error('Failed to delete session:', error)
      toast.error('Failed to delete session')
    }
  }

  const formatDate = (timestamp: string) => {
    return new Date(timestamp).toLocaleString()
  }

  const getSessionIdShort = (sessionId: string) => {
    return sessionId.slice(0, 8) + '...'
  }

  if (loading) {
    return (
      <div className="card">
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
          <span className="ml-3 text-gray-600">Loading sessions...</span>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Session List */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">Available Sessions</h2>
          <button
            onClick={loadSessions}
            className="btn btn-secondary"
          >
            Refresh
          </button>
        </div>

        {sessions.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <FolderOpen className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>No sessions found. Start using the voice agent to create sessions.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {sessions.map((session) => (
              <div
                key={session.session_id}
                className={`p-4 rounded-lg border cursor-pointer transition-colors ${
                  selectedSession === session.session_id
                    ? 'border-primary-500 bg-primary-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
                onClick={() => setSelectedSession(session.session_id)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      <span className="font-mono text-sm text-gray-900">
                        {getSessionIdShort(session.session_id)}
                      </span>
                      <span className={`status-indicator ${
                        session.storage === 'local' ? 'status-info' : 'status-success'
                      }`}>
                        {session.storage}
                      </span>
                    </div>
                    
                    <div className="flex items-center space-x-4 text-sm text-gray-500">
                      <div className="flex items-center space-x-1">
                        <Calendar className="w-4 h-4" />
                        <span>{formatDate(session.timestamp)}</span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        handleExportSession(session.session_id)
                      }}
                      className="p-2 text-gray-600 hover:text-primary-600 hover:bg-primary-50 rounded-lg transition-colors"
                      title="Export session"
                    >
                      <Download className="w-4 h-4" />
                    </button>
                    
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        handleDeleteSession(session.session_id)
                      }}
                      className="p-2 text-gray-600 hover:text-error-600 hover:bg-error-50 rounded-lg transition-colors"
                      title="Delete session"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Session Details */}
      {selectedSession && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Session Details</h3>
          
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <span className="text-sm text-gray-600">Session ID:</span>
                <p className="font-mono text-sm text-gray-900">{selectedSession}</p>
              </div>
              <div>
                <span className="text-sm text-gray-600">Storage:</span>
                <p className="text-sm text-gray-900">
                  {sessions.find(s => s.session_id === selectedSession)?.storage}
                </p>
              </div>
            </div>
            
            <div>
              <span className="text-sm text-gray-600">Created:</span>
              <p className="text-sm text-gray-900">
                {formatDate(sessions.find(s => s.session_id === selectedSession)?.timestamp || '')}
              </p>
            </div>
            
            <div className="flex space-x-2 pt-4">
              <button
                onClick={() => handleExportSession(selectedSession)}
                className="btn btn-primary flex items-center space-x-2"
              >
                <Download className="w-4 h-4" />
                <span>Export Session</span>
              </button>
              
              <button
                onClick={() => handleDeleteSession(selectedSession)}
                className="btn btn-error flex items-center space-x-2"
              >
                <Trash2 className="w-4 h-4" />
                <span>Delete Session</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
