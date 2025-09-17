'use client'

import { useEffect, useRef, useCallback } from 'react'

interface AudioCaptureProps {
  isRecording: boolean
  onAudioLevelChange: (level: number) => void
  onAudioData: (data: ArrayBuffer) => void
}

export function AudioCapture({ isRecording, onAudioLevelChange, onAudioData }: AudioCaptureProps) {
  const audioContextRef = useRef<AudioContext | null>(null)
  const mediaStreamRef = useRef<MediaStream | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const animationFrameRef = useRef<number | null>(null)
  const processorRef = useRef<ScriptProcessorNode | null>(null)

  const startAudioCapture = useCallback(async () => {
    try {
      // Get user media
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 44100,
          channelCount: 1
        }
      })

      mediaStreamRef.current = stream

      // Create audio context
      audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)({
        sampleRate: 44100
      })

      // Create analyser for audio level monitoring
      analyserRef.current = audioContextRef.current.createAnalyser()
      analyserRef.current.fftSize = 256
      analyserRef.current.smoothingTimeConstant = 0.8

      // Create audio processor for data capture
      processorRef.current = audioContextRef.current.createScriptProcessor(4096, 1, 1)
      
      // Connect audio nodes
      const source = audioContextRef.current.createMediaStreamSource(stream)
      source.connect(analyserRef.current)
      source.connect(processorRef.current)
      processorRef.current.connect(audioContextRef.current.destination)

      // Process audio data
      processorRef.current.onaudioprocess = (event) => {
        if (isRecording) {
          const inputBuffer = event.inputBuffer
          const inputData = inputBuffer.getChannelData(0)
          
          // Convert to ArrayBuffer for transmission
          const arrayBuffer = new ArrayBuffer(inputData.length * 2)
          const dataView = new DataView(arrayBuffer)
          
          for (let i = 0; i < inputData.length; i++) {
            dataView.setInt16(i * 2, inputData[i] * 32767, true)
          }
          
          onAudioData(arrayBuffer)
        }
      }

      // Start audio level monitoring
      const monitorAudioLevel = () => {
        if (analyserRef.current && isRecording) {
          const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount)
          analyserRef.current.getByteFrequencyData(dataArray)
          
          // Calculate RMS (Root Mean Square) for audio level
          let sum = 0
          for (let i = 0; i < dataArray.length; i++) {
            sum += dataArray[i] * dataArray[i]
          }
          const rms = Math.sqrt(sum / dataArray.length)
          const normalizedLevel = rms / 255
          
          onAudioLevelChange(normalizedLevel)
          
          animationFrameRef.current = requestAnimationFrame(monitorAudioLevel)
        }
      }

      monitorAudioLevel()

    } catch (error) {
      console.error('Error starting audio capture:', error)
      throw error
    }
  }, [isRecording, onAudioData, onAudioLevelChange])

  const stopAudioCapture = useCallback(() => {
    // Stop animation frame
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current)
      animationFrameRef.current = null
    }

    // Disconnect audio nodes
    if (processorRef.current) {
      processorRef.current.disconnect()
      processorRef.current = null
    }

    // Stop media stream
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach(track => track.stop())
      mediaStreamRef.current = null
    }

    // Close audio context
    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      audioContextRef.current.close()
      audioContextRef.current = null
    }

    // Reset audio level
    onAudioLevelChange(0)
  }, [onAudioLevelChange])

  useEffect(() => {
    if (isRecording) {
      startAudioCapture()
    } else {
      stopAudioCapture()
    }

    return () => {
      stopAudioCapture()
    }
  }, [isRecording, startAudioCapture, stopAudioCapture])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopAudioCapture()
    }
  }, [stopAudioCapture])

  return null // This component doesn't render anything
}
