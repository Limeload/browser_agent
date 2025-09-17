'use client'

import { useState, useEffect } from 'react'
import { VoiceAgent } from '@/components/VoiceAgent'
import { SessionManager } from '@/components/SessionManager'
import { MonitoringDashboard } from '@/components/MonitoringDashboard'
import { Header } from '@/components/Header'
import { Sidebar } from '@/components/Sidebar'
import { useVoiceAgentStore } from '@/store/voiceAgentStore'

export default function Home() {
  const [activeTab, setActiveTab] = useState<'agent' | 'sessions' | 'monitoring'>('agent')
  const { isConnected, sessionId } = useVoiceAgentStore()

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      
      <div className="flex">
        <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />
        
        <main className="flex-1 p-6">
          {activeTab === 'agent' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h1 className="text-3xl font-bold text-gray-900">Voice Agent</h1>
                <div className="flex items-center space-x-2">
                  <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-success-500' : 'bg-error-500'}`} />
                  <span className="text-sm text-gray-600">
                    {isConnected ? 'Connected' : 'Disconnected'}
                  </span>
                  {sessionId && (
                    <span className="text-xs text-gray-500">Session: {sessionId.slice(0, 8)}...</span>
                  )}
                </div>
              </div>
              
              <VoiceAgent />
            </div>
          )}
          
          {activeTab === 'sessions' && (
            <div className="space-y-6">
              <h1 className="text-3xl font-bold text-gray-900">Session Management</h1>
              <SessionManager />
            </div>
          )}
          
          {activeTab === 'monitoring' && (
            <div className="space-y-6">
              <h1 className="text-3xl font-bold text-gray-900">Monitoring Dashboard</h1>
              <MonitoringDashboard />
            </div>
          )}
        </main>
      </div>
    </div>
  )
}
