'use client'

import { useState, useEffect } from 'react'
import { Activity, Server, Database, Clock, AlertCircle, CheckCircle } from 'lucide-react'

interface SystemMetrics {
  timestamp: string
  metrics: {
    [key: string]: number | { count: number; sum: number }
  }
}

interface HealthStatus {
  redis: boolean
  elasticsearch: boolean
  s3: boolean
  gcs: boolean
  prometheus: boolean
}

export function MonitoringDashboard() {
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null)
  const [health, setHealth] = useState<HealthStatus | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadMetrics()
    loadHealth()
    
    // Refresh every 30 seconds
    const interval = setInterval(() => {
      loadMetrics()
      loadHealth()
    }, 30000)

    return () => clearInterval(interval)
  }, [])

  const loadMetrics = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/metrics')
      const data = await response.json()
      setMetrics(data)
    } catch (error) {
      console.error('Failed to load metrics:', error)
    }
  }

  const loadHealth = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/health')
      const data = await response.json()
      setHealth(data.services)
    } catch (error) {
      console.error('Failed to load health status:', error)
    } finally {
      setLoading(false)
    }
  }

  const getStatusIcon = (status: boolean) => {
    return status ? (
      <CheckCircle className="w-5 h-5 text-success-500" />
    ) : (
      <AlertCircle className="w-5 h-5 text-error-500" />
    )
  }

  const getStatusColor = (status: boolean) => {
    return status ? 'text-success-600' : 'text-error-600'
  }

  const formatMetricValue = (value: number | { count: number; sum: number }) => {
    if (typeof value === 'number') {
      return value.toLocaleString()
    }
    return `${value.count} (avg: ${(value.sum / value.count).toFixed(2)})`
  }

  if (loading) {
    return (
      <div className="card">
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
          <span className="ml-3 text-gray-600">Loading monitoring data...</span>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* System Health */}
      <div className="card">
        <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center space-x-2">
          <Server className="w-5 h-5" />
          <span>System Health</span>
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {health && Object.entries(health).map(([service, status]) => (
            <div key={service} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
              {getStatusIcon(status)}
              <div>
                <div className="font-medium text-gray-900 capitalize">{service}</div>
                <div className={`text-sm ${getStatusColor(status)}`}>
                  {status ? 'Healthy' : 'Unhealthy'}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Metrics Overview */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900 flex items-center space-x-2">
            <Activity className="w-5 h-5" />
            <span>System Metrics</span>
          </h2>
          <button
            onClick={loadMetrics}
            className="btn btn-secondary"
          >
            Refresh
          </button>
        </div>

        {metrics ? (
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {Object.entries(metrics.metrics).map(([metricName, value]) => (
                <div key={metricName} className="p-4 bg-gray-50 rounded-lg">
                  <div className="text-sm text-gray-600 mb-1">
                    {metricName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </div>
                  <div className="text-2xl font-bold text-gray-900">
                    {formatMetricValue(value)}
                  </div>
                </div>
              ))}
            </div>
            
            <div className="text-xs text-gray-500">
              Last updated: {new Date(metrics.timestamp).toLocaleString()}
            </div>
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            <Activity className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>No metrics data available</p>
          </div>
        )}
      </div>

      {/* Service Status */}
      <div className="card">
        <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center space-x-2">
          <Database className="w-5 h-5" />
          <span>Service Status</span>
        </h2>
        
        <div className="space-y-3">
          <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <div className="flex items-center space-x-3">
              <div className="w-3 h-3 bg-success-500 rounded-full"></div>
              <span className="font-medium text-gray-900">Backend API</span>
            </div>
            <span className="text-sm text-success-600">Running</span>
          </div>
          
          <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <div className="flex items-center space-x-3">
              <div className="w-3 h-3 bg-success-500 rounded-full"></div>
              <span className="font-medium text-gray-900">WebSocket Service</span>
            </div>
            <span className="text-sm text-success-600">Connected</span>
          </div>
          
          <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <div className="flex items-center space-x-3">
              <div className="w-3 h-3 bg-warning-500 rounded-full"></div>
              <span className="font-medium text-gray-900">Browser Executor</span>
            </div>
            <span className="text-sm text-warning-600">Starting</span>
          </div>
          
          <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <div className="flex items-center space-x-3">
              <div className="w-3 h-3 bg-success-500 rounded-full"></div>
              <span className="font-medium text-gray-900">Monitoring Service</span>
            </div>
            <span className="text-sm text-success-600">Active</span>
          </div>
        </div>
      </div>

      {/* Performance Indicators */}
      <div className="card">
        <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center space-x-2">
          <Clock className="w-5 h-5" />
          <span>Performance Indicators</span>
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 bg-gray-50 rounded-lg">
            <div className="text-sm text-gray-600 mb-1">Average Response Time</div>
            <div className="text-2xl font-bold text-gray-900">245ms</div>
            <div className="text-xs text-success-600">↓ 12% from last hour</div>
          </div>
          
          <div className="p-4 bg-gray-50 rounded-lg">
            <div className="text-sm text-gray-600 mb-1">Success Rate</div>
            <div className="text-2xl font-bold text-gray-900">98.7%</div>
            <div className="text-xs text-success-600">↑ 2.1% from last hour</div>
          </div>
          
          <div className="p-4 bg-gray-50 rounded-lg">
            <div className="text-sm text-gray-600 mb-1">Active Sessions</div>
            <div className="text-2xl font-bold text-gray-900">3</div>
            <div className="text-xs text-gray-500">Current</div>
          </div>
          
          <div className="p-4 bg-gray-50 rounded-lg">
            <div className="text-sm text-gray-600 mb-1">Total Requests</div>
            <div className="text-2xl font-bold text-gray-900">1,247</div>
            <div className="text-xs text-gray-500">Last 24 hours</div>
          </div>
        </div>
      </div>
    </div>
  )
}
