import { useState } from 'react';
import { ShieldAlert, Check, X, Edit3 } from 'lucide-react';

export interface PendingAction {
  actionId: string;
  actionType: string;
  reversibility: string;
  description: string;
  target?: string;
}

interface HITLModalProps {
  action: PendingAction | null;
  onApprove: (actionId: string, modifiedIntent?: Record<string, unknown>) => void;
  onDeny: (actionId: string) => void;
}

export const HITLModal = ({ action, onApprove, onDeny }: HITLModalProps) => {
  const [editing, setEditing] = useState(false);
  const [editedDescription, setEditedDescription] = useState('');
  const [editedTarget, setEditedTarget] = useState('');

  if (!action) return null;

  const handleApprove = () => {
    if (editing) {
      const modified: Record<string, unknown> = {
        description: editedDescription || action.description,
        target: editedTarget || action.target,
        action_type: action.actionType,
        reversibility: action.reversibility,
      };
      onApprove(action.actionId, modified);
    } else {
      onApprove(action.actionId);
    }
    setEditing(false);
  };

  const handleDeny = () => {
    onDeny(action.actionId);
    setEditing(false);
  };

  const startEditing = () => {
    setEditedDescription(action.description);
    setEditedTarget(action.target || '');
    setEditing(true);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-dark-900 border border-red-500/50 rounded-xl shadow-2xl w-full max-w-md mx-4 p-6">
        <div className="flex items-center gap-3 mb-4">
          <ShieldAlert className="text-red-400 w-6 h-6 flex-shrink-0" />
          <h2 className="text-white font-semibold text-lg">Approval Required</h2>
        </div>

        <div className="space-y-3 mb-6">
          <div className="flex gap-2">
            <span className="text-xs text-gray-400 w-24 flex-shrink-0 pt-0.5">Action</span>
            <span className="text-sm text-white font-mono bg-dark-800 px-2 py-0.5 rounded">
              {action.actionType}
            </span>
          </div>

          <div className="flex gap-2">
            <span className="text-xs text-gray-400 w-24 flex-shrink-0 pt-0.5">Risk</span>
            <span className="text-xs text-red-400 bg-red-500/10 border border-red-500/30 px-2 py-0.5 rounded">
              {action.reversibility}
            </span>
          </div>

          <div className="flex gap-2">
            <span className="text-xs text-gray-400 w-24 flex-shrink-0 pt-0.5">Description</span>
            {editing ? (
              <textarea
                className="text-sm text-white bg-dark-800 border border-gray-600 rounded px-2 py-1 flex-1 resize-none"
                rows={2}
                value={editedDescription}
                onChange={e => setEditedDescription(e.target.value)}
              />
            ) : (
              <span className="text-sm text-gray-200">{action.description}</span>
            )}
          </div>

          {(action.target || editing) && (
            <div className="flex gap-2">
              <span className="text-xs text-gray-400 w-24 flex-shrink-0 pt-0.5">Target</span>
              {editing ? (
                <input
                  className="text-sm text-white bg-dark-800 border border-gray-600 rounded px-2 py-1 flex-1 font-mono"
                  value={editedTarget}
                  onChange={e => setEditedTarget(e.target.value)}
                />
              ) : (
                <span className="text-sm text-gray-400 font-mono">{action.target}</span>
              )}
            </div>
          )}
        </div>

        <div className="flex gap-2">
          {!editing && (
            <button
              onClick={startEditing}
              className="flex items-center gap-1.5 px-3 py-2 text-xs text-gray-300 bg-dark-800 hover:bg-dark-700 border border-gray-600 rounded-lg transition-colors"
            >
              <Edit3 className="w-3.5 h-3.5" />
              Modify
            </button>
          )}
          <div className="flex gap-2 ml-auto">
            <button
              onClick={handleDeny}
              className="flex items-center gap-1.5 px-4 py-2 text-sm text-red-300 bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 rounded-lg transition-colors"
            >
              <X className="w-4 h-4" />
              Deny
            </button>
            <button
              onClick={handleApprove}
              className="flex items-center gap-1.5 px-4 py-2 text-sm text-green-300 bg-green-500/10 hover:bg-green-500/20 border border-green-500/30 rounded-lg transition-colors"
            >
              <Check className="w-4 h-4" />
              {editing ? 'Approve Modified' : 'Approve'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
