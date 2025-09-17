/**
 * Monitoring Service for Browser Executor
 * Handles metrics collection and logging
 */

import winston from 'winston'

export interface MetricTags {
  [key: string]: string
}

export class MonitoringService {
  private logger: winston.Logger
  private metrics: Map<string, number> = new Map()

  constructor(logger: winston.Logger) {
    this.logger = logger
  }

  public async initialize(): Promise<void> {
    this.logger.info('Initializing Monitoring Service')
    // Initialize any required resources
  }

  public async recordMetric(
    metricName: string, 
    value: number, 
    tags: MetricTags = {}
  ): Promise<void> {
    try {
      // Store metric
      const key = `${metricName}_${JSON.stringify(tags)}`
      this.metrics.set(key, value)

      // Log metric
      this.logger.debug('Metric recorded', { 
        metric: metricName, 
        value, 
        tags 
      })

    } catch (error) {
      this.logger.error('Failed to record metric', { 
        error: error.message, 
        metric: metricName 
      })
    }
  }

  public async logEvent(
    level: string,
    message: string,
    metadata: Record<string, any> = {}
  ): Promise<void> {
    try {
      const logData = {
        timestamp: new Date().toISOString(),
        level,
        message,
        ...metadata
      }

      this.logger.log(level, message, logData)

    } catch (error) {
      this.logger.error('Failed to log event', { 
        error: error.message 
      })
    }
  }

  public getMetrics(): Record<string, number> {
    const result: Record<string, number> = {}
    for (const [key, value] of this.metrics.entries()) {
      result[key] = value
    }
    return result
  }

  public async healthCheck(): Promise<{
    status: string
    metrics: Record<string, number>
  }> {
    return {
      status: 'healthy',
      metrics: this.getMetrics()
    }
  }

  public async shutdown(): Promise<void> {
    this.logger.info('Shutting down Monitoring Service')
    this.metrics.clear()
  }
}