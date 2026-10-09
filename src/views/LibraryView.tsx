import React, { useState } from 'react';
import { Resource } from '../types';

interface LibraryViewProps {
  resources: Resource[];
  searchQuery: string;
  onSearchChange: (q: string) => void;
  onSelectResource: (res: Resource) => void;
  onToggleSave: (id: string) => void;
  onOpenFlashcards: () => void;
  onShowToast: (msg: string) => void;
}

export const LibraryView: React.FC<LibraryViewProps> = ({
  resources,
  searchQuery,
  onSearchChange,
  onSelectResource,
  onToggleSave,
  onOpenFlashcards,
  onShowToast
}) => {
  const [selectedType, setSelectedType] = useState('all');
  const [filterTags, setFilterTags] = useState<string[]>(['Data Structures', 'Graphs']);
  const [sortOption, setSortOption] = useState('Most relevant');

  const removeFilterTag = (tag: string) => {
    setFilterTags(filterTags.filter((t) => t !== tag));
    onShowToast(`Removed filter: ${tag}`);
  };

  const filteredResources = resources.filter((item) => {
    const q = searchQuery.toLowerCase().trim();
    const queryMatch =
      !q ||
      item.title.toLowerCase().includes(q) ||
      item.subject.toLowerCase().includes(q) ||
      item.author.toLowerCase().includes(q) ||
      item.typeBadge.toLowerCase().includes(q);

    const typeMatch =
      selectedType === 'all' ||
      (selectedType === 'notes' && (item.type === 'notes' || item.type === 'doc')) ||
      (selectedType === 'pdf' && item.type === 'pdf') ||
      (selectedType === 'video' && item.type === 'video') ||
      (selectedType === 'repo' && item.type === 'repo') ||
      (selectedType === 'pyq' && item.type === 'pyq') ||
      (selectedType === 'book' && (item.type === 'book' || item.type === 'textbook'));

    return queryMatch && typeMatch;
  });

  const savedCount = resources.filter((r) => r.saved).length;

  return (
    <div className="flex flex-col w-full pb-12 space-y-4 animate-fadeIn">
      {/* 1. Search & Filter Controls */}
      <section className="flex flex-col gap-2 pt-1">
        <div className="flex items-center gap-2 w-full">
          <div className="relative flex-1 flex items-center bg-white rounded-2xl shadow-xs border border-black/[0.04]">
            <span className="material-symbols-outlined absolute left-3.5 text-[#58605a] text-[20px]">
              search
            </span>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => onSearchChange(e.target.value)}
              placeholder="Search resources, topics, authors..."
              className="w-full bg-transparent pl-11 pr-10 py-3 font-body text-xs sm:text-sm text-[#131c2a] placeholder-[#58605a] focus:outline-none"
            />
            {searchQuery && (
              <button
                onClick={() => onSearchChange('')}
                className="absolute right-2.5 w-7 h-7 flex items-center justify-center rounded-full text-[#58605a] hover:bg-gray-100 transition-colors"
              >
                <span className="material-symbols-outlined text-[16px]">close</span>
              </button>
            )}
          </div>

          <button
            onClick={() => onShowToast('Advanced facets: Midterms, Endterms, Verified Notes, Video breakdowns')}
            className="w-12 h-12 flex-shrink-0 flex items-center justify-center rounded-2xl bg-white text-[#58605a] shadow-xs hover:text-[#3f4dbf] active:scale-95 transition-transform border border-black/[0.04]"
            title="Filter facets"
          >
            <span className="material-symbols-outlined text-[22px]">tune</span>
          </button>
        </div>

        {/* Filter Pills (Horizontal Scroll) */}
        <div className="flex items-center gap-2 overflow-x-auto no-scrollbar py-1 -mx-4 px-4 sm:mx-0 sm:px-0">
          {[
            { id: 'all', label: 'All types' },
            { id: 'notes', label: 'Notes' },
            { id: 'pdf', label: 'PDFs' },
            { id: 'video', label: 'YouTube videos' },
            { id: 'repo', label: 'GitHub repositories' },
            { id: 'pyq', label: 'PYQs' },
            { id: 'book', label: 'Textbooks' }
          ].map((pill) => {
            const isSelected = selectedType === pill.id;
            return (
              <button
                key={pill.id}
                onClick={() => setSelectedType(pill.id)}
                className={`flex-shrink-0 px-3.5 py-1.5 rounded-full font-label-md text-xs font-semibold transition-all active-haptic whitespace-nowrap shadow-xs ${
                  isSelected
                    ? 'bg-[#5967d9] text-white'
                    : 'bg-white text-[#58605a] hover:text-[#131c2a] hover:bg-gray-100'
                }`}
              >
                {pill.label}
              </button>
            );
          })}
        </div>
      </section>

      {/* 2. Filter Context Bar */}
      <section className="flex flex-col gap-1.5 mt-1">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="font-label-md text-xs text-[#58605a]">
              {filteredResources.length} results for{' '}
              <span className="text-[#131c2a] font-bold">“{searchQuery || 'graphs'}”</span>
            </span>
            <span className="text-gray-400 text-xs">•</span>
            {filterTags.map((tag) => (
              <div
                key={tag}
                className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-[#e7eeff] text-[#131c2a] font-label-sm text-[11px]"
              >
                <span>{tag}</span>
                <span
                  onClick={() => removeFilterTag(tag)}
                  className="material-symbols-outlined text-[12px] cursor-pointer hover:text-[#ba1a1a]"
                >
                  close
                </span>
              </div>
            ))}
          </div>

          <button
            onClick={() => {
              const opts = ['Most relevant', 'Recently added', 'Highest rated'];
              const next = opts[(opts.indexOf(sortOption) + 1) % opts.length];
              setSortOption(next);
              onShowToast(`Sorted by: ${next}`);
            }}
            className="flex items-center gap-1 px-2.5 py-1 rounded-full bg-white text-[#58605a] shadow-xs hover:text-[#131c2a] transition-colors border border-black/[0.04]"
          >
            <span className="font-label-sm text-[11px] font-semibold">Sort: {sortOption}</span>
            <span className="material-symbols-outlined text-[14px]">arrow_drop_down</span>
          </button>
        </div>
      </section>

      {/* 3. AI Companion Micro-banner */}
      <section
        onClick={onOpenFlashcards}
        className="w-full p-3.5 rounded-2xl bg-white shadow-xs border border-black/[0.04] flex items-center justify-between gap-3 cursor-pointer active-haptic hover:border-[#3f4dbf]/30 transition-all"
      >
        <div className="flex items-center gap-2.5 min-w-0">
          <div className="w-8 h-8 rounded-lg bg-[#5967d9] text-white flex items-center justify-center flex-shrink-0 shadow-xs">
            <span className="material-symbols-outlined text-[18px]">auto_awesome</span>
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-1.5">
              <span className="font-headline text-xs sm:text-sm font-bold text-[#131c2a]">
                Curated Graph Synthesis
              </span>
              <span className="text-[9px] uppercase tracking-wider px-1.5 py-0.2 rounded bg-[#202938] text-white font-bold">
                BETA
              </span>
            </div>
            <p className="font-body text-xs text-[#58605a] truncate">
              Synthesized 6 items into an active revision deck
            </p>
          </div>
        </div>

        <button className="w-8 h-8 rounded-full bg-[#f0f3ff] flex items-center justify-center text-[#3f4dbf] flex-shrink-0 hover:bg-[#dfe8fd] transition-colors">
          <span className="material-symbols-outlined text-[18px]">chevron_right</span>
        </button>
      </section>

      {/* 4. Tactile Book-Spine Resource Stream */}
      <section className="flex flex-col gap-3">
        {filteredResources.map((item) => (
          <article
            key={item.id}
            onClick={() => onSelectResource(item)}
            className="relative flex bg-white rounded-2xl overflow-hidden shadow-xs border border-black/[0.04] active:scale-[0.99] transition-all cursor-pointer hover:border-black/[0.1]"
          >
            {/* Tactile Book Spine Simulator */}
            <div
              className={`w-2.5 bg-gradient-to-r ${
                item.spineGradient || 'from-[#4d5a74] via-[#dfe8fd] to-white'
              } flex-shrink-0 book-spine-tactile`}
            />

            {/* Visual Thumbnail */}
            <div className="w-24 min-h-[120px] relative bg-[#f0f3ff] flex-shrink-0 overflow-hidden">
              {item.imageUrl ? (
                <img
                  src={item.imageUrl}
                  alt={item.title}
                  className="w-full h-full object-cover"
                  referrerPolicy="no-referrer"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-[#3f4dbf]">
                  <span className="material-symbols-outlined text-[32px]">{item.icon}</span>
                </div>
              )}

              {/* Gradient scrim & Format badge */}
              <div className="absolute inset-0 bg-gradient-to-t from-black/40 via-transparent to-transparent" />
              <span className="absolute top-2 left-2 px-1.5 py-0.5 rounded bg-white/90 backdrop-blur-md font-label-sm text-[10px] text-[#131c2a] font-bold">
                {item.typeBadge}
              </span>

              {item.type === 'video' && (
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="w-7 h-7 rounded-full bg-white/90 backdrop-blur-md flex items-center justify-center text-[#ba1a1a] shadow-xs">
                    <span className="material-symbols-outlined text-[18px] fill-icon">play_arrow</span>
                  </div>
                </div>
              )}
            </div>

            {/* Card Body */}
            <div className="flex-1 p-3 flex flex-col justify-between min-w-0">
              <div>
                <div className="flex items-start justify-between gap-1 mb-1">
                  <h3 className="font-headline text-xs sm:text-sm font-bold text-[#131c2a] truncate">
                    {item.title}
                  </h3>
                  {item.saved ? (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onToggleSave(item.id);
                      }}
                      className="inline-flex items-center gap-0.5 px-2 py-0.5 rounded-full bg-[#dce5dd] text-[#151d19] font-label-sm text-[11px] font-semibold flex-shrink-0 active-haptic"
                    >
                      <span className="material-symbols-outlined text-[12px] fill-icon text-[#3f4dbf]">
                        bookmark
                      </span>
                      <span>Saved</span>
                    </button>
                  ) : (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onToggleSave(item.id);
                      }}
                      className="inline-flex items-center gap-0.5 px-2.5 py-0.5 rounded-full bg-[#5967d9] text-white font-label-sm text-[11px] font-semibold flex-shrink-0 active-haptic"
                    >
                      <span className="material-symbols-outlined text-[12px]">add</span>
                      <span>Save</span>
                    </button>
                  )}
                </div>
                <p className="font-body text-xs text-[#58605a] line-clamp-1">
                  {item.author} • {item.subjectName}
                </p>
              </div>

              <div className="flex items-center justify-between text-[#58605a] pt-2">
                <div className="flex items-center gap-2 font-label-md text-[11px]">
                  {item.pages && (
                    <span className="flex items-center gap-1">
                      <span className="material-symbols-outlined text-[14px]">article</span>
                      <span>{item.pages}</span>
                    </span>
                  )}
                  {item.duration && (
                    <span className="flex items-center gap-1">
                      <span className="material-symbols-outlined text-[14px]">timer</span>
                      <span>{item.duration}</span>
                    </span>
                  )}
                  <span>•</span>
                  <span>{item.updatedAt || 'Recent'}</span>
                </div>

                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onSelectResource(item);
                  }}
                  className="w-7 h-7 rounded-full flex items-center justify-center text-[#58605a] hover:text-[#131c2a] hover:bg-gray-100"
                >
                  <span className="material-symbols-outlined text-[18px]">more_horiz</span>
                </button>
              </div>
            </div>
          </article>
        ))}
      </section>

      {/* 5. Sticky Bottom Summary Floating Pill */}
      <div className="sticky bottom-20 z-30 self-center mt-4">
        <div className="px-4 py-2 rounded-full bg-[#202938]/90 backdrop-blur-md text-white shadow-lg flex items-center gap-2 text-xs font-semibold">
          <span className="w-2 h-2 rounded-full bg-[#dfe0ff] animate-pulse" />
          <span>{filteredResources.length} matches</span>
          <span className="text-gray-400">•</span>
          <span className="text-[#bcc2ff]">{savedCount} saved to your vault</span>
        </div>
      </div>
    </div>
  );
};
