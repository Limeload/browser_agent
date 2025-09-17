interface WebSocketCallbacks {
  onConnect: () => void
  onDisconnect: () => void
  onTranscript: (data: any) => void
  onIntent: (data: any) => void
  onExecution: (data: any) => void
  onError: (error: Error) => void
}

export class WebSocketService {
  private ws: WebSocket | null = null
  private url: string
  private callbacks: WebSocketCallbacks
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000

  constructor(url: string, callbacks: WebSocketCallbacks) {
    this.url = url
    this.callbacks = callbacks
    this.connect()
  }

  private connect() {
    try {
      this.ws = new WebSocket(this.url)

      this.ws.onopen = () => {
        console.log('WebSocket connected')
        this.reconnectAttempts = 0
        this.callbacks.onConnect()
      }

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          this.handleMessage(data)
        } catch (error) {
          console.error('Error parsing WebSocket message:', error)
          this.callbacks.onError(new Error('Failed to parse message'))
        }
      }

      this.ws.onclose = () => {
        console.log('WebSocket disconnected')
        this.callbacks.onDisconnect()
        this.attemptReconnect()
      }

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        this.callbacks.onError(new Error('WebSocket connection error'))
      }

    } catch (error) {
      console.error('Error creating WebSocket:', error)
      this.callbacks.onError(new Error('Failed to create WebSocket connection'))
    }
  }

  private handleMessage(data: any) {
    switch (data.type) {
      case 'transcript':
        this.callbacks.onTranscript(data.data)
        break
      case 'intent':
        this.callbacks.onIntent(data.data)
        break
      case 'execution_plan':
        // Handle execution plan if needed
        break
      case 'execution_result':
        this.callbacks.onExecution(data.data)
        break
      case 'error':
        this.callbacks.onError(new Error(data.data.error))
        break
      default:
        console.log('Unknown message type:', data.type)
    }
  }

  private attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1)
      
      console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts})`)
      
      setTimeout(() => {
        this.connect()
      }, delay)
    } else {
      console.error('Max reconnection attempts reached')
      this.callbacks.onError(new Error('Max reconnection attempts reached'))
    }
  }

  public sendAudio(audioData: ArrayBuffer) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(audioData)
    } else {
      console.warn('WebSocket not connected, cannot send audio data')
    }
  }

  public sendMessage(message: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message))
    } else {
      console.warn('WebSocket not connected, cannot send message')
    }
  }

  public disconnect() {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  public getReadyState(): number {
    return this.ws?.readyState ?? WebSocket.CLOSED
  }

  public isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN
  }
}
