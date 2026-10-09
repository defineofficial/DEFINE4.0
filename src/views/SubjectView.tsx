import React, { useState } from 'react';
import { Resource, ScreenType } from '../types';
import { TOPICS_CS204 } from '../data/mockData';

interface SubjectViewProps {
  resources: Resource[];
  onSelectResource: (res: Resource) => void;
  onToggleSave: (id: string) => void;
  onOpenReader: () => void;
  onOpenAddModal: () => void;
  onSelectScreen: (screen: ScreenType) => void;
  onShowToast: (msg: string) => void;
}

export const SubjectView: React.FC<SubjectViewProps> = ({
  resources,
  onSelectResource,
  onToggleSave,
  onOpenReader,
  onOpenAddModal,
  onSelectScreen,
  onShowToast
}) => {
  const [activeTab, setActiveTab] = useState<'topics' | 'all' | 'collections' | 'pyqs'>('topics');
  const [activeTopic, setActiveTopic] = useState('graphs');

  // Filter resources based on active topic or tab
  const topicFilteredResources = resources.filter((r) => {
    if (activeTab === 'pyqs') return r.type === 'pyq';
    if (activeTab === 'collections') return r.saved;
    if (activeTopic === 'all') return true;
    if (activeTopic === 'graphs') return r.topic === 'Graphs';
    return true;
  });

  return (
    <div className="flex flex-col w-full pb-8 space-y-4 animate-fadeIn">
      {/* 1. Subject Header */}
      <section className="flex flex-col gap-2 pt-1">
        <div className="flex items-start justify-between gap-2">
          <div className="flex flex-col min-w-0">
            <div className="flex items-center gap-1.5 mb-1">
              <span className="inline-flex items-center px-2 py-0.5 rounded-full bg-[#dce5dd] text-[#151d19] font-label-sm text-[11px] font-bold">
                CS204
              </span>
              <span className="font-label-sm text-xs text-[#58605a]">Semester 4</span>
            </div>
            <h1 className="font-headline text-2xl sm:text-3xl text-[#131c2a] tracking-tight font-bold">
              Data Structures & Algorithms
            </h1>
            <p className="font-body text-xs text-[#58605a] mt-0.5">
              42 resources organised into 6 core topics
            </p>
          </div>

          <button
            aria-label="Add to subject"
            onClick={onOpenAddModal}
            className="flex items-center justify-center w-11 h-11 rounded-xl bg-[#5967d9] text-white shadow-sm hover:brightness-105 active:scale-95 transition-all flex-shrink-0"
            title="Add to subject"
          >
            <span className="material-symbols-outlined text-[22px]">add</span>
          </button>
        </div>

        {/* Action Button Row */}
        <div className="flex items-center gap-1.5 mt-1">
          <button
            onClick={onOpenAddModal}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white text-[#131c2a] shadow-xs active:bg-gray-100 transition-colors border border-black/[0.04]"
          >
            <span className="material-symbols-outlined text-[16px] text-[#3f4dbf]">add_circle</span>
            <span className="font-label-md text-xs font-semibold">Add to subject</span>
          </button>
          <button
            onClick={() => onShowToast('Subject vault link copied to clipboard!')}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white text-[#58605a] shadow-xs active:bg-gray-100 transition-colors border border-black/[0.04]"
          >
            <span className="material-symbols-outlined text-[16px]">share</span>
            <span className="font-label-md text-xs font-semibold">Share</span>
          </button>
          <button
            onClick={() => onShowToast('Subject syllabus and mark distribution verified.')}
            className="flex items-center justify-center w-8 h-8 rounded-lg bg-white text-[#58605a] shadow-xs ml-auto active:bg-gray-100 border border-black/[0.04]"
          >
            <span className="material-symbols-outlined text-[18px]">more_horiz</span>
          </button>
        </div>
      </section>

      {/* 2. Horizontal Scrollable Navigation Tabs */}
      <div className="w-full overflow-x-auto py-1 -mx-4 px-4 sm:mx-0 sm:px-0 no-scrollbar">
        <div className="flex items-center gap-2 min-w-max pb-1">
          <button
            onClick={() => setActiveTab('topics')}
            className={`px-4 py-1.5 rounded-full font-label-md text-xs font-semibold transition-all shadow-xs ${
              activeTab === 'topics'
                ? 'bg-[#3f4dbf] text-white'
                : 'bg-white text-[#58605a] active:bg-gray-100'
            }`}
          >
            Topics
          </button>
          <button
            onClick={() => setActiveTab('all')}
            className={`px-4 py-1.5 rounded-full font-label-md text-xs font-semibold transition-all shadow-xs ${
              activeTab === 'all'
                ? 'bg-[#3f4dbf] text-white'
                : 'bg-white text-[#58605a] active:bg-gray-100'
            }`}
          >
            All resources
          </button>
          <button
            onClick={() => setActiveTab('collections')}
            className={`px-4 py-1.5 rounded-full font-label-md text-xs font-semibold transition-all shadow-xs ${
              activeTab === 'collections'
                ? 'bg-[#3f4dbf] text-white'
                : 'bg-white text-[#58605a] active:bg-gray-100'
            }`}
          >
            Collections
          </button>
          <button
            onClick={() => setActiveTab('pyqs')}
            className={`px-4 py-1.5 rounded-full font-label-md text-xs font-semibold transition-all shadow-xs ${
              activeTab === 'pyqs'
                ? 'bg-[#3f4dbf] text-white'
                : 'bg-white text-[#58605a] active:bg-gray-100'
            }`}
          >
            PYQs
          </button>
        </div>
      </div>

      {/* 3. Topics Selector Pills (Interactive Scroll) */}
      <div className="w-full overflow-x-auto py-1 -mx-4 px-4 sm:mx-0 sm:px-0 no-scrollbar">
        <div className="flex items-center gap-2 min-w-max">
          {TOPICS_CS204.filter(t => t.id !== 'all').map((topic) => {
            const isSelected = activeTopic === topic.id;
            return (
              <button
                key={topic.id}
                onClick={() => {
                  setActiveTopic(topic.id);
                  onShowToast(`Filtered topic: ${topic.name}`);
                }}
                className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-full font-label-sm text-xs font-semibold transition-colors shadow-xs ${
                  isSelected
                    ? 'bg-[#5967d9] text-white'
                    : 'bg-white text-[#58605a] hover:text-[#131c2a]'
                }`}
              >
                {isSelected && <span className="w-1.5 h-1.5 rounded-full bg-white" />}
                <span>{topic.name}</span>
                <span
                  className={`px-1.5 py-0.2 rounded-full text-[10px] ${
                    isSelected ? 'bg-white/20 text-white' : 'bg-[#e7eeff] text-[#454653]'
                  }`}
                >
                  {topic.count}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* 4. Editorial Next Step Recommendation Card */}
      <section className="mt-2">
        <div className="relative overflow-hidden rounded-2xl bg-white p-4 shadow-sm border border-black/[0.04]">
          <div className="absolute -right-6 -bottom-6 w-24 h-24 rounded-full bg-[#dfe0ff]/30 pointer-events-none" />
          <div className="flex items-start gap-3">
            <div className="w-9 h-9 rounded-lg bg-[#f0f3ff] flex items-center justify-center text-[#3f4dbf] flex-shrink-0">
              <span className="material-symbols-outlined text-[20px] fill-icon">auto_awesome</span>
            </div>
            <div className="flex flex-col flex-1 min-w-0">
              <span className="font-label-sm text-[11px] text-[#3f4dbf] font-bold uppercase tracking-wider mb-0.5">
                A Good Next Step
              </span>
              <p className="font-body text-xs sm:text-sm text-[#131c2a] leading-snug">
                You left off at <span className="font-semibold text-[#3f4dbf]">page 4</span> of the 2025 graph questions.
              </p>
              <button
                onClick={onOpenReader}
                className="inline-flex items-center gap-1 mt-2 text-xs text-[#3f4dbf] font-bold hover:underline self-start group"
              >
                <span>Resume question paper</span>
                <span className="material-symbols-outlined text-[16px] group-hover:translate-x-0.5 transition-transform">
                  arrow_forward
                </span>
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* 5. Pinned Collection Callout Banner & Exam Progress Bento */}
      <section className="flex flex-col gap-3">
        {/* Pinned DSA Exam Prep Banner */}
        <div className="rounded-2xl bg-[#dfe8fd] p-4 shadow-sm flex items-center justify-between gap-3">
          <div className="flex items-center gap-3 min-w-0">
            <div className="w-12 h-12 rounded-xl bg-white flex items-center justify-center text-[#3f4dbf] shadow-xs flex-shrink-0">
              <span className="material-symbols-outlined text-[24px]">bookmark_star</span>
            </div>
            <div className="flex flex-col min-w-0">
              <span className="font-label-sm text-[11px] uppercase tracking-wider text-[#58605a] font-semibold">
                Pinned Collection
              </span>
              <h2 className="font-headline text-base font-bold text-[#131c2a] truncate">
                DSA Exam Prep
              </h2>
              <span className="font-body text-xs text-[#58605a] truncate">
                12 resources curated
              </span>
            </div>
          </div>
          <div className="flex flex-col items-end flex-shrink-0">
            <span className="px-2.5 py-1 rounded-full bg-[#ffdad6] text-[#ba1a1a] font-label-sm text-xs font-bold flex items-center gap-1 font-mono">
              <span className="material-symbols-outlined text-[14px]">timer</span>
              <span>9 days left</span>
            </span>
          </div>
        </div>

        {/* Exam Progress Indicator Card */}
        <div className="rounded-2xl bg-white p-4 shadow-sm border border-black/[0.04] flex flex-col gap-2.5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-[#58605a] text-[18px]">verified</span>
              <span className="font-headline text-xs sm:text-sm text-[#131c2a] font-bold">
                Subject Mastery
              </span>
            </div>
            <span className="font-label-md text-xs text-[#3f4dbf] font-bold font-mono">
              68% Complete
            </span>
          </div>
          {/* Progress Bar Track */}
          <div className="w-full h-2 rounded-full bg-[#e7eeff] overflow-hidden">
            <div className="h-full bg-[#5967d9] rounded-full" style={{ width: '68%' }} />
          </div>
          <div className="flex items-center justify-between font-label-sm text-xs text-[#58605a]">
            <span>29 of 42 resources completed</span>
            <span className="text-[#131c2a] font-semibold">13 remaining</span>
          </div>
        </div>
      </section>

      {/* 6. Active Topic Section: Graphs */}
      <section className="flex flex-col gap-3">
        {/* Section Heading */}
        <div className="flex items-center justify-between">
          <div className="flex items-baseline gap-2">
            <h2 className="font-headline text-lg sm:text-xl font-bold text-[#131c2a]">Graphs</h2>
            <span className="font-body text-xs text-[#58605a]">· {topicFilteredResources.length} resources</span>
          </div>
          <button
            onClick={() => onShowToast('Filter options active for Graph structures')}
            className="flex items-center gap-1 text-[#58605a] text-xs font-semibold hover:text-[#131c2a]"
          >
            <span className="material-symbols-outlined text-[16px]">tune</span>
            <span>Filter</span>
          </button>
        </div>

        {/* Companion Reference Visual Thumbnail (Desktop Match Feature) */}
        <div className="relative rounded-2xl overflow-hidden shadow-xs bg-[#f0f3ff] border border-black/[0.04]">
          <div className="flex items-center p-3 gap-3">
            <div className="relative w-16 h-20 rounded-xl overflow-hidden flex-shrink-0 shadow-xs bg-[#d1daee]">
              <img
                src="https://lh3.googleusercontent.com/aida-public/AB6AXuBll6nrCz0mrYVkun1fIxqxJzoViKbJGH0s8DY2kVcI7LXoYfBE2QfQrkACGlIuXZHmOKnwQ93Pgyotjly43fq1PU5_CSb85lQVrNUHQgWiqpOANE1g2uxHBNn_U1wvgsLj8elBKWhCVyAzIVK0sZ6D6HRW1U3RJ3yxQ72YAdkP3CgMFEMX1CjwpnV1f4RtkK5FHjDVv7BAVCynCDN4fN6eNCyNaxj6YYQvZ1bPhDXh-GdULmQxlpYj6c_iZql4kPA7"
                alt="DSA Graphs workspace reference"
                className="w-full h-full object-cover"
                referrerPolicy="no-referrer"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent" />
            </div>
            <div className="flex flex-col flex-1 min-w-0">
              <span className="font-label-sm text-[10px] text-[#3f4dbf] font-bold uppercase tracking-wider">
                Companion Vault
              </span>
              <h3 className="font-headline text-sm sm:text-base font-bold text-[#131c2a] truncate">
                Algorithms Visual Atlas
              </h3>
              <p className="font-body text-xs text-[#58605a] line-clamp-1">
                Desktop synchronised graph diagrams & traversal traces.
              </p>
            </div>
            <button
              onClick={onOpenReader}
              className="w-9 h-9 rounded-full bg-white text-[#3f4dbf] shadow-xs flex items-center justify-center flex-shrink-0 hover:scale-105 transition-transform"
              title="Open Visual Atlas"
            >
              <span className="material-symbols-outlined text-[18px]">open_in_new</span>
            </button>
          </div>
        </div>

        {/* Resource Items List */}
        <div className="flex flex-col gap-2.5">
          {topicFilteredResources.map((item) => (
            <div
              key={item.id}
              onClick={() => {
                if (item.type === 'pyq') {
                  onOpenReader();
                } else {
                  onSelectResource(item);
                }
              }}
              className="flex items-center justify-between p-3.5 rounded-2xl bg-white shadow-xs border border-black/[0.04] active:bg-[#f0f3ff] transition-colors cursor-pointer"
            >
              <div className="flex items-center gap-3 min-w-0">
                <div
                  className={`w-10 h-10 rounded-xl ${item.colorClass} flex items-center justify-center flex-shrink-0`}
                >
                  <span className="material-symbols-outlined text-[20px]">{item.icon}</span>
                </div>
                <div className="flex flex-col min-w-0">
                  <div className="flex items-center gap-1.5 mb-0.5">
                    <span className="px-1.5 py-0.2 rounded bg-[#e7eeff] text-[#454653] font-label-sm text-[10px] font-bold">
                      {item.typeBadge}
                    </span>
                    <span className="font-label-sm text-xs text-[#58605a] truncate">
                      {item.meta.split('·')[0]}
                    </span>
                  </div>
                  <h4 className="font-headline text-xs sm:text-sm font-semibold text-[#131c2a] truncate">
                    {item.title}
                  </h4>
                </div>
              </div>

              <div className="flex items-center gap-2 flex-shrink-0 ml-2">
                {item.saved ? (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onToggleSave(item.id);
                    }}
                    className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-[#dce5dd] text-[#151d19] font-label-sm text-xs font-semibold active-haptic"
                  >
                    <span className="material-symbols-outlined text-[14px] fill-icon text-[#3f4dbf]">
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
                    className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-[#e7eeff] text-[#131c2a] font-label-sm text-xs font-semibold hover:bg-[#dce5dd] active-haptic transition-colors"
                  >
                    <span className="material-symbols-outlined text-[14px]">bookmark_border</span>
                    <span>+ Save</span>
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* 7. Tactile Add Quick Button Footer Bar */}
      <div className="mt-4 flex items-center justify-between p-4 rounded-2xl bg-[#f0f3ff] shadow-xs border border-black/[0.04]">
        <div className="flex items-center gap-2">
          <span className="material-symbols-outlined text-[#3f4dbf] text-[20px]">library_add</span>
          <span className="font-label-md text-xs sm:text-sm font-semibold text-[#131c2a]">
            Add notes, PDFs or code files
          </span>
        </div>
        <button
          onClick={onOpenAddModal}
          className="px-3.5 py-1.5 rounded-xl bg-[#3f4dbf] text-white font-label-md text-xs font-bold shadow-xs active:scale-95 transition-all hover:bg-[#5967d9]"
        >
          Upload
        </button>
      </div>
    </div>
  );
};
