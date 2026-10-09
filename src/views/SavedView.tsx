import React, { useState } from 'react';
import { Resource } from '../types';

interface SavedViewProps {
  resources: Resource[];
  onSelectResource: (res: Resource) => void;
  onToggleSave: (id: string) => void;
  onOpenReader: () => void;
  onShowToast: (msg: string) => void;
}

export const SavedView: React.FC<SavedViewProps> = ({
  resources,
  onSelectResource,
  onToggleSave,
  onOpenReader,
  onShowToast
}) => {
  const [selectedSubject, setSelectedSubject] = useState('ALL');

  const savedList = resources.filter((r) => r.saved);
  const filteredList = savedList.filter(
    (r) => selectedSubject === 'ALL' || r.subject === selectedSubject
  );

  return (
    <div className="flex flex-col w-full pb-10 space-y-4 animate-fadeIn">
      <div className="bg-white rounded-2xl p-4 shadow-xs border border-black/[0.04]">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="font-headline text-xl sm:text-2xl font-bold text-[#131c2a]">
              Saved Vault
            </h2>
            <p className="font-body text-xs text-[#58605a] mt-0.5">
              {savedList.length} curated resources pinned for quick reference
            </p>
          </div>
          <span className="px-2.5 py-1 rounded-full bg-[#dce5dd] text-[#151d19] font-label-sm text-xs font-bold">
            Permanent Sync
          </span>
        </div>

        {/* Filter Chips */}
        <div className="flex items-center gap-2 mt-3 overflow-x-auto no-scrollbar">
          {['ALL', 'CS204', 'CS206', 'MA202'].map((subj) => (
            <button
              key={subj}
              onClick={() => setSelectedSubject(subj)}
              className={`px-3 py-1 rounded-full text-xs font-semibold active-haptic transition-all ${
                selectedSubject === subj
                  ? 'bg-[#3f4dbf] text-white shadow-xs'
                  : 'bg-[#F7F5F0] text-[#58605a] hover:bg-gray-200'
              }`}
            >
              {subj === 'ALL' ? 'All Subjects' : subj}
            </button>
          ))}
        </div>
      </div>

      {filteredList.length === 0 ? (
        <div className="bg-white rounded-2xl p-8 text-center border border-black/[0.04] space-y-2">
          <span className="material-symbols-outlined text-4xl text-[#58605a]">bookmark_remove</span>
          <h3 className="font-headline text-base font-bold text-[#131c2a]">No saved items in this subject</h3>
          <p className="font-body text-xs text-[#58605a]">
            Tap the bookmark icon on any paper or lecture in Library to pin it here.
          </p>
        </div>
      ) : (
        <div className="flex flex-col gap-2.5">
          {filteredList.map((item) => (
            <div
              key={item.id}
              onClick={() => {
                if (item.type === 'pyq') {
                  onOpenReader();
                } else {
                  onSelectResource(item);
                }
              }}
              className="bg-white rounded-2xl p-3.5 shadow-xs border border-black/[0.04] flex items-center justify-between active-haptic cursor-pointer hover:border-black/[0.1] transition-all"
            >
              <div className="flex items-center gap-3 min-w-0">
                <div
                  className={`w-11 h-11 rounded-xl ${item.colorClass} flex items-center justify-center flex-shrink-0`}
                >
                  <span className="material-symbols-outlined text-[20px]">{item.icon}</span>
                </div>
                <div className="min-w-0">
                  <div className="flex items-center gap-1.5 mb-0.5">
                    <span className="font-label-sm text-[10px] px-1.5 py-0.2 rounded bg-[#F7F5F0] text-[#58605a] font-bold">
                      {item.typeBadge}
                    </span>
                    <span className="text-[11px] font-semibold text-[#58605a]">{item.subject}</span>
                  </div>
                  <h4 className="font-headline text-xs sm:text-sm font-semibold text-[#131c2a] truncate">
                    {item.title}
                  </h4>
                  <p className="font-body text-[11px] text-[#58605a] truncate mt-0.5">
                    {item.author} · {item.meta}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-1 flex-shrink-0 ml-2">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onToggleSave(item.id);
                  }}
                  className="p-2 text-[#3f4dbf] active-haptic hover:scale-110"
                  title="Remove from saved"
                >
                  <span className="material-symbols-outlined fill-icon text-[20px]">
                    bookmark
                  </span>
                </button>
                <span className="material-symbols-outlined text-gray-400 text-[18px]">
                  chevron_right
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
