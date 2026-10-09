import React, { useState } from 'react';
import { Resource, ScreenType } from '../types';

interface DashboardViewProps {
  resources: Resource[];
  activeSubject: string;
  onSelectResource: (res: Resource) => void;
  onToggleSave: (id: string) => void;
  onOpenFlashcards: () => void;
  onOpenDrill: () => void;
  onOpenAiSolver: () => void;
  onSelectSubject: (code: string) => void;
  onSelectScreen: (screen: ScreenType) => void;
  onShowToast: (msg: string) => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({
  resources,
  activeSubject,
  onSelectResource,
  onToggleSave,
  onOpenFlashcards,
  onOpenDrill,
  onOpenAiSolver,
  onSelectSubject,
  onSelectScreen,
  onShowToast
}) => {
  const [selectedFormatFilter, setSelectedFormatFilter] = useState<string>('all');

  const filteredResources = resources.filter((item) => {
    const subjectMatch = activeSubject === 'ALL' || item.subject === activeSubject;
    const formatMatch =
      selectedFormatFilter === 'all' ||
      (selectedFormatFilter === 'pyq' && item.type === 'pyq') ||
      (selectedFormatFilter === 'notes' && (item.type === 'notes' || item.type === 'doc')) ||
      (selectedFormatFilter === 'video' && item.type === 'video') ||
      (selectedFormatFilter === 'textbook' && (item.type === 'textbook' || item.type === 'book'));
    return subjectMatch && formatMatch;
  });

  const savedResources = resources.filter((r) => r.saved);

  return (
    <div className="flex flex-col w-full pb-8 space-y-5 animate-fadeIn">
      {/* 1. Workspace Header Greeting */}
      <div className="flex flex-col gap-1 pt-1">
        <div className="flex items-center justify-between">
          <div
            onClick={() => onSelectScreen('collections')}
            className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#E5EEE6] text-[#243B29] cursor-pointer active-haptic border border-[#d2ded3] shadow-xs"
          >
            <span className="material-symbols-outlined text-[16px] text-[#3f4dbf]">school</span>
            <span className="font-label-md text-xs font-semibold tracking-wide">
              My study workspace · CS · Sem 4
            </span>
            <span className="material-symbols-outlined text-[14px] text-[#58605a]">expand_more</span>
          </div>
          <span className="font-label-md text-xs text-[#58605a]">Friday, 9 Oct</span>
        </div>

        <div className="mt-2.5">
          <h2 className="font-headline text-2xl sm:text-3xl text-[#131c2a] tracking-tight font-bold">
            A little focus goes a long way.
          </h2>
          <p className="font-body text-sm text-[#58605a] mt-0.5">
            Welcome back, <span className="font-semibold text-[#131c2a]">Aanya</span>. Ready for deep work?
          </p>
        </div>
      </div>

      {/* 2. Milestone Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-[#202938] text-[#ecf1ff] p-5 shadow-md">
        <div className="absolute -right-10 -top-10 w-48 h-48 rounded-full bg-[#5967d9]/25 blur-2xl pointer-events-none" />
        <div className="relative z-10 flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <span className="font-label-sm text-[11px] uppercase tracking-wider text-[#bcc2ff] bg-white/10 px-2.5 py-0.5 rounded-full font-semibold">
              Your Next Milestone
            </span>
            <span className="font-label-md text-xs font-bold px-2.5 py-0.5 rounded-full bg-white/15 text-[#dfe0ff] tracking-wide font-mono">
              09 DAYS TO GO
            </span>
          </div>

          <div>
            <h3 className="font-headline text-lg sm:text-xl text-white leading-snug font-bold">
              DSA exam, minus the last-minute scramble.
            </h3>
            <p className="font-body text-xs text-[#bcc2ff]/90 mt-1 flex items-center gap-1.5">
              <span className="material-symbols-outlined text-[16px]">event_available</span>
              <span>12 saved resources · 18 Oct</span>
            </p>
          </div>

          <div className="pt-1">
            <button
              onClick={() => onSelectScreen('collections')}
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-[#5967d9] text-white font-label-lg text-sm font-semibold shadow-sm active-haptic transition-all hover:brightness-110"
            >
              <span>Open DSA exam prep</span>
              <span className="material-symbols-outlined text-[18px]">arrow_forward</span>
            </button>
          </div>
        </div>
      </div>

      {/* 2.5 Active Recall Flashcard Sprint Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-[#3f4dbf] via-[#4d5ccb] to-[#2a38ab] text-white p-4.5 shadow-md border border-[#5967d9]/30">
        <div className="absolute -right-6 -bottom-6 w-32 h-32 rounded-full bg-white/10 blur-xl pointer-events-none" />
        <div className="relative z-10 flex flex-col gap-2.5">
          <div className="flex items-center justify-between">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-white/20 text-white font-label-sm text-[11px] backdrop-blur-md font-semibold">
              <span className="material-symbols-outlined text-[14px] text-amber-300">bolt</span>
              <span>Active Recall Quiz</span>
            </span>
            <span className="text-[11px] font-semibold tracking-wide text-[#dfe0ff] uppercase bg-black/20 px-2 py-0.5 rounded-md">
              5 Cards · Spaced Repetition
            </span>
          </div>

          <div>
            <h3 className="font-headline text-base sm:text-lg text-white font-bold leading-tight">
              ✨ Quick Recall Quiz: CS204 Graph Traversals & Algorithms
            </h3>
            <p className="font-body text-xs text-[#bcc2ff] mt-1 leading-relaxed">
              Test essential concepts: BFS/DFS data structures, Dijkstra assumptions, DAGs & spanning trees in 2 minutes.
            </p>
          </div>

          <div className="pt-1 flex items-center gap-2.5">
            <button
              onClick={onOpenFlashcards}
              className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-white text-[#3f4dbf] font-label-lg text-xs sm:text-sm font-bold shadow-md active-haptic transition-all hover:bg-[#F0F3FF]"
            >
              <span className="material-symbols-outlined text-[18px]">style</span>
              <span>Start Flashcard Drill</span>
            </button>
            <button
              onClick={onOpenAiSolver}
              className="w-10 h-10 rounded-xl bg-white/15 flex items-center justify-center text-white active-haptic hover:bg-white/25 transition-colors flex-shrink-0"
              title="Open AI Proof Solver"
            >
              <span className="material-symbols-outlined text-[18px]">psychology</span>
            </button>
          </div>
        </div>
      </div>

      {/* 3. Vault At A Glance Card */}
      <div className="bg-white rounded-2xl p-4 shadow-sm border border-black/[0.04]">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-1.5">
            <span className="material-symbols-outlined text-[#3f4dbf] text-[20px]">auto_stories</span>
            <h4 className="font-headline text-sm text-[#131c2a] font-bold">Vault At A Glance</h4>
          </div>
          <span className="font-label-sm text-[11px] text-[#3f4dbf] font-bold bg-[#dfe0ff] px-2.5 py-0.5 rounded-full">
            +8 added this week
          </span>
        </div>

        <div className="grid grid-cols-3 gap-2.5 text-center">
          <div
            onClick={() => onSelectScreen('library')}
            className="p-3 rounded-xl bg-[#F7F5F0] active-haptic cursor-pointer flex flex-col items-center hover:bg-[#eef2f9] transition-colors"
          >
            <span className="font-headline text-xl text-[#3f4dbf] font-bold">128</span>
            <span className="font-label-sm text-[10px] text-[#58605a] uppercase tracking-tight mt-0.5">
              Resources
            </span>
          </div>

          <div
            onClick={() => onSelectSubject('ALL')}
            className="p-3 rounded-xl bg-[#F7F5F0] active-haptic cursor-pointer flex flex-col items-center hover:bg-[#eef2f9] transition-colors"
          >
            <span className="font-headline text-xl text-[#131c2a] font-bold">3</span>
            <span className="font-label-sm text-[10px] text-[#58605a] uppercase tracking-tight mt-0.5">
              Subjects
            </span>
          </div>

          <div
            onClick={() => onSelectScreen('saved')}
            className="p-3 rounded-xl bg-[#F7F5F0] active-haptic cursor-pointer flex flex-col items-center hover:bg-[#eef2f9] transition-colors"
          >
            <span className="font-headline text-xl text-[#131c2a] font-bold">{savedResources.length}</span>
            <span className="font-label-sm text-[10px] text-[#58605a] uppercase tracking-tight mt-0.5">
              Saved
            </span>
          </div>
        </div>
      </div>

      {/* 4. Filter Tabs / Browse Library */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="font-label-md text-xs text-[#58605a] uppercase tracking-wider font-bold">
            Browse Library
          </span>
          <button
            onClick={() => onSelectScreen('library')}
            className="text-xs text-[#3f4dbf] font-semibold hover:underline"
          >
            All Resources
          </button>
        </div>

        <div className="flex items-center gap-2 overflow-x-auto no-scrollbar py-1 -mx-4 px-4 sm:mx-0 sm:px-0">
          {[
            { id: 'all', label: 'All Types' },
            { id: 'pyq', label: 'Exam PYQs' },
            { id: 'video', label: 'Video Lectures' },
            { id: 'notes', label: 'Lecture Notes' },
            { id: 'textbook', label: 'Textbooks' }
          ].map((cat) => {
            const isSelected = selectedFormatFilter === cat.id;
            return (
              <button
                key={cat.id}
                onClick={() => setSelectedFormatFilter(cat.id)}
                className={`px-3.5 py-1.5 rounded-full text-xs font-semibold border transition-all active-haptic whitespace-nowrap ${
                  isSelected
                    ? 'bg-[#202938] text-white border-transparent shadow-xs'
                    : 'bg-white text-[#58605a] border-black/[0.08] hover:border-black/20'
                }`}
              >
                {cat.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* 5. Pick Up Where You Left Off */}
      <div className="flex flex-col space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="font-headline text-base text-[#131c2a] flex items-center gap-1.5 font-bold">
            <span className="material-symbols-outlined text-[#58605a] text-[20px]">history</span>
            <span>Pick up where you left off</span>
          </h3>
          <span className="font-label-md text-xs text-[#3f4dbf] font-semibold">
            {filteredResources.length} visible
          </span>
        </div>

        <div className="flex flex-col gap-3">
          {filteredResources.map((item) => (
            <div
              key={item.id}
              onClick={() => onSelectResource(item)}
              className="bg-white rounded-2xl p-3.5 shadow-sm border border-black/[0.04] flex items-start gap-3 transition-all hover:border-black/[0.1] active:scale-[0.99] cursor-pointer"
            >
              {/* Type Graphic / Thumbnail */}
              <div
                className={`w-12 h-16 rounded-xl ${item.colorClass} flex-shrink-0 flex items-center justify-center relative overflow-hidden shadow-xs`}
              >
                {item.imageUrl ? (
                  <img
                    src={item.imageUrl}
                    alt={item.title}
                    className="w-full h-full object-cover"
                    referrerPolicy="no-referrer"
                  />
                ) : (
                  <span className="material-symbols-outlined text-[24px]">{item.icon}</span>
                )}
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-1">
                  <div className="flex items-center gap-1.5">
                    <span className="font-label-sm text-[10px] px-1.5 py-0.5 rounded bg-[#F7F5F0] text-[#58605a] uppercase font-bold">
                      {item.typeBadge}
                    </span>
                    <span className="font-label-sm text-[11px] text-[#58605a] font-semibold">
                      {item.subject}
                    </span>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onToggleSave(item.id);
                    }}
                    className="p-1 text-[#58605a] hover:text-[#3f4dbf] active-haptic"
                    title="Toggle Bookmark"
                  >
                    <span
                      className={`material-symbols-outlined text-[20px] ${
                        item.saved ? 'text-[#3f4dbf] fill-icon' : 'text-gray-300'
                      }`}
                    >
                      {item.saved ? 'bookmark' : 'bookmark_border'}
                    </span>
                  </button>
                </div>

                <h4 className="font-headline text-sm font-semibold text-[#131c2a] truncate mt-0.5">
                  {item.title}
                </h4>
                <p className="font-body text-xs text-[#58605a] truncate mt-0.5">
                  {item.meta}
                </p>

                {/* Progress bar */}
                <div className="w-full bg-[#F7F5F0] h-1.5 rounded-full mt-2 overflow-hidden">
                  <div
                    className="bg-[#3f4dbf] h-full rounded-full transition-all duration-300"
                    style={{ width: `${item.progress}%` }}
                  />
                </div>

                <div className="mt-2.5 flex items-center justify-between">
                  <span className="text-[11px] font-semibold text-[#58605a]">
                    {item.progress}% complete
                  </span>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onSelectResource(item);
                    }}
                    className="inline-flex items-center gap-1 px-3 py-1 rounded-lg bg-[#F7F5F0] text-[#3f4dbf] font-label-md text-xs font-semibold hover:bg-[#3f4dbf] hover:text-white transition-all active-haptic"
                  >
                    <span>{item.type === 'video' ? 'Resume video' : 'Continue reading'}</span>
                    <span className="material-symbols-outlined text-[15px]">
                      {item.type === 'video' ? 'play_arrow' : 'menu_book'}
                    </span>
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 6. Your Subjects Carousel */}
      <div className="flex flex-col space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="font-headline text-base text-[#131c2a] flex items-center gap-1.5 font-bold">
            <span className="material-symbols-outlined text-[#58605a] text-[20px]">library_books</span>
            <span>Your subjects</span>
          </h3>
          <button
            onClick={() => onSelectSubject('ALL')}
            className="font-label-md text-xs text-[#3f4dbf] font-semibold hover:underline"
          >
            View all
          </button>
        </div>

        <div className="flex gap-3 overflow-x-auto pb-2 -mx-4 px-4 sm:mx-0 sm:px-0 no-scrollbar">
          {/* Subject 1: CS204 */}
          <div
            onClick={() => {
              onSelectSubject('CS204');
              onSelectScreen('collections');
            }}
            className="flex-shrink-0 w-64 bg-white rounded-2xl p-4 shadow-sm border border-black/[0.05] flex flex-col justify-between active-haptic cursor-pointer hover:border-[#3f4dbf]/40 transition-all"
          >
            <div>
              <div className="flex items-center justify-between">
                <span className="font-label-sm text-xs px-2 py-0.5 rounded bg-[#dfe0ff] text-[#000a64] font-bold">
                  CS204
                </span>
                <span className="material-symbols-outlined text-[#58605a] text-[18px]">more_horiz</span>
              </div>
              <h4 className="font-headline text-base text-[#131c2a] font-bold mt-2 leading-tight">
                Data Structures & Algorithms
              </h4>
              <p className="font-body text-xs text-[#58605a] mt-1">
                42 resources · 6 active topics
              </p>
            </div>
            <div className="mt-4 pt-3 flex items-center justify-between border-t border-black/[0.04]">
              <div className="flex -space-x-1.5 overflow-hidden">
                <span className="inline-block h-6 w-6 rounded-full bg-[#dfe8fd] flex items-center justify-center text-[10px] font-bold text-[#131c2a] ring-1 ring-white">
                  AVL
                </span>
                <span className="inline-block h-6 w-6 rounded-full bg-[#dae3f7] flex items-center justify-center text-[10px] font-bold text-[#131c2a] ring-1 ring-white">
                  BST
                </span>
                <span className="inline-block h-6 w-6 rounded-full bg-[#dce5dd] flex items-center justify-center text-[10px] font-bold text-[#131c2a] ring-1 ring-white">
                  +4
                </span>
              </div>
              <span className="material-symbols-outlined text-[#3f4dbf] text-[20px]">arrow_forward</span>
            </div>
          </div>

          {/* Subject 2: CS206 */}
          <div
            onClick={() => {
              onSelectSubject('CS206');
              onShowToast('Filtered to CS206 Operating Systems');
            }}
            className="flex-shrink-0 w-64 bg-white rounded-2xl p-4 shadow-sm border border-black/[0.05] flex flex-col justify-between active-haptic cursor-pointer hover:border-[#3f4dbf]/40 transition-all"
          >
            <div>
              <div className="flex items-center justify-between">
                <span className="font-label-sm text-xs px-2 py-0.5 rounded bg-[#dce5dd] text-[#151d19] font-bold">
                  CS206
                </span>
                <span className="material-symbols-outlined text-[#58605a] text-[18px]">more_horiz</span>
              </div>
              <h4 className="font-headline text-base text-[#131c2a] font-bold mt-2 leading-tight">
                Operating Systems
              </h4>
              <p className="font-body text-xs text-[#58605a] mt-1">
                31 resources · 5 active topics
              </p>
            </div>
            <div className="mt-4 pt-3 flex items-center justify-between border-t border-black/[0.04]">
              <div className="flex -space-x-1.5 overflow-hidden">
                <span className="inline-block h-6 w-6 rounded-full bg-[#dfe8fd] flex items-center justify-center text-[10px] font-bold text-[#131c2a] ring-1 ring-white">
                  TH
                </span>
                <span className="inline-block h-6 w-6 rounded-full bg-[#dae3f7] flex items-center justify-center text-[10px] font-bold text-[#131c2a] ring-1 ring-white">
                  VM
                </span>
                <span className="inline-block h-6 w-6 rounded-full bg-[#dce5dd] flex items-center justify-center text-[10px] font-bold text-[#131c2a] ring-1 ring-white">
                  +3
                </span>
              </div>
              <span className="material-symbols-outlined text-[#3f4dbf] text-[20px]">arrow_forward</span>
            </div>
          </div>

          {/* Subject 3: MA202 */}
          <div
            onClick={() => {
              onSelectSubject('MA202');
              onShowToast('Filtered to MA202 Linear Algebra');
            }}
            className="flex-shrink-0 w-64 bg-white rounded-2xl p-4 shadow-sm border border-black/[0.05] flex flex-col justify-between active-haptic cursor-pointer hover:border-[#3f4dbf]/40 transition-all"
          >
            <div>
              <div className="flex items-center justify-between">
                <span className="font-label-sm text-xs px-2 py-0.5 rounded bg-[#d6e3ff] text-[#0d1c32] font-bold">
                  MA202
                </span>
                <span className="material-symbols-outlined text-[#58605a] text-[18px]">more_horiz</span>
              </div>
              <h4 className="font-headline text-base text-[#131c2a] font-bold mt-2 leading-tight">
                Linear Algebra
              </h4>
              <p className="font-body text-xs text-[#58605a] mt-1">
                24 resources · 4 active topics
              </p>
            </div>
            <div className="mt-4 pt-3 flex items-center justify-between border-t border-black/[0.04]">
              <div className="flex -space-x-1.5 overflow-hidden">
                <span className="inline-block h-6 w-6 rounded-full bg-[#dfe8fd] flex items-center justify-center text-[10px] font-bold text-[#131c2a] ring-1 ring-white">
                  EIG
                </span>
                <span className="inline-block h-6 w-6 rounded-full bg-[#dae3f7] flex items-center justify-center text-[10px] font-bold text-[#131c2a] ring-1 ring-white">
                  SVD
                </span>
                <span className="inline-block h-6 w-6 rounded-full bg-[#dce5dd] flex items-center justify-center text-[10px] font-bold text-[#131c2a] ring-1 ring-white">
                  +2
                </span>
              </div>
              <span className="material-symbols-outlined text-[#3f4dbf] text-[20px]">arrow_forward</span>
            </div>
          </div>
        </div>
      </div>

      {/* 7. Quick Access Archive & Recently Saved */}
      <div className="flex flex-col space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="font-headline text-base text-[#131c2a] flex items-center gap-1.5 font-bold">
            <span className="material-symbols-outlined text-[#58605a] text-[20px]">bookmark</span>
            <span>Quick Access Archive</span>
          </h3>
          <button
            onClick={() => onSelectScreen('saved')}
            className="font-label-md text-xs text-[#3f4dbf] font-semibold hover:underline"
          >
            {savedResources.length} saved to vault
          </button>
        </div>

        <div className="bg-white rounded-2xl p-2.5 shadow-sm border border-black/[0.04] flex flex-col gap-1">
          {savedResources.slice(0, 3).map((item) => (
            <div
              key={item.id}
              onClick={() => onSelectResource(item)}
              className="flex items-center justify-between p-2 rounded-xl hover:bg-[#F7F5F0] transition-colors cursor-pointer active-haptic"
            >
              <div className="flex items-center gap-3 min-w-0">
                <div className="w-10 h-10 rounded-xl bg-[#F0F3FF] flex items-center justify-center text-[#3f4dbf] flex-shrink-0">
                  <span className="material-symbols-outlined text-[20px]">{item.icon}</span>
                </div>
                <div className="min-w-0">
                  <h5 className="font-headline text-xs sm:text-sm font-semibold text-[#131c2a] truncate">
                    {item.title}
                  </h5>
                  <p className="font-body text-[11px] text-[#58605a] truncate">
                    {item.subject} · {item.author}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-1">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onToggleSave(item.id);
                  }}
                  className="p-1.5 text-[#58605a] hover:text-[#3f4dbf] active-haptic"
                >
                  <span className="material-symbols-outlined text-[18px] text-[#3f4dbf] fill-icon">
                    bookmark
                  </span>
                </button>
                <span className="material-symbols-outlined text-gray-400 text-[20px] flex-shrink-0">
                  chevron_right
                </span>
              </div>
            </div>
          ))}
        </div>

        {/* Practice PYQ Promo Card with Embedded Workspace Visual */}
        <div className="relative overflow-hidden rounded-2xl bg-white p-4 shadow-sm border border-black/[0.05] mt-2 flex flex-col gap-3">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-[#3f4dbf] text-[22px]">quiz</span>
            <span className="font-label-md text-xs text-[#3f4dbf] font-bold uppercase tracking-wider">
              Exam Readiness
            </span>
          </div>

          <div>
            <h4 className="font-headline text-base font-bold text-[#131c2a]">
              Practice previous-year questions
            </h4>
            <p className="font-body text-xs text-[#58605a] mt-1 leading-relaxed">
              Simulate timed semester test patterns with detailed step-by-step solutions and peer benchmarks.
            </p>
          </div>

          {/* Embedded Image Graphic */}
          <div
            onClick={onOpenDrill}
            className="w-full h-36 rounded-xl overflow-hidden shadow-xs relative mt-1 group cursor-pointer"
          >
            <img
              src="https://lh3.googleusercontent.com/aida-public/AB6AXuBll6nrCz0mrYVkun1fIxqxJzoViKbJGH0s8DY2kVcI7LXoYfBE2QfQrkACGlIuXZHmOKnwQ93Pgyotjly43fq1PU5_CSb85lQVrNUHQgWiqpOANE1g2uxHBNn_U1wvgsLj8elBKWhCVyAzIVK0sZ6D6HRW1U3RJ3yxQ72YAdkP3CgMFEMX1CjwpnV1f4RtkK5FHjDVv7BAVCynCDN4fN6eNCyNaxj6YYQvZ1bPhDXh-GdULmQxlpYj6c_iZql4kPA7"
              alt="Curated CS204 Archive"
              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
              referrerPolicy="no-referrer"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-transparent to-transparent flex items-end p-2.5">
              <span className="font-label-sm text-xs text-white font-medium flex items-center gap-1">
                <span className="material-symbols-outlined text-[14px]">visibility</span>
                <span>Curated CS204 Archive</span>
              </span>
            </div>
          </div>

          <button
            onClick={onOpenDrill}
            className="w-full py-2.5 px-4 rounded-xl bg-[#3f4dbf] text-white font-label-lg text-xs sm:text-sm font-bold flex items-center justify-center gap-2 shadow-sm active-haptic hover:brightness-105 transition-all"
          >
            <span>Start PYQ Drill</span>
            <span className="material-symbols-outlined text-[18px]">arrow_forward</span>
          </button>
        </div>
      </div>
    </div>
  );
};
