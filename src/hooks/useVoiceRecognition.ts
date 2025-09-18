import { useState, useEffect, useCallback } from 'react';
import { VoiceRecognitionState, VoiceCommand } from '../types';

// Extend Window interface for SpeechRecognition
declare global {
  interface Window {
    SpeechRecognition: any;
    webkitSpeechRecognition: any;
  }
}

interface UseVoiceRecognitionReturn {
  state: VoiceRecognitionState;
  startListening: () => void;
  stopListening: () => void;
  toggleListening: () => void;
  parseIntent: (transcript: string) => VoiceCommand;
}

export const useVoiceRecognition = (): UseVoiceRecognitionReturn => {
  const [state, setState] = useState<VoiceRecognitionState>({
    isListening: false,
    transcript: '',
    confidence: 0,
    isSupported: false,
  });

    const [recognition, setRecognition] = useState<any | null>(null);

  useEffect(() => {
    // Check if speech recognition is supported
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
    if (!SpeechRecognition) {
      setState(prev => ({ ...prev, isSupported: false }));
      return;
    }

    const recognitionInstance = new SpeechRecognition();
    recognitionInstance.continuous = true;
    recognitionInstance.interimResults = true;
    recognitionInstance.lang = 'en-US';
    recognitionInstance.maxAlternatives = 1;

    recognitionInstance.onstart = () => {
      setState(prev => ({ ...prev, isListening: true }));
    };

        recognitionInstance.onresult = (event: any) => {
      let finalTranscript = '';
      let interimTranscript = '';

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        const confidence = event.results[i][0].confidence;

        if (event.results[i].isFinal) {
          finalTranscript += transcript;
          setState(prev => ({ ...prev, confidence: confidence }));
        } else {
          interimTranscript += transcript;
        }
      }

      const fullTranscript = finalTranscript || interimTranscript;
      if (fullTranscript) {
        setState(prev => ({ ...prev, transcript: fullTranscript }));
      }
    };

        recognitionInstance.onerror = (event: any) => {
      console.error('Speech recognition error:', event.error);
      setState(prev => ({ ...prev, isListening: false }));
    };

    recognitionInstance.onend = () => {
      setState(prev => ({ ...prev, isListening: false }));
    };

    setRecognition(recognitionInstance);
    setState(prev => ({ ...prev, isSupported: true }));
  }, []);

  const startListening = useCallback(() => {
    if (recognition && !state.isListening) {
      try {
        recognition.start();
      } catch (error) {
        console.error('Failed to start recognition:', error);
      }
    }
  }, [recognition, state.isListening]);

  const stopListening = useCallback(() => {
    if (recognition && state.isListening) {
      recognition.stop();
    }
  }, [recognition, state.isListening]);

  const toggleListening = useCallback(() => {
    if (state.isListening) {
      stopListening();
    } else {
      startListening();
    }
  }, [state.isListening, startListening, stopListening]);

  const parseIntent = useCallback((transcript: string): VoiceCommand => {
    const text = transcript.toLowerCase().trim();
    
    // Navigation commands
    if (text.includes('go to') || text.includes('navigate to') || text.includes('visit')) {
      const url = extractUrl(text);
      return {
        intent: 'navigate',
        type: 'navigation',
        params: { url: url || 'unknown' },
        command: 'navigate',
        target: url || 'unknown'
      };
    }

    // Click commands
    if (text.includes('click') || text.includes('press') || text.includes('tap')) {
      const selector = extractSelector(text);
      return {
        intent: 'click',
        type: 'interaction',
        params: { selector: selector },
        command: 'click',
        target: selector
      };
    }

    // Type commands
    if (text.includes('type') || text.includes('enter') || text.includes('input')) {
      const { selector, text: inputText } = extractTypeCommand(text);
      return {
        intent: 'type',
        type: 'interaction',
        params: { selector: selector, text: inputText },
        command: 'type',
        target: selector,
        value: inputText
      };
    }

    // Screenshot commands
    if (text.includes('screenshot') || text.includes('capture') || text.includes('take picture')) {
      return {
        intent: 'screenshot',
        type: 'capture',
        params: {},
        command: 'screenshot'
      };
    }

    // Wait commands
    if (text.includes('wait') || text.includes('pause')) {
      const duration = extractDuration(text);
      return {
        intent: 'wait',
        type: 'timing',
        params: { duration: duration },
        command: 'wait',
        duration: duration
      };
    }

    // Scroll commands
    if (text.includes('scroll')) {
      const direction = extractScrollDirection(text);
      return {
        intent: 'scroll',
        type: 'interaction',
        params: { direction: direction },
        command: 'scroll',
        direction: direction
      };
    }

    return {
      intent: 'unknown',
      type: 'unknown',
      params: { transcript: transcript },
      command: 'unknown'
    };
  }, []);

  return {
    state,
    startListening,
    stopListening,
    toggleListening,
    parseIntent,
  };
};

// Helper functions
function extractUrl(text: string): string | null {
  const urlMatch = text.match(/(?:https?:\/\/)?(?:www\.)?([a-zA-Z0-9-]+\.[a-zA-Z]{2,})/);
  return urlMatch ? (urlMatch[0].startsWith('http') ? urlMatch[0] : `https://${urlMatch[0]}`) : null;
}

function extractSelector(text: string): string {
  if (text.includes('button')) return 'button';
  if (text.includes('link')) return 'a';
  if (text.includes('input')) return 'input';
  if (text.includes('form')) return 'form';
  
  const textMatch = text.match(/(?:click|press|tap)\s+(.+?)(?:\s|$)/);
  return textMatch ? textMatch[1] : 'button';
}

function extractTypeCommand(text: string): { selector: string; text: string } {
  const typeMatch = text.match(/(?:type|enter|input)\s+(.+?)(?:\s+into|\s+in|\s+on)?\s*(.+)?/);
  if (typeMatch) {
    return {
      text: typeMatch[1],
      selector: typeMatch[2] || 'input'
    };
  }
  return { text: '', selector: 'input' };
}

function extractDuration(text: string): number {
  const durationMatch = text.match(/(\d+)\s*(?:second|sec|s|minute|min|m)/);
  return durationMatch ? parseInt(durationMatch[1]) * (text.includes('min') ? 60 : 1) : 1;
}

function extractScrollDirection(text: string): string {
  if (text.includes('up')) return 'up';
  if (text.includes('down')) return 'down';
  if (text.includes('left')) return 'left';
  if (text.includes('right')) return 'right';
  return 'down';
}
