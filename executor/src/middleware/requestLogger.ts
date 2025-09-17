/**
 * Request Logger Middleware
 */

import { Request, Response, NextFunction } from 'express'
import winston from 'winston'

export function requestLogger(logger: winston.Logger) {
  return (req: Request, res: Response, next: NextFunction) => {
    const startTime = Date.now()

    // Log request
    logger.info('Request received', {
      method: req.method,
      url: req.url,
      userAgent: req.get('User-Agent'),
      ip: req.ip,
      timestamp: new Date().toISOString()
    })

    // Override res.end to log response
    const originalEnd = res.end
    res.end = function(chunk?: any, encoding?: any) {
      const duration = Date.now() - startTime
      
      logger.info('Request completed', {
        method: req.method,
        url: req.url,
        statusCode: res.statusCode,
        duration: `${duration}ms`,
        contentLength: res.get('Content-Length') || 0
      })

      // Call original end method
      originalEnd.call(this, chunk, encoding)
    }

    next()
  }
}