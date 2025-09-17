/**
 * Execution Manager Service
 * Manages execution workflows and coordinates between services
 */

import { BrowserExecutor, BrowserAction, ExecutionResult } from './BrowserExecutor'
import { MonitoringService } from './MonitoringService'
import winston from 'winston'

export interface ExecutionContext {
  sessionId: string
  userId?: string
  preferences?: Record<string, any>
  metadata?: Record<string, any>
}

export interface ExecutionRequest {
  sessionId: string
  actions: BrowserAction[]
  context: ExecutionContext
}

export class ExecutionManager {
  private browserExecutor: BrowserExecutor
  private monitoringService: MonitoringService
  private logger: winston.Logger
  private activeExecutions: Map<string, Promise<ExecutionResult>> = new Map()

  constructor(
    browserExecutor: BrowserExecutor,
    monitoringService: MonitoringService,
    logger: winston.Logger
  ) {
    this.browserExecutor = browserExecutor
    this.monitoringService = monitoringService
    this.logger = logger
  }

  public async executeActions(
    sessionId: string,
    actions: BrowserAction[],
    context: Record<string, any> = {}
  ): Promise<ExecutionResult> {
    const startTime = Date.now()

    try {
      this.logger.info('Starting execution', { 
        sessionId, 
        actionCount: actions.length,
        context 
      })

      // Check if there's already an active execution for this session
      if (this.activeExecutions.has(sessionId)) {
        this.logger.warn('Execution already in progress', { sessionId })
        throw new Error('Execution already in progress for this session')
      }

      // Validate actions
      this.validateActions(actions)

      // Create execution promise
      const executionPromise = this.browserExecutor.executeActions(sessionId, actions)
      this.activeExecutions.set(sessionId, executionPromise)

      // Wait for execution to complete
      const result = await executionPromise

      // Record execution metrics
      const executionTime = Date.now() - startTime
      await this.monitoringService.recordMetric('total_execution_time', executionTime, { sessionId })
      await this.monitoringService.recordMetric('execution_success', result.success ? 1 : 0, { sessionId })

      this.logger.info('Execution completed', { 
        sessionId, 
        success: result.success,
        executionTime,
        actionsExecuted: result.actions_executed.length
      })

      return result

    } catch (error) {
      this.logger.error('Execution failed', { 
        sessionId, 
        error: error.message 
      })

      // Record error metrics
      await this.monitoringService.recordMetric('execution_errors', 1, { 
        sessionId, 
        errorType: error.constructor.name 
      })

      throw error

    } finally {
      // Clean up active execution
      this.activeExecutions.delete(sessionId)
    }
  }

  private validateActions(actions: BrowserAction[]): void {
    if (!actions || actions.length === 0) {
      throw new Error('No actions provided')
    }

    for (const action of actions) {
      this.validateAction(action)
    }
  }

  private validateAction(action: BrowserAction): void {
    if (!action.action_type) {
      throw new Error('Action type is required')
    }

    const validActionTypes = [
      'navigate', 'click', 'type', 'scroll', 'wait', 
      'screenshot', 'extract_text', 'extract_links'
    ]

    if (!validActionTypes.includes(action.action_type)) {
      throw new Error(`Invalid action type: ${action.action_type}`)
    }

    // Validate action-specific requirements
    switch (action.action_type) {
      case 'navigate':
        if (!action.url) {
          throw new Error('URL is required for navigate action')
        }
        break

      case 'click':
        if (!action.selector && !action.xpath && !action.coordinates) {
          throw new Error('Selector, xpath, or coordinates required for click action')
        }
        break

      case 'type':
        if (!action.selector && !action.xpath) {
          throw new Error('Selector or xpath required for type action')
        }
        if (!action.text) {
          throw new Error('Text is required for type action')
        }
        break

      case 'wait':
        if (!action.wait_time || action.wait_time <= 0) {
          throw new Error('Valid wait_time is required for wait action')
        }
        break
    }
  }

  public async getExecutionStatus(sessionId: string): Promise<{
    isActive: boolean
    progress?: number
  }> {
    const isActive = this.activeExecutions.has(sessionId)
    
    return {
      isActive,
      progress: isActive ? 0.5 : undefined // Simplified progress tracking
    }
  }

  public async cancelExecution(sessionId: string): Promise<void> {
    if (this.activeExecutions.has(sessionId)) {
      this.logger.info('Cancelling execution', { sessionId })
      
      // Close the browser session to cancel execution
      await this.browserExecutor.closeSession()
      
      // Remove from active executions
      this.activeExecutions.delete(sessionId)
      
      this.logger.info('Execution cancelled', { sessionId })
    } else {
      this.logger.warn('No active execution found to cancel', { sessionId })
    }
  }

  public async getActiveExecutions(): Promise<string[]> {
    return Array.from(this.activeExecutions.keys())
  }

  public async cleanup(): Promise<void> {
    this.logger.info('Cleaning up execution manager')
    
    // Cancel all active executions
    const activeSessions = Array.from(this.activeExecutions.keys())
    for (const sessionId of activeSessions) {
      await this.cancelExecution(sessionId)
    }
    
    this.logger.info('Execution manager cleanup complete')
  }
}
