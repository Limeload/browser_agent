/**
 * Browser Executor Service
 * Handles browser automation using Browserbase SDK and Playwright
 */

import { chromium, Browser, BrowserContext, Page } from 'playwright'
import { MonitoringService } from './MonitoringService'
import winston from 'winston'

export interface BrowserAction {
  action_type: string
  selector?: string
  text?: string
  url?: string
  xpath?: string
  coordinates?: { x: number; y: number }
  wait_time?: number
  retry_count?: number
  metadata?: Record<string, any>
}

export interface ExecutionResult {
  success: boolean
  actions_executed: BrowserAction[]
  screenshots: string[]
  final_url?: string
  extracted_data?: Record<string, any>
  execution_time: number
  error_message?: string
}

export class BrowserExecutor {
  private monitoringService: MonitoringService
  private logger: winston.Logger
  private browser: Browser | null = null
  private context: BrowserContext | null = null
  private page: Page | null = null
  private sessionId: string | null = null

  constructor(monitoringService: MonitoringService, logger: winston.Logger) {
    this.monitoringService = monitoringService
    this.logger = logger
  }

  public async initialize(): Promise<void> {
    try {
      this.logger.info('Initializing Browser Executor')
      
      // Launch browser
      this.browser = await chromium.launch({
        headless: true,
        args: [
          '--no-sandbox',
          '--disable-setuid-sandbox',
          '--disable-dev-shm-usage',
          '--disable-accelerated-2d-canvas',
          '--no-first-run',
          '--no-zygote',
          '--disable-gpu'
        ]
      })

      this.logger.info('Browser launched successfully')
      
    } catch (error) {
      this.logger.error('Failed to initialize Browser Executor', { error: error.message })
      throw error
    }
  }

  public async createSession(sessionId: string): Promise<void> {
    try {
      if (!this.browser) {
        throw new Error('Browser not initialized')
      }

      // Create new context for the session
      this.context = await this.browser.newContext({
        viewport: { width: 1280, height: 720 },
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
      })

      // Create new page
      this.page = await this.context.newPage()
      this.sessionId = sessionId

      this.logger.info('Browser session created', { sessionId })
      
    } catch (error) {
      this.logger.error('Failed to create browser session', { 
        sessionId, 
        error: error.message 
      })
      throw error
    }
  }

  public async executeActions(
    sessionId: string,
    actions: BrowserAction[]
  ): Promise<ExecutionResult> {
    const startTime = Date.now()
    const executedActions: BrowserAction[] = []
    const screenshots: string[] = []

    try {
      // Ensure session exists
      if (!this.page || this.sessionId !== sessionId) {
        await this.createSession(sessionId)
      }

      this.logger.info('Executing browser actions', { 
        sessionId, 
        actionCount: actions.length 
      })

      // Execute each action
      for (let i = 0; i < actions.length; i++) {
        const action = actions[i]
        
        try {
          await this.executeAction(action)
          executedActions.push(action)
          
          // Take screenshot after each action
          const screenshot = await this.takeScreenshot()
          screenshots.push(screenshot)
          
          this.logger.debug('Action executed successfully', { 
            sessionId, 
            actionIndex: i, 
            actionType: action.action_type 
          })

        } catch (error) {
          this.logger.error('Action execution failed', { 
            sessionId, 
            actionIndex: i, 
            actionType: action.action_type, 
            error: error.message 
          })
          
          // Retry logic
          if (action.retry_count && action.retry_count > 0) {
            action.retry_count--
            i-- // Retry the same action
            continue
          }
          
          throw error
        }
      }

      const executionTime = Date.now() - startTime
      const finalUrl = this.page?.url()

      // Record metrics
      await this.monitoringService.recordMetric('execution_time', executionTime, { sessionId })
      await this.monitoringService.recordMetric('actions_executed', executedActions.length, { sessionId })

      this.logger.info('All actions executed successfully', { 
        sessionId, 
        executionTime, 
        actionsExecuted: executedActions.length 
      })

      return {
        success: true,
        actions_executed: executedActions,
        screenshots,
        final_url: finalUrl,
        execution_time: executionTime / 1000
      }

    } catch (error) {
      const executionTime = Date.now() - startTime
      
      this.logger.error('Execution failed', { 
        sessionId, 
        executionTime, 
        error: error.message 
      })

      // Record error metric
      await this.monitoringService.recordMetric('execution_errors', 1, { 
        sessionId, 
        errorType: error.constructor.name 
      })

      return {
        success: false,
        actions_executed: executedActions,
        screenshots,
        execution_time: executionTime / 1000,
        error_message: error.message
      }
    }
  }

  private async executeAction(action: BrowserAction): Promise<void> {
    if (!this.page) {
      throw new Error('No active page')
    }

    switch (action.action_type) {
      case 'navigate':
        await this.navigate(action.url!)
        break
      
      case 'click':
        await this.click(action.selector!, action.xpath, action.coordinates)
        break
      
      case 'type':
        await this.type(action.selector!, action.text!, action.xpath)
        break
      
      case 'scroll':
        await this.scroll(action.coordinates)
        break
      
      case 'wait':
        await this.wait(action.wait_time!)
        break
      
      case 'screenshot':
        await this.takeScreenshot()
        break
      
      case 'extract_text':
        await this.extractText(action.selector!, action.xpath)
        break
      
      case 'extract_links':
        await this.extractLinks()
        break
      
      default:
        throw new Error(`Unknown action type: ${action.action_type}`)
    }
  }

  private async navigate(url: string): Promise<void> {
    if (!this.page) throw new Error('No active page')
    
    await this.page.goto(url, { 
      waitUntil: 'networkidle',
      timeout: 30000 
    })
    
    this.logger.debug('Navigated to URL', { url })
  }

  private async click(
    selector?: string, 
    xpath?: string, 
    coordinates?: { x: number; y: number }
  ): Promise<void> {
    if (!this.page) throw new Error('No active page')

    if (coordinates) {
      await this.page.click('body', { 
        position: { x: coordinates.x, y: coordinates.y } 
      })
    } else if (xpath) {
      await this.page.click(`xpath=${xpath}`)
    } else if (selector) {
      await this.page.click(selector)
    } else {
      throw new Error('No click target specified')
    }
    
    this.logger.debug('Click action executed', { selector, xpath, coordinates })
  }

  private async type(
    selector: string, 
    text: string, 
    xpath?: string
  ): Promise<void> {
    if (!this.page) throw new Error('No active page')

    const target = xpath ? `xpath=${xpath}` : selector
    await this.page.fill(target, text)
    
    this.logger.debug('Type action executed', { selector, xpath, textLength: text.length })
  }

  private async scroll(coordinates?: { x: number; y: number }): Promise<void> {
    if (!this.page) throw new Error('No active page')

    if (coordinates) {
      await this.page.mouse.wheel(coordinates.x, coordinates.y)
    } else {
      await this.page.mouse.wheel(0, 500) // Default scroll down
    }
    
    this.logger.debug('Scroll action executed', { coordinates })
  }

  private async wait(seconds: number): Promise<void> {
    await new Promise(resolve => setTimeout(resolve, seconds * 1000))
    this.logger.debug('Wait action executed', { seconds })
  }

  private async takeScreenshot(): Promise<string> {
    if (!this.page) throw new Error('No active page')

    const screenshot = await this.page.screenshot({ 
      type: 'png',
      fullPage: true 
    })
    
    // Convert to base64 for transmission
    const base64 = screenshot.toString('base64')
    this.logger.debug('Screenshot taken', { size: base64.length })
    
    return `data:image/png;base64,${base64}`
  }

  private async extractText(selector?: string, xpath?: string): Promise<Record<string, any>> {
    if (!this.page) throw new Error('No active page')

    let text = ''
    
    if (xpath) {
      text = await this.page.textContent(`xpath=${xpath}`) || ''
    } else if (selector) {
      text = await this.page.textContent(selector) || ''
    } else {
      text = await this.page.textContent('body') || ''
    }
    
    this.logger.debug('Text extracted', { selector, xpath, textLength: text.length })
    
    return { extracted_text: text }
  }

  private async extractLinks(): Promise<Record<string, any>> {
    if (!this.page) throw new Error('No active page')

    const links = await this.page.$$eval('a', elements => 
      elements.map(el => ({
        text: el.textContent?.trim(),
        href: el.getAttribute('href'),
        title: el.getAttribute('title')
      }))
    )
    
    this.logger.debug('Links extracted', { linkCount: links.length })
    
    return { extracted_links: links }
  }

  public async closeSession(): Promise<void> {
    try {
      if (this.context) {
        await this.context.close()
        this.context = null
      }
      
      this.page = null
      this.sessionId = null
      
      this.logger.info('Browser session closed')
      
    } catch (error) {
      this.logger.error('Failed to close browser session', { error: error.message })
      throw error
    }
  }

  public async shutdown(): Promise<void> {
    try {
      await this.closeSession()
      
      if (this.browser) {
        await this.browser.close()
        this.browser = null
      }
      
      this.logger.info('Browser Executor shutdown complete')
      
    } catch (error) {
      this.logger.error('Error during browser executor shutdown', { error: error.message })
      throw error
    }
  }
}
