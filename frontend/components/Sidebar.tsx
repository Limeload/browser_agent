'use client'

import { Mic, FolderOpen, BarChart3 } from 'lucide-react'

interface SidebarProps {
  activeTab: 'agent' | 'sessions' | 'monitoring'
  onTabChange: (tab: 'agent' | 'sessions' | 'monitoring') => void
}

export function Sidebar({ activeTab, onTabChange }: SidebarProps) {
  const tabs = [
    {
      id: 'agent' as const,
      label: 'Voice Agent',
      icon: Mic,
      description: 'Control browser with voice commands'
    },
    {
      id: 'sessions' as const,
      label: 'Sessions',
      icon: FolderOpen,
      description: 'Manage and export sessions'
    },
    {
      id: 'monitoring' as const,
      label: 'Monitoring',
      icon: BarChart3,
      description: 'System metrics and logs'
    }
  ]

  return (
    <aside className="w-64 bg-white border-r border-gray-200 min-h-screen">
      <nav className="p-4">
        <div className="space-y-2">
          {tabs.map((tab) => {
            const Icon = tab.icon
            const isActive = activeTab === tab.id
            
            return (
              <button
                key={tab.id}
                onClick={() => onTabChange(tab.id)}
                className={`w-full flex items-start space-x-3 p-3 rounded-lg text-left transition-colors ${
                  isActive
                    ? 'bg-primary-50 border border-primary-200 text-primary-900'
                    : 'hover:bg-gray-50 text-gray-700'
                }`}
              >
                <Icon className={`w-5 h-5 mt-0.5 ${isActive ? 'text-primary-600' : 'text-gray-500'}`} />
                <div>
                  <div className={`font-medium ${isActive ? 'text-primary-900' : 'text-gray-900'}`}>
                    {tab.label}
                  </div>
                  <div className={`text-xs ${isActive ? 'text-primary-700' : 'text-gray-500'}`}>
                    {tab.description}
                  </div>
                </div>
              </button>
            )
          })}
        </div>
      </nav>
    </aside>
  )
}
