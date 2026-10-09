import React, { useState } from 'react';

interface DocumentReaderViewProps {
  onBack: () => void;
  onOpenTestModal: () => void;
  onShowToast: (msg: string) => void;
}

export const DocumentReaderView: React.FC<DocumentReaderViewProps> = ({
  onBack,
  onOpenTestModal,
  onShowToast
}) => {
  const [currentPage, setCurrentPage] = useState(4);
  const totalPages = 12;
  const [isBookmarked, setIsBookmarked] = useState(true);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [userNote, setUserNote] = useState(
    'BFS = shortest path only when edges have equal weight. Revise O(V+E) time analysis.'
  );
  const [isEditingNote, setIsEditingNote] = useState(false);
  const [activeNodeHighlight, setActiveNodeHighlight] = useState<string | null>('A');

  const handlePrevPage = () => {
    if (currentPage > 1) {
      setCurrentPage((prev) => prev - 1);
      onShowToast(`Navigated to Page ${currentPage - 1}`);
    }
  };

  const handleNextPage = () => {
    if (currentPage < totalPages) {
      setCurrentPage((prev) => prev + 1);
      onShowToast(`Navigated to Page ${currentPage + 1}`);
    }
  };

  const toggleBookmark = () => {
    setIsBookmarked(!isBookmarked);
    onShowToast(isBookmarked ? 'Removed exam paper from Saved' : 'Bookmarked CS204 May 2025 Paper in Saved');
  };

  return (
    <div className="flex flex-col w-full pb-8 space-y-4 animate-fadeIn">
      {/* Top Navigation & Status Sub-Bar */}
      <div className="w-full flex items-center justify-between gap-2 py-2 bg-white rounded-2xl px-3 shadow-xs border border-black/[0.04]">
        <div className="flex items-center gap-1.5">
          <button
            onClick={onBack}
            className="w-9 h-9 flex items-center justify-center rounded-xl bg-[#F7F5F0] hover:bg-gray-200 text-[#131c2a] transition-all active-haptic"
            title="Go back"
          >
            <span className="material-symbols-outlined text-[20px]">arrow_back</span>
          </button>

          <button
            onClick={handlePrevPage}
            disabled={currentPage <= 1}
            className="w-9 h-9 flex items-center justify-center rounded-xl bg-[#F7F5F0] hover:bg-gray-200 text-[#131c2a] transition-all active-haptic disabled:opacity-40"
            title="Previous page"
          >
            <span className="material-symbols-outlined text-[20px]">chevron_left</span>
          </button>

          <div className="flex items-center px-2.5 py-1 bg-[#F7F5F0] rounded-lg">
            <span className="font-label-md text-xs font-semibold text-[#131c2a] font-mono">
              Page {currentPage} of {totalPages}
            </span>
          </div>

          <button
            onClick={handleNextPage}
            disabled={currentPage >= totalPages}
            className="w-9 h-9 flex items-center justify-center rounded-xl bg-[#F7F5F0] hover:bg-gray-200 text-[#131c2a] transition-all active-haptic disabled:opacity-40"
            title="Next page"
          >
            <span className="material-symbols-outlined text-[20px]">chevron_right</span>
          </button>
        </div>

        <div className="flex items-center gap-1.5">
          <span className="font-label-sm text-[11px] bg-[#F7F5F0] px-2 py-1 rounded-md text-[#58605a] font-mono font-semibold">
            100%
          </span>

          <button
            onClick={() => onShowToast('Exam paper link copied to clipboard!')}
            className="w-9 h-9 flex items-center justify-center rounded-xl bg-[#F7F5F0] text-[#58605a] hover:text-[#131c2a] shadow-xs transition-all active-haptic"
            title="Share Question Paper"
          >
            <span className="material-symbols-outlined text-[18px]">share</span>
          </button>

          <button
            onClick={toggleBookmark}
            className={`flex items-center gap-1 px-2.5 h-9 rounded-xl transition-all active-haptic shadow-xs ${
              isBookmarked
                ? 'bg-[#3f4dbf] text-white'
                : 'bg-[#F7F5F0] text-[#58605a] hover:text-[#131c2a]'
            }`}
          >
            <span className="material-symbols-outlined text-[18px] fill-icon">
              {isBookmarked ? 'bookmark' : 'bookmark_border'}
            </span>
            <span className="font-label-sm text-xs font-semibold hidden sm:inline">
              {isBookmarked ? 'Saved' : 'Save'}
            </span>
          </button>
        </div>
      </div>

      {/* Document Viewer Canvas: Examination Paper Texture */}
      <article className="relative w-full bg-white rounded-3xl p-4 sm:p-6 shadow-md overflow-hidden border border-black/[0.04]">
        {/* Subtle Spine Illusion */}
        <div className="absolute left-0 top-0 bottom-0 w-2.5 bg-gradient-to-r from-black/10 via-black/5 to-transparent pointer-events-none" />
        <div className="absolute top-0 right-0 w-32 h-32 bg-[#3f4dbf]/5 rounded-bl-full pointer-events-none" />

        {/* Exam Paper Header */}
        <header className="mb-5 pb-3 bg-[#f0f3ff] p-4 rounded-2xl">
          <div className="flex flex-wrap items-center justify-between gap-1 mb-1">
            <span className="font-label-sm text-[11px] tracking-wider uppercase text-[#58605a] font-semibold">
              University Examinations · May 2025
            </span>
            <span className="font-label-sm text-xs px-2 py-0.5 rounded bg-[#5967d9] text-white font-bold">
              Total: 30 Marks
            </span>
          </div>
          <h2 className="font-headline text-lg sm:text-xl font-bold text-[#131c2a]">
            Data Structures & Algorithms · CS204
          </h2>
          <p className="font-label-md text-xs text-[#3f4dbf] font-semibold mt-0.5">
            Section B: Graph Theory & Graph Traversal Algorithms
          </p>
        </header>

        {/* Question 7 Container */}
        <section className="space-y-4">
          <div className="flex items-start justify-between gap-2">
            <div className="flex items-center gap-2">
              <span className="w-7 h-7 flex items-center justify-center rounded-full bg-[#131c2a] text-white font-headline text-xs font-bold">
                7
              </span>
              <h3 className="font-headline text-base sm:text-lg font-bold text-[#131c2a]">
                Breadth-First and Depth-First Traversal
              </h3>
            </div>
            <span className="font-label-md text-xs bg-[#e7eeff] text-[#454653] px-2.5 py-1 rounded-md font-bold">
              [10 Marks]
            </span>
          </div>

          <p className="font-body text-xs sm:text-sm text-[#131c2a] leading-relaxed">
            Consider the undirected, unweighted graph <span className="font-semibold italic">G = (V, E)</span> illustrated below. Starting at vertex <span className="font-bold text-[#3f4dbf]">A</span>, perform a breadth-first search (BFS). Assume that whenever a choice exists between adjacent vertices, the algorithm explores them in strictly <span className="underline decoration-[#3f4dbf] font-semibold">alphabetical order</span>.
          </p>

          {/* Interactive SVG Graph Canvas */}
          <div className="w-full bg-[#F7F5F0] rounded-2xl p-4 flex flex-col items-center justify-center shadow-inner relative overflow-hidden">
            <div className="w-full flex items-center justify-between mb-1">
              <span className="font-label-sm text-[10px] text-[#58605a] uppercase tracking-widest font-bold">
                Figure 7.1: Graph Schema (Interactive)
              </span>
              <span className="text-[10px] text-[#3f4dbf] font-semibold">
                Active node: {activeNodeHighlight}
              </span>
            </div>

            <div className="w-full max-w-[340px] aspect-[4/3] relative flex items-center justify-center py-2">
              <svg
                aria-label="Undirected graph diagram with nodes A, B, C, D, E, and F"
                className="w-full h-full text-[#131c2a] drop-shadow-sm select-none"
                viewBox="0 0 340 240"
              >
                {/* Graph Edges */}
                <line x1="60" y1="120" x2="140" y2="50" stroke="#767685" strokeWidth="2.5" strokeLinecap="round" />
                <line x1="60" y1="120" x2="140" y2="190" stroke="#767685" strokeWidth="2.5" strokeLinecap="round" />
                <line x1="140" y1="50" x2="210" y2="50" stroke="#767685" strokeWidth="2.5" strokeLinecap="round" />
                <line x1="140" y1="50" x2="140" y2="190" stroke="#767685" strokeWidth="2.5" strokeLinecap="round" />
                <line x1="140" y1="190" x2="210" y2="190" stroke="#767685" strokeWidth="2.5" strokeLinecap="round" />
                <line x1="210" y1="50" x2="280" y2="120" stroke="#767685" strokeWidth="2.5" strokeLinecap="round" />
                <line x1="210" y1="190" x2="280" y2="120" stroke="#767685" strokeWidth="2.5" strokeLinecap="round" />
                {/* Discarded back/cross edge (B, E) */}
                <line x1="140" y1="50" x2="210" y2="190" stroke="#ba1a1a" strokeWidth="2" strokeDasharray="4 3" />

                {/* Node A (Start Node) */}
                <g className="cursor-pointer" onClick={() => setActiveNodeHighlight('A')}>
                  <circle cx="60" cy="120" r="26" fill="none" stroke="#5967d9" strokeWidth="2" strokeDasharray="3 3" />
                  <circle cx="60" cy="120" r="22" fill="#3f4dbf" />
                  <text x="60" y="126" textAnchor="middle" fill="#ffffff" fontFamily="Outfit" fontSize="16" fontWeight="700">A</text>
                  <text x="60" y="80" textAnchor="middle" fill="#3f4dbf" fontFamily="Plus Jakarta Sans" fontSize="11" fontWeight="700">START</text>
                </g>

                {/* Node B */}
                <g className="cursor-pointer" onClick={() => setActiveNodeHighlight('B')}>
                  <circle cx="140" cy="50" r="20" fill={activeNodeHighlight === 'B' ? '#5967d9' : '#131c2a'} />
                  <text x="140" y="56" textAnchor="middle" fill="#ffffff" fontFamily="Outfit" fontSize="16" fontWeight="700">B</text>
                </g>

                {/* Node C */}
                <g className="cursor-pointer" onClick={() => setActiveNodeHighlight('C')}>
                  <circle cx="140" cy="190" r="20" fill={activeNodeHighlight === 'C' ? '#5967d9' : '#131c2a'} />
                  <text x="140" y="196" textAnchor="middle" fill="#ffffff" fontFamily="Outfit" fontSize="16" fontWeight="700">C</text>
                </g>

                {/* Node D */}
                <g className="cursor-pointer" onClick={() => setActiveNodeHighlight('D')}>
                  <circle cx="210" cy="50" r="20" fill={activeNodeHighlight === 'D' ? '#5967d9' : '#131c2a'} />
                  <text x="210" y="56" textAnchor="middle" fill="#ffffff" fontFamily="Outfit" fontSize="16" fontWeight="700">D</text>
                </g>

                {/* Node E */}
                <g className="cursor-pointer" onClick={() => setActiveNodeHighlight('E')}>
                  <circle cx="210" cy="190" r="20" fill={activeNodeHighlight === 'E' ? '#5967d9' : '#131c2a'} />
                  <text x="210" y="196" textAnchor="middle" fill="#ffffff" fontFamily="Outfit" fontSize="16" fontWeight="700">E</text>
                </g>

                {/* Node F */}
                <g className="cursor-pointer" onClick={() => setActiveNodeHighlight('F')}>
                  <circle cx="280" cy="120" r="20" fill={activeNodeHighlight === 'F' ? '#5967d9' : '#131c2a'} />
                  <text x="280" y="126" textAnchor="middle" fill="#ffffff" fontFamily="Outfit" fontSize="16" fontWeight="700">F</text>
                </g>
              </svg>
            </div>

            <div className="flex items-center gap-3 mt-1 text-[11px] text-[#58605a]">
              <span className="flex items-center gap-1">
                <span className="w-2.5 h-2.5 rounded-full bg-[#3f4dbf]" />
                <span>A is root origin</span>
              </span>
              <span>•</span>
              <span className="flex items-center gap-1">
                <span className="w-4 h-0.5 bg-[#767685]" />
                <span>Bidirectional edges</span>
              </span>
              <span>•</span>
              <span className="flex items-center gap-1 text-[#ba1a1a]">
                <span className="w-4 h-0.5 bg-[#ba1a1a] border-dashed" />
                <span>(B, E) cross edge</span>
              </span>
            </div>
          </div>

          {/* Subquestions List */}
          <div className="space-y-2 pt-1">
            <div className="p-3 bg-[#e7eeff] rounded-xl flex items-start justify-between gap-3">
              <div className="flex-1">
                <span className="font-bold text-xs text-[#131c2a]">(a)</span>
                <span className="text-xs text-[#131c2a] ml-1.5 leading-relaxed">
                  Write down the explicit vertex discovery sequence yielded by the BFS search. Specify the state of the FIFO queue after vertex C is processed.
                </span>
              </div>
              <span className="text-[11px] px-2 py-0.5 bg-white text-[#3f4dbf] font-bold rounded shadow-xs font-mono">
                [4]
              </span>
            </div>

            <div className="p-3 bg-[#e7eeff] rounded-xl flex items-start justify-between gap-3">
              <div className="flex-1">
                <span className="font-bold text-xs text-[#131c2a]">(b)</span>
                <span className="text-xs text-[#131c2a] ml-1.5 leading-relaxed">
                  Construct the resulting BFS spanning tree. Identify all cross edges or back edges discarded during traversal.
                </span>
              </div>
              <span className="text-[11px] px-2 py-0.5 bg-white text-[#3f4dbf] font-bold rounded shadow-xs font-mono">
                [3]
              </span>
            </div>

            <div className="p-3 bg-[#e7eeff] rounded-xl flex items-start justify-between gap-3">
              <div className="flex-1">
                <span className="font-bold text-xs text-[#131c2a]">(c)</span>
                <span className="text-xs text-[#131c2a] ml-1.5 leading-relaxed">
                  Suppose edge (B, E) is assigned a negative weight -3. Explain concisely why BFS can no longer guarantee shortest-path validity.
                </span>
              </div>
              <span className="text-[11px] px-2 py-0.5 bg-white text-[#3f4dbf] font-bold rounded shadow-xs font-mono">
                [3]
              </span>
            </div>
          </div>

          {/* Question 8 Highlight Box */}
          <div className="mt-5 bg-[#dfe8fd] rounded-2xl p-4 shadow-xs relative overflow-hidden">
            <div className="flex items-start justify-between gap-2 mb-1.5">
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 flex items-center justify-center rounded-full bg-[#58605a] text-white font-headline text-xs font-bold">
                  8
                </span>
                <h4 className="font-headline text-sm font-bold text-[#131c2a]">
                  Comparing Traversal Algorithms
                </h4>
              </div>
              <span className="text-xs bg-white text-[#58605a] px-2.5 py-0.5 rounded font-bold font-mono">
                [8 Marks]
              </span>
            </div>
            <p className="font-body text-xs text-[#131c2a] leading-relaxed">
              Provide an asymptotic complexity comparison between BFS (using an adjacency list) versus DFS (using an adjacency matrix) in terms of vertex set |V| and edge set |E|.
            </p>
          </div>

          {/* Document Reference Card with Supplied Asset */}
          <div className="w-full bg-[#f0f3ff] p-3 rounded-2xl flex items-center gap-3 shadow-xs mt-3">
            <div className="w-16 h-20 rounded-xl overflow-hidden flex-shrink-0 bg-[#dfe8fd] relative">
              <img
                src="https://lh3.googleusercontent.com/aida-public/AB6AXuBll6nrCz0mrYVkun1fIxqxJzoViKbJGH0s8DY2kVcI7LXoYfBE2QfQrkACGlIuXZHmOKnwQ93Pgyotjly43fq1PU5_CSb85lQVrNUHQgWiqpOANE1g2uxHBNn_U1wvgsLj8elBKWhCVyAzIVK0sZ6D6HRW1U3RJ3yxQ72YAdkP3CgMFEMX1CjwpnV1f4RtkK5FHjDVv7BAVCynCDN4fN6eNCyNaxj6YYQvZ1bPhDXh-GdULmQxlpYj6c_iZql4kPA7"
                alt="DSA 2025 Textbook and graph question notes reference cover"
                className="w-full h-full object-cover"
                referrerPolicy="no-referrer"
              />
              <div className="absolute inset-0 bg-[#3f4dbf]/10 mix-blend-multiply" />
            </div>
            <div className="flex-1 min-w-0">
              <span className="text-[10px] text-[#3f4dbf] uppercase font-bold tracking-wider">
                Source Material
              </span>
              <h5 className="font-headline text-sm text-[#131c2a] font-bold truncate">
                Algorithms & Graphs 2025 Ed.
              </h5>
              <p className="font-body text-xs text-[#58605a] truncate mt-0.5">
                Referenced in CS204 Lecture Notes Series
              </p>
            </div>
            <button
              onClick={() => onShowToast('Navigating to Chapter 22 Elementary Graphs...')}
              className="w-9 h-9 rounded-full bg-white flex items-center justify-center text-[#3f4dbf] shadow-xs hover:scale-105 transition-transform"
              title="Open Source Notes"
            >
              <span className="material-symbols-outlined text-[20px]">menu_book</span>
            </button>
          </div>
        </section>

        {/* Interactive Reader Highlight & Notes Banner */}
        <div className="mt-5 p-4 bg-[#F7F5F0] rounded-2xl shadow-xs border border-black/[0.04]">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-[#3f4dbf] text-[20px]">ink_highlighter</span>
              <span className="font-headline text-xs font-bold text-[#131c2a]">
                My Personal Notes (1 highlight)
              </span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="text-[10px] text-[#58605a] bg-white px-2 py-0.5 rounded-full">
                Just now
              </span>
              <button
                onClick={() => setIsEditingNote(!isEditingNote)}
                className="text-[11px] font-semibold text-[#3f4dbf] hover:underline"
              >
                {isEditingNote ? 'Done' : 'Edit'}
              </button>
            </div>
          </div>

          {isEditingNote ? (
            <textarea
              value={userNote}
              onChange={(e) => setUserNote(e.target.value)}
              className="w-full p-2.5 rounded-xl bg-white text-xs text-[#131c2a] border border-black/[0.08] focus:ring-1 focus:ring-[#3f4dbf]"
              rows={2}
            />
          ) : (
            <blockquote className="bg-white p-3 rounded-xl font-body text-xs text-[#131c2a] leading-relaxed border-l-2 border-[#3f4dbf]">
              “{userNote}”
            </blockquote>
          )}
        </div>
      </article>

      {/* Related Resources Collapsible Bottom Drawer */}
      <div className="w-full bg-[#f0f3ff] rounded-2xl p-4 shadow-xs border border-black/[0.04]">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3 min-w-0">
            <div className="w-10 h-10 rounded-xl bg-[#dce5dd] flex items-center justify-center text-[#151d19] flex-shrink-0">
              <span className="material-symbols-outlined text-[22px]">auto_stories</span>
            </div>
            <div className="min-w-0">
              <p className="font-headline text-xs sm:text-sm font-bold text-[#131c2a] truncate">
                Related to Question 7
              </p>
              <p className="font-body text-xs text-[#58605a] truncate">
                Graph traversal notes, BFS & DFS video (2 items)
              </p>
            </div>
          </div>
          <button
            onClick={() => setIsDrawerOpen(!isDrawerOpen)}
            className="flex-shrink-0 px-3 py-1.5 rounded-xl bg-white text-[#131c2a] font-label-md text-xs font-semibold shadow-xs hover:bg-gray-100 transition-colors flex items-center gap-1"
          >
            <span>{isDrawerOpen ? 'Hide' : 'View'}</span>
            <span className="material-symbols-outlined text-[16px]">
              {isDrawerOpen ? 'expand_less' : 'expand_more'}
            </span>
          </button>
        </div>

        {/* Collapsible Content */}
        {isDrawerOpen && (
          <div className="mt-3 pt-3 border-t border-black/[0.05] space-y-2 animate-fadeIn">
            <div
              onClick={() => onShowToast('Opening Graph Traversal Master Handout (PDF)...')}
              className="flex items-center justify-between p-2.5 bg-white rounded-xl hover:bg-gray-50 transition-colors cursor-pointer active-haptic"
            >
              <div className="flex items-center gap-2.5">
                <span className="material-symbols-outlined text-[#3f4dbf] text-[20px]">description</span>
                <div>
                  <p className="font-headline text-xs font-bold text-[#131c2a]">
                    Graph Traversal Master Handout
                  </p>
                  <p className="font-body text-[11px] text-[#58605a]">PDF · 4 pages · 1.2 MB</p>
                </div>
              </div>
              <span className="material-symbols-outlined text-[#58605a] text-[18px]">open_in_new</span>
            </div>

            <div
              onClick={() => onShowToast('Streaming: Visualizing BFS Queue Invariants by Prof. Harrison')}
              className="flex items-center justify-between p-2.5 bg-white rounded-xl hover:bg-gray-50 transition-colors cursor-pointer active-haptic"
            >
              <div className="flex items-center gap-2.5">
                <span className="material-symbols-outlined text-[#ba1a1a] text-[20px]">smart_display</span>
                <div>
                  <p className="font-headline text-xs font-bold text-[#131c2a]">
                    Visualizing BFS Queue Invariants
                  </p>
                  <p className="font-body text-[11px] text-[#58605a]">Video · 8 mins · Prof. Harrison</p>
                </div>
              </div>
              <span className="material-symbols-outlined text-[#58605a] text-[18px]">play_circle</span>
            </div>
          </div>
        )}
      </div>

      {/* Exam Prep Assistant Sticky Touch Strip */}
      <div className="w-full bg-gradient-to-r from-[#3f4dbf] to-[#5967d9] p-4 rounded-2xl shadow-lg text-white flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="w-11 h-11 rounded-xl bg-white/20 backdrop-blur-md flex items-center justify-center text-white flex-shrink-0">
            <span className="material-symbols-outlined text-[24px]">psychology</span>
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-headline text-sm sm:text-base font-bold text-white">
                Exam Prep Assistant
              </span>
              <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-white text-[#3f4dbf] uppercase">
                BETA
              </span>
            </div>
            <p className="font-body text-xs text-[#dfe0ff] leading-tight mt-0.5">
              Solve Question 7 & verify step-by-step queue states
            </p>
          </div>
        </div>

        <button
          onClick={onOpenTestModal}
          className="w-full sm:w-auto px-5 py-2.5 rounded-xl bg-white text-[#3f4dbf] font-label-lg text-xs sm:text-sm font-bold shadow-md hover:bg-gray-50 transition-all active:scale-95 flex items-center justify-center gap-2 flex-shrink-0"
        >
          <span className="material-symbols-outlined text-[20px]">task_alt</span>
          <span>Test My Solution</span>
        </button>
      </div>

      {/* Reading Footer Status */}
      <footer className="text-center py-2">
        <p className="font-label-sm text-xs text-[#58605a] flex items-center justify-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span>Reading position saved automatically</span>
          <span className="text-gray-400">•</span>
          <span className="font-semibold text-[#131c2a]">Page {currentPage} of {totalPages}</span>
        </p>
      </footer>
    </div>
  );
};
