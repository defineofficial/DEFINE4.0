import React from 'react';
import { WORKSPACES } from '../data/mockData';

interface WorkspaceModalProps {
  isOpen: boolean;
  activeId: string;
  onSelect: (ws: typeof WORKSPACES[0]) => void;
  onClose: () => void;
}

export const WorkspaceModal: React.FC<WorkspaceModalProps> = ({
  isOpen,
  activeId,
  onSelect,
  onClose
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-[#283140]/60 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />

      {/* Sheet */}
      <div className="relative z-10 w-full max-w-md bg-white rounded-t-[32px] sm:rounded-3xl p-5 shadow-2xl border-t border-black/[0.05]">
        <div className="w-12 h-1.5 rounded-full bg-gray-300 mx-auto mb-4 sm:hidden" />

        <div className="flex items-center justify-between mb-3">
          <h3 className="font-headline text-lg text-[#131c2a] font-bold">
            Switch Study Workspace
          </h3>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center text-[#58605a] active-haptic"
          >
            <span className="material-symbols-outlined text-[18px]">close</span>
          </button>
        </div>

        <p className="font-body text-xs text-[#58605a] mb-3">
          Each workspace has its own curated courses, lecture slides, and past papers.
        </p>

        <div className="space-y-2">
          {WORKSPACES.map((ws) => {
            const isSelected = ws.id === activeId;
            return (
              <button
                key={ws.id}
                onClick={() => {
                  onSelect(ws);
                  onClose();
                }}
                className={`w-full p-3.5 rounded-2xl flex items-center justify-between text-left active-haptic transition-all ${
                  isSelected
                    ? 'bg-[#E5EEE6] border border-[#d2ded3]'
                    : 'bg-[#F7F5F0] hover:bg-gray-100 border border-transparent'
                }`}
              >
                <div className="flex items-center gap-3">
                  <div
                    className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                      isSelected ? 'bg-[#3f4dbf] text-white' : 'bg-white text-[#58605a]'
                    } shadow-xs flex-shrink-0`}
                  >
                    <span className="material-symbols-outlined text-[20px]">school</span>
                  </div>
                  <div>
                    <p className="font-headline text-sm font-bold text-[#131c2a]">
                      {ws.shortName}
                    </p>
                    <p className="font-body text-[11px] text-[#58605a] mt-0.5">
                      {ws.stats}
                    </p>
                  </div>
                </div>

                {isSelected ? (
                  <span className="material-symbols-outlined text-[#3f4dbf] text-[22px]">
                    check_circle
                  </span>
                ) : (
                  <span className="material-symbols-outlined text-gray-400 text-[20px]">
                    chevron_right
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};
