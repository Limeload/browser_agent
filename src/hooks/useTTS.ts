import { useState, useCallback } from 'react';

interface UseTTSReturn {
  showFeedback: (message: string) => void;
  feedback: {
    message: string;
    visible: boolean;
  };
}

export const useTTS = (): UseTTSReturn => {
  const [feedback, setFeedback] = useState({
    message: '',
    visible: false,
  });

  const showFeedback = useCallback((message: string) => {
    setFeedback({ message, visible: true });
    
    // Use browser's built-in TTS
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(message);
      utterance.rate = 0.9;
      utterance.pitch = 1;
      speechSynthesis.speak(utterance);
    }
    
    // Hide feedback after 3 seconds
    setTimeout(() => {
      setFeedback(prev => ({ ...prev, visible: false }));
    }, 3000);
  }, []);

  return {
    showFeedback,
    feedback,
  };
};
