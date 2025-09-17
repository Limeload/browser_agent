/**
 * Browser Executor Service
 * Handles browser automation using Browserbase SDK and Playwright
 */

import express from 'express'
import { createServer } from 'http'
import { Server as SocketIOServer } from 'socket.io'
import cors from 'cors'
import helmet from 'helmet'
import compression from 'compression'
import dotenv from 'dotenv'
import winston from 'winston'

import { BrowserExecutor } from './services/BrowserExecutor'
import { ExecutionManager } from './services/ExecutionManager'
import { MonitoringService } from './services/MonitoringService'
import { routes } from './routes'
import { errorHandler } from './middleware/errorHandler'
import { requestLogger } from './middleware/requestLogger'

// Load environment variables
dotenv.config()

// Configure logger
const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  defaultMeta: { service: 'browser-executor' },
  transports: [
    new winston.transports.Console({
      format: winston.format.combine(
        winston.format.colorize(),
        winston.format.simple()
      )
    })
  ]
})

class BrowserExecutorService {
  private app: express.Application
  private server: any
  private io: SocketIOServer
  private browserExecutor: BrowserExecutor
  private executionManager: ExecutionManager
  private monitoringService: MonitoringService
  private port: number

  constructor() {
    this.port = parseInt(process.env.EXECUTOR_PORT || '3001', 10)
    this.app = express()
    this.server = createServer(this.app)
    this.io = new SocketIOServer(this.server, {
      cors: {
        origin: ["http://localhost:3000", "http://localhost:8000"],
        methods: ["GET", "POST"]
      }
    })

    // Initialize services
    this.monitoringService = new MonitoringService(logger)
    this.browserExecutor = new BrowserExecutor(this.monitoringService, logger)
    this.executionManager = new ExecutionManager(
      this.browserExecutor,
      this.monitoringService,
      logger
    )

    this.setupMiddleware()
    this.setupRoutes()
    this.setupSocketHandlers()
    this.setupErrorHandling()
  }

  private setupMiddleware(): void {
    // Security middleware
    this.app.use(helmet())
    this.app.use(cors({
      origin: ["http://localhost:3000", "http://localhost:8000"],
      credentials: true
    }))
    this.app.use(compression())

    // Body parsing
    this.app.use(express.json({ limit: '10mb' }))
    this.app.use(express.urlencoded({ extended: true, limit: '10mb' }))

    // Request logging
    this.app.use(requestLogger(logger))
  }

  private setupRoutes(): void {
    // Health check
    this.app.get('/health', (req, res) => {
      res.json({
        status: 'healthy',
        service: 'browser-executor',
        timestamp: new Date().toISOString(),
        version: '1.0.0'
      })
    })

    // API routes
    this.app.use('/api', routes(this.executionManager, this.monitoringService))

    // 404 handler
    this.app.use('*', (req, res) => {
      res.status(404).json({
        error: 'Not Found',
        message: `Route ${req.originalUrl} not found`
      })
    })
  }

  private setupSocketHandlers(): void {
    this.io.on('connection', (socket) => {
      logger.info('Client connected', { socketId: socket.id })

      socket.on('execute', async (data) => {
        try {
          logger.info('Execution request received', { 
            socketId: socket.id, 
            sessionId: data.sessionId 
          })

          const result = await this.executionManager.executeActions(
            data.sessionId,
            data.actions,
            data.context || {}
          )

          socket.emit('execution_result', {
            sessionId: data.sessionId,
            result
          })

        } catch (error) {
          logger.error('Execution failed', { 
            socketId: socket.id, 
            error: error.message 
          })

          socket.emit('execution_error', {
            sessionId: data.sessionId,
            error: error.message
          })
        }
      })

      socket.on('disconnect', () => {
        logger.info('Client disconnected', { socketId: socket.id })
      })
    })
  }

  private setupErrorHandling(): void {
    this.app.use(errorHandler(logger))
  }

  public async start(): Promise<void> {
    try {
      // Initialize services
      await this.monitoringService.initialize()
      await this.browserExecutor.initialize()

      // Start server
      this.server.listen(this.port, () => {
        logger.info(`Browser Executor Service started on port ${this.port}`)
      })

      // Graceful shutdown
      process.on('SIGTERM', () => this.shutdown())
      process.on('SIGINT', () => this.shutdown())

    } catch (error) {
      logger.error('Failed to start service', { error: error.message })
      process.exit(1)
    }
  }

  public async shutdown(): Promise<void> {
    logger.info('Shutting down Browser Executor Service...')

    try {
      await this.browserExecutor.shutdown()
      await this.monitoringService.shutdown()

      this.server.close(() => {
        logger.info('Server closed')
        process.exit(0)
      })

    } catch (error) {
      logger.error('Error during shutdown', { error: error.message })
      process.exit(1)
    }
  }
}

// Start the service
const service = new BrowserExecutorService()
service.start().catch((error) => {
  console.error('Failed to start service:', error)
  process.exit(1)
})
