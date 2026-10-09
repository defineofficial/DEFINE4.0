import React from 'react';
import { Resource } from '../types';

interface ResourceDetailModalProps {
  resource: Resource | null;
  isOpen: boolean;
  onClose: () => void;
  onToggleSave: (id: string) => void;
  onOpenReader: (resource: Resource) => void;
  onShowToast: (msg: string) => void;
}

export const ResourceDetailModal: React.FC<ResourceDetailModalProps> = ({
  resource,
  isOpen,
  onClose,
  onToggleSave,
  onOpenReader,
  onShowToast
}) => {
  if (!isOpen || !resource) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-[#283140]/60 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />

      {/* Sheet */}
      <div className="relative z-10 w-full max-w-lg bg-white rounded-t-[32px] sm:rounded-3xl p-5 shadow-2xl flex flex-col max-h-[90vh] overflow-y-auto border-t border-black/[0.05]">
        <div className="w-12 h-1.5 rounded-full bg-gray-300 mx-auto mb-4 sm:hidden" />

        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider bg-[#dfe0ff] text-[#000a64]">
              {resource.typeBadge}
            </span>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-gray-100 text-[#58605a]">
              {resource.subject}
            </span>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center text-[#58605a] hover:text-[#131c2a] active-haptic"
          >
            <span className="material-symbols-outlined text-[20px]">close</span>
          </button>
        </div>

        <h3 className="font-headline text-xl text-[#131c2a] font-bold mt-3 leading-snug">
          {resource.title}
        </h3>

        <p className="font-body text-xs text-[#58605a] mt-1">
          {resource.meta} · {resource.author}
        </p>

        {/* Thumbnail Preview if available */}
        {resource.imageUrl && (
          <div className="w-full h-36 rounded-xl overflow-hidden mt-3 shadow-xs bg-[#f0f3ff] relative">
            <img
              src={resource.imageUrl}
              alt={resource.title}
              className="w-full h-full object-cover"
              referrerPolicy="no-referrer"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-black/50 via-transparent to-transparent flex items-end p-2.5">
              <span className="text-[11px] text-white font-medium flex items-center gap-1">
                <span className="material-symbols-outlined text-[14px]">school</span>
                <span>Verified Faculty Material</span>
              </span>
            </div>
          </div>
        )}

        {/* Reading Progress */}
        <div className="bg-[#F7F5F0] rounded-xl p-3 mt-4 border border-black/[0.04]">
          <div className="flex justify-between items-center text-xs text-[#58605a] mb-1.5">
            <span>Course Progress</span>
            <span className="font-bold text-[#3f4dbf]">{resource.progress}% Completed</span>
          </div>
          <div className="w-full bg-black/10 h-2 rounded-full overflow-hidden">
            <div
              className="bg-[#3f4dbf] h-full rounded-full transition-all duration-300"
              style={{ width: `${resource.progress}%` }}
            />
          </div>
        </div>

        {/* Highlights */}
        <div className="mt-4 space-y-2">
          <h4 className="font-headline text-xs font-bold uppercase tracking-wider text-[#131c2a]">
            Curated Highlights & Syllabus Anchor
          </h4>
          <div className="text-xs text-[#58605a] space-y-1.5 pl-3 list-disc">
            {resource.highlights && resource.highlights.length > 0 ? (
              resource.highlights.map((h, i) => <p key={i}>• {h}</p>)
            ) : (
              <p>• Department verified academic lecture revision note.</p>
            )}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="mt-6 pt-3 border-t border-black/[0.06] flex flex-col gap-2.5">
          <button
            onClick={() => {
              onClose();
              onOpenReader(resource);
            }}
            className="w-full py-3 rounded-xl bg-[#3f4dbf] text-white font-label-lg font-bold flex items-center justify-center gap-2 shadow-sm active-haptic hover:bg-[#5967d9]"
          >
            <span className="material-symbols-outlined text-[18px]">
              {resource.type === 'video' ? 'play_arrow' : 'menu_book'}
            </span>
            <span>{resource.type === 'video' ? 'Play Video Walkthrough' : 'Open in Document Reader'}</span>
          </button>

          <div className="grid grid-cols-2 gap-2">
            <button
              onClick={() => onToggleSave(resource.id)}
              className={`py-2.5 rounded-xl border border-black/[0.1] font-label-md text-xs font-semibold flex items-center justify-center gap-1.5 active-haptic transition-colors ${
                resource.saved
                  ? 'bg-[#dce5dd] text-[#151d19] border-[#c0c9c1]'
                  : 'bg-white text-[#131c2a] hover:bg-gray-50'
              }`}
            >
              <span className={`material-symbols-outlined text-[18px] ${resource.saved ? 'fill-icon text-[#3f4dbf]' : ''}`}>
                {resource.saved ? 'bookmark' : 'bookmark_border'}
              </span>
              <span>{resource.saved ? 'Saved in Vault' : '+ Save to Vault'}</span>
            </button>

            <button
              onClick={() => {
                onShowToast(`Downloading "${resource.title}" PDF offline cache...`);
              }}
              className="py-2.5 rounded-xl border border-black/[0.1] bg-white font-label-md text-xs font-semibold text-[#131c2a] flex items-center justify-center gap-1.5 active-haptic hover:bg-gray-50"
            >
              <span className="material-symbols-outlined text-[18px]">download</span>
              <span>Download PDF</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
