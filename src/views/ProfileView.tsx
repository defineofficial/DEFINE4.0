import React from 'react';
import { ScreenType } from '../types';

interface ProfileViewProps {
  onSelectScreen: (screen: ScreenType) => void;
  onOpenWorkspaceModal: () => void;
  onOpenFlashcards: () => void;
  onShowToast: (msg: string) => void;
}

export const ProfileView: React.FC<ProfileViewProps> = ({
  onSelectScreen,
  onOpenWorkspaceModal,
  onOpenFlashcards,
  onShowToast
}) => {
  return (
    <div className="flex flex-col w-full pb-10 space-y-4 animate-fadeIn">
      {/* Profile Card */}
      <div className="bg-white rounded-3xl p-6 shadow-xs border border-black/[0.04] text-center">
        <div className="w-20 h-20 rounded-full bg-[#3f4dbf] mx-auto flex items-center justify-center text-white text-3xl font-bold shadow-md">
          A
        </div>
        <h3 className="font-headline text-xl text-[#131c2a] font-bold mt-3">Aanya Sharma</h3>
        <p className="font-body text-xs text-[#58605a]">Computer Science & Engineering · Semester 4</p>

        <div className="mt-3.5 flex justify-center gap-2">
          <span className="px-3 py-1 bg-[#dce5dd] text-[#151d19] rounded-full text-xs font-semibold">
            Scholar Plan
          </span>
          <span className="px-3 py-1 bg-[#dfe0ff] text-[#000a64] rounded-full text-xs font-semibold">
            Cloud Vault Sync Active
          </span>
        </div>
      </div>

      {/* Study Stats & Academic Settings */}
      <div className="bg-white rounded-2xl p-4 shadow-xs border border-black/[0.04] space-y-3">
        <h4 className="font-headline text-xs font-bold uppercase tracking-wider text-[#131c2a]">
          Academic Activity & Goals
        </h4>

        <div className="flex justify-between items-center py-2 border-b border-black/[0.04]">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-[#3f4dbf] text-[18px]">timer</span>
            <span className="font-label-lg text-xs font-medium text-[#131c2a]">Daily Study Goal</span>
          </div>
          <span className="font-label-md text-xs text-[#3f4dbf] font-bold">2.5 hrs (Completed 78%)</span>
        </div>

        <div className="flex justify-between items-center py-2 border-b border-black/[0.04]">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-[#58605a] text-[18px]">cloud</span>
            <span className="font-label-lg text-xs font-medium text-[#131c2a]">Storage Used</span>
          </div>
          <span className="font-label-md text-xs text-[#58605a]">1.2 GB of 15 GB</span>
        </div>

        <div className="flex justify-between items-center py-2 border-b border-black/[0.04]">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-emerald-600 text-[18px]">download_done</span>
            <span className="font-label-lg text-xs font-medium text-[#131c2a]">Offline Cached Notes</span>
          </div>
          <span className="font-label-md text-xs text-[#58605a]">18 PDFs downloaded</span>
        </div>

        <div
          onClick={onOpenWorkspaceModal}
          className="flex justify-between items-center py-2 border-b border-black/[0.04] cursor-pointer hover:bg-gray-50 rounded-lg px-1 transition-colors"
        >
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-[#5967d9] text-[18px]">school</span>
            <span className="font-label-lg text-xs font-medium text-[#131c2a]">Current Workspace</span>
          </div>
          <span className="font-label-md text-xs text-[#3f4dbf] font-semibold flex items-center gap-0.5">
            <span>CS · Sem 4</span>
            <span className="material-symbols-outlined text-[14px]">chevron_right</span>
          </span>
        </div>

        <div
          onClick={onOpenFlashcards}
          className="flex justify-between items-center py-2 cursor-pointer hover:bg-gray-50 rounded-lg px-1 transition-colors"
        >
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-amber-500 text-[18px]">bolt</span>
            <span className="font-label-lg text-xs font-medium text-[#131c2a]">Active Recall Drill</span>
          </div>
          <span className="font-label-md text-xs text-[#3f4dbf] font-semibold">5 Cards Ready →</span>
        </div>
      </div>

      {/* Return to Dashboard Button */}
      <button
        onClick={() => onSelectScreen('dashboard')}
        className="w-full py-3 rounded-2xl bg-[#dfe8fd] text-[#131c2a] font-label-lg text-xs font-bold active-haptic hover:bg-[#dae3f7] transition-colors"
      >
        Return to Study Dashboard
      </button>
    </div>
  );
};
