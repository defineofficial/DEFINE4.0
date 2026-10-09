import React from 'react';
import { ScreenType } from '../types';

interface BottomNavProps {
  currentScreen: ScreenType;
  onSelectScreen: (screen: ScreenType) => void;
}

export const BottomNav: React.FC<BottomNavProps> = ({ currentScreen, onSelectScreen }) => {
  return (
    <nav className="fixed bottom-0 w-full z-40 pb-safe bg-[#F7F5F0]/95 backdrop-blur-xl border-t border-black/[0.05] shadow-[0_-2px_12px_rgba(0,0,0,0.04)]">
      <div className="flex justify-between items-center h-16 px-3 max-w-lg mx-auto relative">
        {/* Tab 1: Dashboard */}
        <button
          onClick={() => onSelectScreen('dashboard')}
          className={`flex flex-col items-center justify-center flex-1 h-full py-1 transition-colors active-haptic min-w-[44px] ${
            currentScreen === 'dashboard' ? 'text-[#3f4dbf] font-bold' : 'text-[#58605a] hover:text-[#131c2a]'
          }`}
        >
          <span className={`material-symbols-outlined text-[22px] ${currentScreen === 'dashboard' ? 'fill-icon' : ''}`}>
            home
          </span>
          <span className="font-label-sm text-[10px] mt-0.5">Dashboard</span>
        </button>

        {/* Tab 2: Library */}
        <button
          onClick={() => onSelectScreen('library')}
          className={`flex flex-col items-center justify-center flex-1 h-full py-1 transition-colors active-haptic min-w-[44px] ${
            currentScreen === 'library' ? 'text-[#3f4dbf] font-bold' : 'text-[#58605a] hover:text-[#131c2a]'
          }`}
        >
          <span className={`material-symbols-outlined text-[22px] ${currentScreen === 'library' ? 'fill-icon' : ''}`}>
            menu_book
          </span>
          <span className="font-label-sm text-[10px] mt-0.5">Library</span>
        </button>

        {/* Tab 3: Center FAB (Add Resource) */}
        <div className="flex flex-col items-center justify-center flex-1 h-full relative -top-3.5">
          <button
            onClick={() => onSelectScreen('add')}
            className="w-12 h-12 rounded-full bg-[#5967d9] text-white flex items-center justify-center shadow-[0_8px_20px_rgba(89,103,217,0.38)] active-haptic hover:brightness-105 transition-all"
            title="Add Resource to Vault"
          >
            <span className="material-symbols-outlined text-[26px]">add</span>
          </button>
          <span className="font-label-sm text-[10px] text-[#58605a] mt-1">Add</span>
        </div>

        {/* Tab 4: Saved / Collections */}
        <button
          onClick={() => onSelectScreen('saved')}
          className={`flex flex-col items-center justify-center flex-1 h-full py-1 transition-colors active-haptic min-w-[44px] ${
            currentScreen === 'saved' || currentScreen === 'collections' ? 'text-[#3f4dbf] font-bold' : 'text-[#58605a] hover:text-[#131c2a]'
          }`}
        >
          <span className={`material-symbols-outlined text-[22px] ${currentScreen === 'saved' || currentScreen === 'collections' ? 'fill-icon' : ''}`}>
            bookmark
          </span>
          <span className="font-label-sm text-[10px] mt-0.5">Saved</span>
        </button>

        {/* Tab 5: Profile */}
        <button
          onClick={() => onSelectScreen('profile')}
          className={`flex flex-col items-center justify-center flex-1 h-full py-1 transition-colors active-haptic min-w-[44px] ${
            currentScreen === 'profile' ? 'text-[#3f4dbf] font-bold' : 'text-[#58605a] hover:text-[#131c2a]'
          }`}
        >
          <span className={`material-symbols-outlined text-[22px] ${currentScreen === 'profile' ? 'fill-icon' : ''}`}>
            account_circle
          </span>
          <span className="font-label-sm text-[10px] mt-0.5">Profile</span>
        </button>
      </div>
    </nav>
  );
};
