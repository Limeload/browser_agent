/**
 * Error Handler Middleware
 */

import { Request, Response, NextFunction } from 'express'
import winston from 'winston'

export function errorHandler(logger: winston.Logger) {
  return (error: Error, req: Request, res: Response, next: NextFunction) => {
    // Log the error
    logger.error('Unhandled error', {
      error: error.message,
      stack: error.stack,
      url: req.url,
      method: req.method,
      body: req.body,
      query: req.query,
      params: req.params
    })

    // Don't expose internal errors in production
    const isDevelopment = process.env.NODE_ENV === 'development'
    
    const errorResponse = {
      success: false,
      error: isDevelopment ? error.message : 'Internal server error',
      ...(isDevelopment && { stack: error.stack })
    }

    // Set appropriate status code
    let statusCode = 500
    if (error.name === 'ValidationError') {
      statusCode = 400
    } else if (error.name === 'UnauthorizedError') {
      statusCode = 401
    } else if (error.name === 'ForbiddenError') {
      statusCode = 403
    } else if (error.name === 'NotFoundError') {
      statusCode = 404
    }

    res.status(statusCode).json(errorResponse)
  }
}