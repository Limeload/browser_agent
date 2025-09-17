/**
 * API Routes for Browser Executor
 */

import { Router } from 'express'
import { ExecutionManager } from '../services/ExecutionManager'
import { MonitoringService } from '../services/MonitoringService'

export function routes(
  executionManager: ExecutionManager,
  monitoringService: MonitoringService
): Router {
  const router = Router()

  // Health check
  router.get('/health', async (req, res) => {
    try {
      const health = await monitoringService.healthCheck()
      res.json({
        status: 'healthy',
        service: 'browser-executor',
        timestamp: new Date().toISOString(),
        ...health
      })
    } catch (error) {
      res.status(500).json({
        status: 'unhealthy',
        error: error.message
      })
    }
  })

  // Execute browser actions
  router.post('/execute', async (req, res) => {
    try {
      const { sessionId, actions, context = {} } = req.body

      if (!sessionId) {
        return res.status(400).json({
          error: 'sessionId is required'
        })
      }

      if (!actions || !Array.isArray(actions)) {
        return res.status(400).json({
          error: 'actions array is required'
        })
      }

      const result = await executionManager.executeActions(
        sessionId,
        actions,
        context
      )

      res.json({
        success: true,
        result
      })

    } catch (error) {
      res.status(500).json({
        success: false,
        error: error.message
      })
    }
  })

  // Get execution status
  router.get('/execution/:sessionId/status', async (req, res) => {
    try {
      const { sessionId } = req.params
      const status = await executionManager.getExecutionStatus(sessionId)

      res.json({
        sessionId,
        ...status
      })

    } catch (error) {
      res.status(500).json({
        error: error.message
      })
    }
  })

  // Cancel execution
  router.post('/execution/:sessionId/cancel', async (req, res) => {
    try {
      const { sessionId } = req.params
      await executionManager.cancelExecution(sessionId)

      res.json({
        success: true,
        message: 'Execution cancelled'
      })

    } catch (error) {
      res.status(500).json({
        success: false,
        error: error.message
      })
    }
  })

  // Get active executions
  router.get('/executions/active', async (req, res) => {
    try {
      const activeExecutions = await executionManager.getActiveExecutions()

      res.json({
        activeExecutions,
        count: activeExecutions.length
      })

    } catch (error) {
      res.status(500).json({
        error: error.message
      })
    }
  })

  // Get metrics
  router.get('/metrics', async (req, res) => {
    try {
      const metrics = await monitoringService.healthCheck()

      res.json(metrics)

    } catch (error) {
      res.status(500).json({
        error: error.message
      })
    }
  })

  return router
}