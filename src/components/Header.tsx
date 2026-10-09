import React, { useState } from 'react';
import { ScreenType } from '../types';

interface HeaderProps {
  currentScreen: ScreenType;
  workspaceName: string;
  onOpenWorkspaceModal: () => void;
  onSearchChange: (q: string) => void;
  searchQuery: string;
  onSelectScreen: (screen: ScreenType) => void;
  onShowToast: (msg: string) => void;
}

export const Header: React.FC<HeaderProps> = ({
  currentScreen,
  workspaceName,
  onOpenWorkspaceModal,
  onSearchChange,
  searchQuery,
  onSelectScreen,
  onShowToast
}) => {
  const [searchExpanded, setSearchExpanded] = useState(false);

  // Label based on current screen
  const getContextLabel = () => {
    switch (currentScreen) {
      case 'collections':
        return 'Collections';
      case 'library':
        return 'Library';
      case 'reader':
        return 'Reader View';
      case 'add':
        return 'Add Resource';
      case 'saved':
        return 'Saved Vault';
      case 'profile':
        return 'Profile';
      default:
        return workspaceName;
    }
  };

  return (
    <header className="fixed top-0 w-full z-40 pt-safe bg-[#F7F5F0]/90 backdrop-blur-xl border-b border-black/[0.04] transition-all">
      <div className="h-16 px-4 sm:px-6 max-w-lg mx-auto flex items-center justify-between gap-3">
        {/* Brand / Context Selector */}
        <div className="flex items-center gap-2.5 min-w-0">
          <button
            onClick={() => {
              onSelectScreen('dashboard');
              onShowToast('NoteVault Academic Sanctuary');
            }}
            className="w-10 h-10 rounded-xl bg-[#5967d9] flex items-center justify-center text-white shadow-sm flex-shrink-0 active-haptic"
            title="NoteVault Home"
          >
            <span className="material-symbols-outlined text-[22px]">local_library</span>
          </button>

          {/* Workspace Pill Trigger */}
          <button
            onClick={onOpenWorkspaceModal}
            className="flex items-center gap-1.5 min-w-0 px-3 py-1 rounded-full bg-white/80 border border-black/[0.06] hover:bg-white active-haptic transition-all shadow-xs"
          >
            <span className="material-symbols-outlined text-[#58605a] text-[16px]">folder_special</span>
            <span className="font-label-md text-xs font-semibold text-[#131c2a] truncate max-w-[120px]">
              {getContextLabel()}
            </span>
            <span className="material-symbols-outlined text-[#58605a] text-[14px]">expand_more</span>
          </button>
        </div>

        {/* Right Action Icons */}
        <div className="flex items-center gap-1">
          <button
            aria-label="Search vault"
            onClick={() => {
              setSearchExpanded(!searchExpanded);
              if (currentScreen !== 'library' && currentScreen !== 'dashboard') {
                onSelectScreen('library');
              }
            }}
            className={`w-10 h-10 flex items-center justify-center rounded-full transition-colors active-haptic ${
              searchExpanded ? 'bg-[#dfe0ff] text-[#3f4dbf]' : 'text-[#58605a] hover:text-[#131c2a] hover:bg-white/80'
            }`}
          >
            <span className="material-symbols-outlined text-[22px]">search</span>
          </button>

          <button
            aria-label="Notifications"
            onClick={() => onShowToast('All 3 semester course syllabi are synchronized!')}
            className="w-10 h-10 relative flex items-center justify-center rounded-full text-[#58605a] hover:text-[#131c2a] hover:bg-white/80 active-haptic transition-colors"
          >
            <span className="material-symbols-outlined text-[22px]">notifications</span>
            <span className="absolute top-2 right-2 w-2 h-2 bg-[#ba1a1a] rounded-full ring-2 ring-[#F7F5F0]"></span>
          </button>

          <button
            onClick={() => onSelectScreen('profile')}
            className="w-8 h-8 rounded-full bg-[#3f4dbf] flex items-center justify-center shadow-sm ml-1 flex-shrink-0 cursor-pointer active-haptic"
            title="Student Profile"
          >
            <span className="material-symbols-outlined text-white text-[18px]">person</span>
          </button>
        </div>
      </div>

      {/* Expandable Live Search Input */}
      {searchExpanded && (
        <div className="px-4 pb-3 pt-1 border-t border-black/[0.04] max-w-lg mx-auto animate-fadeIn">
          <div className="relative flex items-center">
            <span className="material-symbols-outlined text-[#58605a] text-[18px] absolute left-3">search</span>
            <input
              autoFocus
              value={searchQuery}
              onChange={(e) => onSearchChange(e.target.value)}
              placeholder="Search notes, PYQs, videos, algorithms..."
              className="w-full bg-white pl-9 pr-9 py-2 rounded-xl text-sm font-body border border-black/[0.08] focus:outline-none focus:ring-2 focus:ring-[#3f4dbf]/30 transition-all text-[#131c2a] placeholder:text-[#58605a]/60 shadow-xs"
            />
            {searchQuery && (
              <button
                onClick={() => onSearchChange('')}
                className="absolute right-3 w-5 h-5 rounded-full bg-gray-100 flex items-center justify-center text-gray-500 hover:text-gray-800"
              >
                <span className="material-symbols-outlined text-[14px]">close</span>
              </button>
            )}
          </div>
          <div className="mt-2 flex items-center justify-between text-[11px] font-medium text-[#58605a] px-1">
            <span>
              {searchQuery ? `Searching for "${searchQuery}"` : 'Type to search 128 resources in vault'}
            </span>
            {searchQuery && (
              <button
                onClick={() => {
                  onSearchChange('');
                  setSearchExpanded(false);
                }}
                className="text-[#3f4dbf] hover:underline"
              >
                Clear
              </button>
            )}
          </div>
        </div>
      )}
    </header>
  );
};
