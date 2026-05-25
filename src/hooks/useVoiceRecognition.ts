import { useState, useEffect, useCallback } from 'react';
import { VoiceRecognitionState } from '../types';

declare global {
  interface Window {
    SpeechRecognition: new () => SpeechRecognition;
    webkitSpeechRecognition: new () => SpeechRecognition;
  }
}

interface UseVoiceRecognitionReturn {
  state: VoiceRecognitionState;
  startListening: () => void;
  stopListening: () => void;
  toggleListening: () => void;
}

export const useVoiceRecognition = (): UseVoiceRecognitionReturn => {
  const [state, setState] = useState<VoiceRecognitionState>({
    isListening: false,
    transcript: '',
    confidence: 0,
    isSupported: false,
  });

  const [recognition, setRecognition] = useState<SpeechRecognition | null>(null);

  useEffect(() => {
    const SpeechRecognitionAPI =
      window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognitionAPI) {
      return;
    }

    const instance = new SpeechRecognitionAPI();
    instance.continuous = true;
    instance.interimResults = true;
    instance.lang = 'en-US';
    instance.maxAlternatives = 1;

    instance.onstart = () => setState(prev => ({ ...prev, isListening: true }));

    instance.onresult = (event: SpeechRecognitionEvent) => {
      let finalTranscript = '';
      let interimTranscript = '';

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const text = event.results[i][0].transcript;
        const conf = event.results[i][0].confidence;
        if (event.results[i].isFinal) {
          finalTranscript += text;
          setState(prev => ({ ...prev, confidence: conf }));
        } else {
          interimTranscript += text;
        }
      }

      const full = finalTranscript || interimTranscript;
      if (full) setState(prev => ({ ...prev, transcript: full }));
    };

    instance.onerror = () =>
      setState(prev => ({ ...prev, isListening: false }));

    instance.onend = () =>
      setState(prev => ({ ...prev, isListening: false }));

    setRecognition(instance);
    setState(prev => ({ ...prev, isSupported: true }));
  }, []);

  const startListening = useCallback(() => {
    if (recognition && !state.isListening) {
      try { recognition.start(); } catch { /* already started */ }
    }
  }, [recognition, state.isListening]);

  const stopListening = useCallback(() => {
    if (recognition && state.isListening) recognition.stop();
  }, [recognition, state.isListening]);

  const toggleListening = useCallback(() => {
    if (state.isListening) stopListening();
    else startListening();
  }, [state.isListening, startListening, stopListening]);

  return { state, startListening, stopListening, toggleListening };
};
