import React from 'react';
import { Volume2 } from 'lucide-react';

interface TTSFeedbackProps {
  message: string;
  visible: boolean;
}

export const TTSFeedback: React.FC<TTSFeedbackProps> = ({ message, visible }) => {
  if (!visible) return null;

  return (
    <div className="fixed bottom-8 right-8 bg-dark-900 border border-dark-800 rounded-xl p-4 shadow-2xl transform transition-all duration-300 animate-slide-up z-50 max-w-sm">
      <div className="flex items-center gap-3">
        <Volume2 className="w-5 h-5 text-primary-500" />
        <span className="text-sm text-dark-100">{message}</span>
      </div>
    </div>
  );
};
